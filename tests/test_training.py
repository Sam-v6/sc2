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
