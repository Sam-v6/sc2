import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from src.rl.actor_critic import ActorCritic
from recurrent_policy import RecurrentPolicy
from fit_batch import digest,fit


class BatchTests(unittest.TestCase):
    def fixture(self,root):
        parent=ActorCritic(['a','b','c'],['wait','build'],seed=9)
        parent.gamma=.99;parent.macro_seconds=1;parent.reward_version='combat-kills-v1'
        policy=RecurrentPolicy(parent,331,False);model=root/'behavior.npz';policy.save(model)
        jobs=[];hashes={str(model):digest(model)}
        for seed in range(4):
            policy.reset_episode();policy.rng=np.random.default_rng(seed)
            states=np.random.default_rng(seed).normal(size=(12,3));masks=np.ones((12,2),dtype=bool)
            chosen=[policy.act(s,m,True) for s,m in zip(states,masks)]
            rewards=np.zeros(12);rewards[-1]=1
            data=policy.episode(states,chosen,masks,rewards)
            job={'seed':seed,'mode':'train','purpose':'controlled-strength-study','role':'recurrent',
                 'behavior_checkpoint':str(model),'behavior_checkpoint_sha256':digest(model),
                 'receipt':str(root/f'{seed}.json'),'trajectory':str(root/f'{seed}.npz')}
            meta={**job,'result':'Victory','features':parent.features,'actions_schema':parent.actions,
                  'updates':0,'gamma':policy.gamma,'memory_reset':False,
                  'reward_version':policy.reward_version,'reward_scale':policy.reward_scale}
            np.savez(job['trajectory'],**data,metadata=np.array(json.dumps(meta)))
            Path(job['receipt']).write_text(json.dumps({**job,'result':'Victory','episode_audit':{'passed':True},
                                                       'trajectory_sha256':digest(job['trajectory'])}))
            jobs.append(job)
            hashes.update({path:digest(path) for path in [job['trajectory'],job['receipt']]})
        task={'purpose':'controlled-strength-study','role':'recurrent','jobs':jobs,'hashes':hashes,
              'behavior_checkpoint':str(model),'behavior_sha256':digest(model),
              'target':str(root/'fitted.npz'),'fit_receipt':str(root/'fit.json'),'task_path':str(root/'task.json')}
        Path(task['task_path']).write_text(json.dumps(task));return task,policy

    def test_four_real_episode_updates_keep_parent_frozen(self):
        with tempfile.TemporaryDirectory() as directory:
            task,before=self.fixture(Path(directory));result=fit(task)
            after=RecurrentPolicy.load(task['target'],before.features,before.actions)
            self.assertEqual(result['optimizer_clock'],16);self.assertEqual(after.episodes,4)
            self.assertEqual(after.attempts,4);self.assertTrue(after.core.actor.any())
            for a,b in zip(before.core.network,after.core.network):np.testing.assert_array_equal(a,b)
            self.assertEqual(json.loads(Path(task['fit_receipt']).read_text())['sha256'],digest(task['target']))

    def test_duplicate_or_evaluation_episode_is_rejected_before_fit(self):
        for change in ['duplicate','evaluate']:
            with tempfile.TemporaryDirectory() as directory:
                task,_=self.fixture(Path(directory))
                if change=='duplicate':task['jobs'][1]=task['jobs'][0]
                else:task['jobs'][0]['mode']='evaluate'
                with self.assertRaises(AssertionError):fit(task)
                self.assertFalse(Path(task['target']).exists())


if __name__=='__main__':unittest.main()
