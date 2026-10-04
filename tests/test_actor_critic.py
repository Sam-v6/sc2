import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from src.rl.actor_critic import ActorCritic


class ActorCriticTests(unittest.TestCase):
    def test_masked_probabilities_and_frozen_choice(self):
        policy = ActorCritic(['bias', 'context'], ['wait', 'produce'])
        np.testing.assert_array_equal(policy.probabilities([1, 0], [True, False]), [1, 0])
        before = json.dumps(policy.rng.bit_generator.state)
        self.assertEqual(policy.act([1, 0], [True, False], False), 0)
        self.assertEqual(before, json.dumps(policy.rng.bit_generator.state))

    def test_terminal_gae_stops_and_cutoff_bootstraps(self):
        policy = ActorCritic(['state'], ['wait'])
        policy.gamma = .5
        policy.network[4][:] = 0
        policy.network[5][...] = .5
        transitions = [(np.array([0]), 0, 1, np.array([1]), np.array([True]), False),
                       (np.array([1]), 0, 2, np.array([2]), np.array([True]), True)]
        policy.collect_episode(transitions, [np.array([True])] * 2)
        self.assertAlmostEqual(policy.rollout[0][4], .75 + .5 * .95 * 1.5)
        self.assertAlmostEqual(policy.rollout[1][5], 2)
        policy.rollout.clear()
        policy.collect_episode(transitions[:1], [np.array([True])])
        self.assertAlmostEqual(policy.rollout[0][5], 1.25)

    def test_checkpoint_preserves_optimizer_rng_rollout_and_rejects_scale_change(self):
        policy = ActorCritic(['state'], ['wait'])
        policy.macro_seconds = 1
        policy.reward_version = 'capacity-v1'
        policy.collect_episode([(np.array([0]), 0, 1, np.array([1]), np.array([True]), True)], [np.array([True])])
        policy.m[4][:] = .2
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'policy.npz'
            policy.save(path)
            loaded = ActorCritic.load(path, policy.features, policy.actions)
            np.testing.assert_array_equal(policy.parameters, loaded.parameters)
            np.testing.assert_array_equal(policy.m[4], loaded.m[4])
            self.assertEqual(len(loaded.rollout), 1)
            self.assertEqual(policy.rng.random(), loaded.rng.random())
            with np.load(path, allow_pickle=False) as saved:
                arrays = {name: saved[name].copy() for name in saved.files}
            metadata = json.loads(str(arrays['metadata']))
            metadata['reward_scale'] = 1
            arrays['metadata'] = np.array(json.dumps(metadata))
            np.savez(path, **arrays)
            with self.assertRaisesRegex(ValueError, 'scale'):
                ActorCritic.load(path, policy.features, policy.actions)


class TorchIntegrationTests(unittest.TestCase):
    @unittest.skipUnless(Path('/home/sam/repos/sc2-repos/SC2RL/.venv/bin/python').is_file(), 'Existing optional Torch runtime unavailable')
    def test_cpu_update_learns_context_and_resumes_adam(self):
        import subprocess
        policy = ActorCritic(['bias', 'context'], ['wait', 'produce'], seed=4)
        def collect():
            for _ in range(64):
                for context in (-1, 1):
                    for action in (0, 1):
                        state = np.array([1., context])
                        outcome = 1 if action == int(context > 0) else -1
                        policy.collect_episode([(state, action, outcome, state, np.array([True, True]), True)], [np.array([True, True])])
        correct_before = [policy.probabilities([1, context], [True, True])[int(context > 0)] for context in (-1, 1)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'policy.npz'
            for _ in range(2):
                collect()
                policy.save(path)
                result = subprocess.run(['/home/sam/repos/sc2-repos/SC2RL/.venv/bin/python', '-B', '-m', 'src.rl.ppo_update', str(path)],
                                        capture_output=True, text=True, timeout=30, check=True)
                self.assertEqual(json.loads(result.stdout)['learner_samples'], 256)
                previous = policy.updates
                policy = ActorCritic.load(path, policy.features, policy.actions)
                self.assertGreater(policy.updates, previous)
                self.assertFalse(policy.rollout)
        for index, context in enumerate((-1, 1)):
            self.assertGreater(policy.probabilities([1, context], [True, True])[int(context > 0)], correct_before[index])
        self.assertTrue(any(np.any(moment) for moment in policy.m))
