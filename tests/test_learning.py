import tempfile
from pathlib import Path
import unittest
import numpy as np
from src.rl.policy import Policy


class LearningTests(unittest.TestCase):
    def make_policy(self):
        return Policy(['bias', 'context'], ['wait', 'produce'], seed=4)

    def test_mask_excludes_unavailable_actions(self):
        policy = self.make_policy()
        for _ in range(100):
            self.assertEqual(policy.act([1, 0], [True, False], explore=True), 0)

    def test_reward_task_learns_context(self):
        policy = self.make_policy()
        for _ in range(300):
            for context in (-1, 1):
                for action in (0, 1):
                    reward = 1 if action == int(context > 0) else -1
                    policy.remember([1, context], action, reward, [1, context], [True, True], terminal=True)
            policy.learn(batch_size=32)
        self.assertEqual(policy.act([1, -1], [True, True], explore=False), 0)
        self.assertEqual(policy.act([1, 1], [True, True], explore=False), 1)
        self.assertGreater(policy.updates, 0)

    def test_checkpoint_resumes_rng_parameters_and_experience(self):
        policy = self.make_policy()
        policy.remember([1, 0], 1, 1, [1, 0], [True, True], terminal=True)
        policy.learn(batch_size=1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'policy.npz'
            policy.save(path)
            loaded = Policy.load(path, ['bias', 'context'], ['wait', 'produce'])
        np.testing.assert_array_equal(policy.parameters, loaded.parameters)
        self.assertEqual(policy.updates, loaded.updates)
        self.assertEqual(len(policy.experience), len(loaded.experience))
        self.assertEqual([policy.act([1, 0], [True, True], True) for _ in range(30)],
                         [loaded.act([1, 0], [True, True], True) for _ in range(30)])

    def test_evaluation_changes_no_parameters_or_rng(self):
        policy = self.make_policy()
        before = policy.parameters.copy()
        rng = str(policy.rng.bit_generator.state)
        for _ in range(10):
            policy.act([1, 0], [True, True], explore=False)
        np.testing.assert_array_equal(before, policy.parameters)
        self.assertEqual(rng, str(policy.rng.bit_generator.state))

    def test_terminal_omits_bootstrap_and_truncation_keeps_it(self):
        policy = self.make_policy()
        nxt = np.array([[1., 0.]])
        masks = np.array([[True, True]])
        rewards = np.array([2.])
        self.assertAlmostEqual(float(policy.targets(rewards, nxt, masks, np.array([True]))[0]), 2)
        expected = 2 + policy.gamma * np.max(policy.values(nxt, target=True))
        self.assertAlmostEqual(float(policy.targets(rewards, nxt, masks, np.array([False]))[0]), expected)

    def test_wrong_checkpoint_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'policy.npz'
            self.make_policy().save(path)
            with self.assertRaises(ValueError):
                Policy.load(path, ['wrong'], ['wait', 'produce'])
