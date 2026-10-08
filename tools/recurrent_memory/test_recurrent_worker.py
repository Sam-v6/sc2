import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from src.rl.actor_critic import ActorCritic
from src.rl.terran import FEATURES,ACTIONS
from src.rl import train as ordinary
from recurrent_policy import RecurrentPolicy
from recurrent_worker import episode,digest


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.root=Path(self.directory.name)
        parent=ActorCritic(FEATURES,ACTIONS);parent.macro_seconds=1;parent.reward_version='combat-kills-v1'
        self.model=self.root/'model.npz';RecurrentPolicy(parent,331,False).save(self.model)
        self.job={'mode':'train','behavior_checkpoint':str(self.model),'behavior_checkpoint_sha256':digest(self.model),
                  'seed':1,'policy_seed':2,'macro_seconds':1,'game_limit':1200,
                  'gamma':parent.gamma,'reward_scale':parent.reward_scale,'reward_version':parent.reward_version,'memory_reset':False,
                  'actions':str(self.root/'actions.jsonl'),'journal':str(self.root/'journal.jsonl'),
                  'trajectory':str(self.root/'trajectory.npz')}

    def test_collection_reconstructs_sequence_without_optimizer_updates(self):
        def fake(job):
            policy=ordinary.load_policy(job['behavior_checkpoint'],FEATURES,ACTIONS)
            bot=ordinary.TerranLearner(policy,False,job['actions'],macro_seconds=1)
            states=np.zeros((2,len(FEATURES)));mask=np.ones(len(ACTIONS),dtype=bool)
            actions=[policy.act(state,mask,True) for state in states]
            bot.decisions=[{'legal':ACTIONS} for _ in actions]
            bot.transitions=[(state,action,float(i),state,mask,i==1) for i,(state,action) in enumerate(zip(states,actions))]
            Path(job['journal']).write_text('fake journal')
            return {'status':'completed','result':'Victory','updates_before':0,'updates_after':0}
        original_load,original_bot=ordinary.load_policy,ordinary.TerranLearner
        with patch('recurrent_worker.ordinary.episode',side_effect=fake):
            result=episode(self.job)
        self.assertEqual(result['trajectory_rows'],2)
        self.assertEqual(result['updates_after'],0)
        with np.load(self.job['trajectory'],allow_pickle=False) as data:
            self.assertEqual(len(data['chosen']),2)
            self.assertTrue(np.isfinite(data['logp']).all())
        self.assertIs(ordinary.load_policy,original_load);self.assertIs(ordinary.TerranLearner,original_bot)
        self.assertEqual(digest(self.model),self.job['behavior_checkpoint_sha256'])

    def test_failure_restores_ordinary_entrypoints_and_keeps_model(self):
        original_load,original_bot=ordinary.load_policy,ordinary.TerranLearner
        with patch('recurrent_worker.ordinary.episode',side_effect=RuntimeError('failure')):
            with self.assertRaises(RuntimeError): episode(self.job)
        self.assertIs(ordinary.load_policy,original_load);self.assertIs(ordinary.TerranLearner,original_bot)
        self.assertFalse(Path(self.job['trajectory']).exists())
        self.assertEqual(digest(self.model),self.job['behavior_checkpoint_sha256'])


if __name__=='__main__':unittest.main()
