import tempfile
from pathlib import Path
import unittest
from src.rl.policy import Policy


class CadenceTests(unittest.TestCase):
    def test_checkpoint_records_cadence_and_changed_training_resume_is_rejected(self):
        from src.rl.train import check_training_cadence
        policy = Policy(['state'], ['wait'])
        policy.macro_seconds = 1
        policy.reward_version = 'capacity-v1'
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / 'policy.npz'
            policy.save(checkpoint)
            loaded = Policy.load(checkpoint, policy.features, policy.actions)
        self.assertEqual(loaded.macro_seconds, 1)
        check_training_cadence(loaded, 1, None)
        with self.assertRaisesRegex(ValueError, 'cadence'):
            check_training_cadence(loaded, 5, None)

    def test_legacy_checkpoint_requires_explicit_known_cadence(self):
        from src.rl.train import check_training_cadence
        policy = Policy(['state'], ['wait'])
        with self.assertRaisesRegex(ValueError, 'legacy-macro-seconds'):
            check_training_cadence(policy, 1, None)
        with self.assertRaises(ValueError):
            check_training_cadence(policy, 5, 1)
        check_training_cadence(policy, 1, 1)
        self.assertEqual(policy.macro_seconds, 1)


class CollectionTests(unittest.TestCase):
    def test_merge_uses_experience_without_replacing_parent_with_stale_worker_weights(self):
        import numpy as np
        from src.rl.train import learn_candidate
        parent = Policy(['state'], ['wait', 'advance'])
        child = Policy(['state'], ['wait', 'advance'])
        for parameter in child.network:
            parameter[:] = 999
        child.remember([1], 1, 1, [1], [True, True], True)
        before = parent.parameters.copy()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'candidate.npz'
            child.save(path)
            result = learn_candidate(parent, path)
        self.assertEqual(parent.episodes, 1)
        self.assertGreater(parent.updates, 0)
        self.assertFalse(np.array_equal(parent.parameters, before))
        self.assertLess(abs(parent.parameters).max(), 100)
        self.assertEqual(result['learner_updates_after'], parent.updates)

    def test_parallel_worker_failures_preserve_canonical_checkpoint(self):
        import hashlib
        from types import SimpleNamespace
        from unittest.mock import patch
        from src.rl import train
        from src.rl.terran import FEATURES, ACTIONS
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = root / 'policy.npz'
            policy = Policy(FEATURES, ACTIONS)
            policy.macro_seconds = 1
            policy.reward_version = 'capacity-v1'
            policy.save(checkpoint)
            before = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
            game_map = root / 'test.SC2Map'
            game_map.write_bytes(b'test')
            with patch('sys.argv', ['train', '--episodes', '2', '--workers', '2', '--checkpoint', str(checkpoint), '--output', str(root / 'output')]), \
                 patch.object(train, 'validate_map', return_value=SimpleNamespace(path=game_map)), \
                 patch.object(train, 'supervise', return_value={'status': 'wall_timeout', 'result': None}), patch('builtins.print'):
                with self.assertRaises(SystemExit):
                    train.main()
            self.assertEqual(before, hashlib.sha256(checkpoint.read_bytes()).hexdigest())
            import json
            summaries = list((root / 'output').glob('*.summary.json'))
            self.assertEqual(len(summaries), 1)
            self.assertEqual(json.loads(summaries[0].read_text())['failures'], 2)
            histories = list((root / 'output').glob('*.behavior.npz'))
            self.assertEqual(len(histories), 1)
            self.assertEqual(hashlib.sha256(histories[0].read_bytes()).hexdigest(), before)

    def test_mixed_batch_resume_advances_schedule_past_all_attempts(self):
        import numpy as np
        import json
        from types import SimpleNamespace
        from unittest.mock import patch
        from src.rl import train
        from src.rl.terran import FEATURES, ACTIONS
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = root / 'policy.npz'
            policy = Policy(FEATURES, ACTIONS)
            policy.macro_seconds = 1
            policy.reward_version = 'capacity-v1'
            policy.save(checkpoint)
            game_map = root / 'test.SC2Map'
            game_map.write_bytes(b'test')
            def collect(function, args, timeout, **kwargs):
                job = args[0]
                if job['seed'] == 7:
                    return {'status': 'wall_timeout', 'result': None}
                candidate = Policy(FEATURES, ACTIONS)
                candidate.remember(np.ones(len(FEATURES)), 0, 1, np.ones(len(FEATURES)), np.ones(len(ACTIONS), dtype=bool), True)
                candidate.save(job['candidate'])
                return {'status': 'completed', 'result': 'Victory'}
            argv = ['train', '--episodes', '2', '--workers', '2', '--checkpoint', str(checkpoint), '--output', str(root / 'first')]
            with patch('sys.argv', argv), patch.object(train, 'validate_map', return_value=SimpleNamespace(path=game_map)), \
                 patch.object(train, 'supervise', side_effect=collect), patch('builtins.print'):
                with self.assertRaises(SystemExit): train.main()
            loaded = Policy.load(checkpoint, FEATURES, ACTIONS)
            self.assertEqual(loaded.episodes, 1)
            self.assertEqual(loaded.attempts, 2)
            argv[2] = '1'
            argv[-1] = str(root / 'resume')
            with patch('sys.argv', argv), patch.object(train, 'validate_map', return_value=SimpleNamespace(path=game_map)), \
                 patch.object(train, 'supervise', side_effect=collect), patch('builtins.print'):
                train.main()
            records = [json.loads(p.read_text()) for p in (root / 'resume').glob('*.json') if not p.name.endswith('summary.json')]
            self.assertEqual(records[0]['seed'], 9)
            self.assertEqual(records[0]['race'], 'Zerg')


class BehaviorHistoryTests(unittest.TestCase):
    def test_batches_keep_the_exact_models_used_by_workers(self):
        import json
        import numpy as np
        from types import SimpleNamespace
        from unittest.mock import patch
        from src.rl import train
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = root / 'policy.npz'
            policy = Policy(train.FEATURES, train.ACTIONS)
            policy.macro_seconds = 1
            policy.reward_version = 'capacity-v1'
            policy.save(checkpoint)
            initial = train.digest(checkpoint)
            game_map = root / 'test.SC2Map'
            game_map.write_bytes(b'test')
            jobs = []
            def collect(function, args, timeout, **kwargs):
                job = args[0]
                jobs.append(job)
                child = Policy.load(job['behavior_checkpoint'], train.FEATURES, train.ACTIONS)
                self.assertEqual(train.digest(job['behavior_checkpoint']), job['behavior_checkpoint_sha256'])
                state = np.ones(len(train.FEATURES))
                child.remember(state, 0, 1, state, np.ones(len(train.ACTIONS), dtype=bool), True)
                child.save(job['candidate'])
                return {'status': 'completed', 'result': 'Victory'}
            argv = ['train', '--episodes', '4', '--workers', '2', '--checkpoint', str(checkpoint),
                    '--output', str(root / 'output')]
            with patch('sys.argv', argv), patch.object(train, 'validate_map', return_value=SimpleNamespace(path=game_map)), \
                 patch.object(train, 'supervise', side_effect=collect), patch('builtins.print'):
                train.main()
            jobs.sort(key=lambda job: job['seed'])
            self.assertEqual(jobs[0]['behavior_checkpoint'], jobs[1]['behavior_checkpoint'])
            self.assertEqual(jobs[2]['behavior_checkpoint'], jobs[3]['behavior_checkpoint'])
            self.assertNotEqual(jobs[0]['behavior_checkpoint'], jobs[2]['behavior_checkpoint'])
            self.assertEqual(train.digest(jobs[0]['behavior_checkpoint']), initial)
            self.assertNotEqual(train.digest(jobs[2]['behavior_checkpoint']), initial)
            loaded = Policy.load(checkpoint, train.FEATURES, train.ACTIONS)
            self.assertEqual((loaded.episodes, loaded.attempts), (4, 4))
            for path in (root / 'output').glob('*.json'):
                receipt = json.loads(path.read_text())
                if 'result' in receipt:
                    self.assertEqual(receipt['checkpoint'], str(checkpoint))
                    self.assertEqual(train.digest(receipt['behavior_checkpoint']), receipt['behavior_checkpoint_sha256'])
            self.assertFalse(list((root / 'output').glob('*.candidate.npz')))

    def test_frozen_evaluation_keeps_its_supplied_file_without_training_history(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from src.rl import train
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = root / 'frozen.npz'
            policy = Policy(train.FEATURES, train.ACTIONS)
            policy.macro_seconds = 1
            policy.save(checkpoint)
            before = train.digest(checkpoint)
            game_map = root / 'test.SC2Map'
            game_map.write_bytes(b'test')
            def collect(function, args, timeout, **kwargs):
                job = args[0]
                self.assertEqual(job['behavior_checkpoint'], str(checkpoint))
                return {'status': 'completed', 'result': 'Victory'}
            argv = ['train', '--mode', 'evaluate', '--episodes', '2', '--workers', '2',
                    '--checkpoint', str(checkpoint), '--output', str(root / 'output')]
            with patch('sys.argv', argv), patch.object(train, 'validate_map', return_value=SimpleNamespace(path=game_map)), \
                 patch.object(train, 'supervise', side_effect=collect), patch('builtins.print'):
                train.main()
            self.assertEqual(train.digest(checkpoint), before)
            self.assertFalse(list((root / 'output').glob('*.behavior.npz')))


class RewardSchemaTests(unittest.TestCase):
    def test_reward_objective_is_saved_and_incompatible_training_is_rejected(self):
        from src.rl.train import check_training_reward
        from src.rl.terran import REWARD_VERSION
        policy = Policy(['state'], ['wait'])
        with self.assertRaisesRegex(ValueError, 'reward'):
            check_training_reward(policy)
        policy.reward_version = 'old-objective'
        with self.assertRaisesRegex(ValueError, 'reward'):
            check_training_reward(policy)
        policy.reward_version = REWARD_VERSION
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / 'policy.npz'
            policy.save(checkpoint)
            loaded = Policy.load(checkpoint, policy.features, policy.actions)
        self.assertEqual(loaded.reward_version, REWARD_VERSION)
        check_training_reward(loaded)


class PPOCollectionTests(unittest.TestCase):
    def test_failed_helper_preserves_parent_and_removes_scratch(self):
        from unittest.mock import patch
        import numpy as np
        from src.rl.actor_critic import ActorCritic
        from src.rl.train import learn_ppo_batch
        policy = ActorCritic(['state'], ['wait'])
        policy.macro_seconds = 1
        policy.reward_version = 'capacity-v1'
        before = policy.parameters.copy()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = ActorCritic(policy.features, policy.actions)
            candidate.macro_seconds = 1
            candidate.reward_version = 'capacity-v1'
            candidate.collect_episode([(np.array([1.]), 0, 1, np.array([1.]), np.array([True]), True)], [np.array([True])])
            candidate.save(root / 'episode.npz')
            with patch('src.rl.train.supervise', return_value={'status': 'error', 'error': 'backend failed'}):
                with self.assertRaisesRegex(RuntimeError, 'backend failed'):
                    learn_ppo_batch(policy, [root / 'episode.npz'], '/missing/python', root / 'update.npz', 1)
            self.assertFalse((root / 'update.npz').exists())
        np.testing.assert_array_equal(before, policy.parameters)
        self.assertEqual(policy.episodes, 0)

    def test_cli_preserves_virtualenv_interpreter_symlink(self):
        import copy
        import sys
        import numpy as np
        from types import SimpleNamespace
        from unittest.mock import patch
        from src.rl import train
        from src.rl.actor_critic import ActorCritic
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            interpreter = root / 'venv-python'
            interpreter.symlink_to(sys.executable)
            game_map = root / 'test.SC2Map'
            game_map.write_bytes(b'test')
            def collect(function, args, timeout, **kwargs):
                job = args[0]
                candidate = ActorCritic.load(job['checkpoint'], train.FEATURES, train.ACTIONS)
                mask = np.array([True] + [False] * (len(train.ACTIONS) - 1))
                state = np.ones(len(train.FEATURES))
                candidate.collect_episode([(state, 0, 1, state, mask, True)], [mask])
                candidate.save(job['candidate'])
                return {'status': 'completed', 'result': 'Victory'}
            def learn(policy, candidates, backend, scratch, attempts):
                self.assertEqual(backend, interpreter.absolute())
                self.assertTrue(backend.is_symlink())
                updated = copy.deepcopy(policy)
                updated.updates += 1
                updated.episodes += 1
                updated.attempts = attempts
                return updated, {'status': 'completed'}
            argv = ['train', '--algorithm', 'ppo', '--torch-python', str(interpreter), '--episodes', '1',
                    '--checkpoint', str(root / 'policy.npz'), '--output', str(root / 'output')]
            with patch('sys.argv', argv), patch.object(train, 'validate_map', return_value=SimpleNamespace(path=game_map)), \
                 patch.object(train, 'supervise', side_effect=collect), patch.object(train, 'learn_ppo_batch', side_effect=learn), patch('builtins.print'):
                train.main()

    def test_helper_failure_reports_its_original_stderr(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from src.rl.train import run_torch_update
        with patch('src.rl.train.subprocess.run', return_value=SimpleNamespace(returncode=1, stderr='Torch missing', stdout='')):
            with self.assertRaisesRegex(RuntimeError, 'Torch missing'):
                run_torch_update('/python', '/checkpoint')
