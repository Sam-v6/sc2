from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import numpy as np
from sc2.data import Result
from src.rl import train
from src.rl.actor_critic import ActorCritic


class FrozenSampleTests(unittest.TestCase):
    def test_episode_samples_seeded_learned_distribution_without_training(self):
        policy=ActorCritic(train.FEATURES,train.ACTIONS)
        policy.epsilon=1  # An explicit sample-mode request must use the learned categorical distribution.
        before=policy.parameters.copy();observations=np.zeros(len(train.FEATURES));observations[0]=1
        mask=np.zeros(len(train.ACTIONS),dtype=bool);mask[:2]=True
        probabilities=policy.probabilities(observations,mask)
        expected=np.random.default_rng(456).choice(len(train.ACTIONS),size=64,p=probabilities).tolist()
        created=[]
        class FakeBot:
            def __init__(self,p,training,action_log,macro_seconds,random_policy,game_seconds=1200):
                self.policy=p;self.training=training;self.random_policy=random_policy
                self.callback_error=None;self.started=True;self.time=10
                self.decisions=[];self.transitions=[];self.workers=NS(amount=12)
                self.townhalls=NS(amount=1);self.supply_army=0;created.append(self)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);replay=root/'game.SC2Replay';candidate=root/'candidate.npz'
            job={'seed':123,'policy_seed':456,'mode':'sample','behavior_checkpoint':'unused',
                 'actions':'unused','macro_seconds':1,'game_limit':120,'map':'unused',
                 'race':'Terran','difficulty':'Hard','build':'Rush','replay':str(replay),
                 'candidate':str(candidate)}
            def game(*args,**kwargs):
                bot=created[0];self.assertFalse(bot.training);self.assertTrue(bot.random_policy)
                bot.decisions=[policy.act(observations,mask,bot.training or bot.random_policy) for _ in range(64)]
                replay.write_bytes(b'fixture');return Result.Tie
            with patch.object(train,'load_policy',return_value=policy),patch.object(train,'TerranLearner',FakeBot), \
                 patch.object(train,'Bot',side_effect=lambda race,bot:NS(ai=bot)),patch.object(train,'validate_map',return_value='fixture'),patch.object(train,'run_game',side_effect=game), \
                 patch.object(train,'get_replay_version',return_value=['Base75689','fixture']):
                result=train.episode(job)
            self.assertEqual(created[0].decisions,expected)
            self.assertEqual(result['result'],'Tie');self.assertFalse(candidate.exists())
            np.testing.assert_array_equal(policy.parameters,before)
            self.assertFalse(policy.rollout)

    def test_main_frozen_sample_preserves_file_and_uses_reproducible_seeds(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);checkpoint=root/'policy.npz';game_map=root/'map.SC2Map'
            game_map.write_bytes(b'fixture')
            policy=ActorCritic(train.FEATURES,train.ACTIONS);policy.macro_seconds=1
            policy.save(checkpoint);before=train.digest(checkpoint);jobs=[]
            def collect(function,args,timeout,**kwargs):
                job=args[0];jobs.append(job)
                self.assertEqual(job['mode'],'sample')
                self.assertEqual(job['behavior_checkpoint'],str(checkpoint))
                self.assertEqual(job['policy_seed'],job['seed'])
                return {'status':'completed','result':'Victory'}
            argv=['train','--mode','sample','--episodes','2','--workers','2','--checkpoint',str(checkpoint),'--output',str(root/'output')]
            with patch('sys.argv',argv),patch.object(train,'validate_map',return_value=NS(path=game_map)), \
                 patch.object(train,'supervise',side_effect=collect),patch('builtins.print'):
                train.main()
            self.assertEqual(len(jobs),2);self.assertEqual(train.digest(checkpoint),before)
            self.assertFalse(list((root/'output').glob('*.behavior.npz')))

    def test_sample_mode_rejects_non_categorical_policy(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);checkpoint=root/'policy.npz';checkpoint.write_bytes(b'fixture')
            argv=['train','--mode','sample','--checkpoint',str(checkpoint),'--output',str(root/'output')]
            with patch('sys.argv',argv),patch.object(train,'validate_map'), \
                 patch.object(train,'load_policy',return_value=NS(algorithm='dqn')):
                with self.assertRaisesRegex(ValueError,'PPO'):
                    train.main()

    def test_sample_rejects_checkpoint_replacement_during_run(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);checkpoint=root/'policy.npz';game_map=root/'map.SC2Map'
            game_map.write_bytes(b'fixture')
            policy=ActorCritic(train.FEATURES,train.ACTIONS);policy.save(checkpoint)
            def collect(*args,**kwargs):
                checkpoint.write_bytes(b'concurrent replacement')
                return {'status':'completed','result':'Victory'}
            argv=['train','--mode','sample','--episodes','1','--workers','1',
                  '--checkpoint',str(checkpoint),'--output',str(root/'output')]
            with patch('sys.argv',argv),patch.object(train,'validate_map',return_value=NS(path=game_map)), \
                 patch.object(train,'supervise',side_effect=collect),patch('builtins.print'):
                with self.assertRaisesRegex(RuntimeError,'Frozen evaluation changed the checkpoint'):
                    train.main()
