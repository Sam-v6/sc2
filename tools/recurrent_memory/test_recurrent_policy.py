import tempfile
import json
from pathlib import Path
import unittest
import numpy as np
from src.rl.actor_critic import ActorCritic
from recurrent_policy import RecurrentPolicy, update


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.parent=ActorCritic(['a','b','c'],['wait','build'],seed=9)
        self.parent.gamma=.99;self.parent.macro_seconds=1;self.parent.reward_version='combat-kills-v1'
        self.policy=RecurrentPolicy(self.parent,seed=331,memory_reset=False)
        self.states=np.random.default_rng(4).normal(size=(12,3))
        self.masks=np.ones((12,2),dtype=bool)

    def episode(self):
        self.policy.reset_episode()
        actions=[self.policy.act(state,mask,True) for state,mask in zip(self.states,self.masks)]
        rewards=np.zeros(12);rewards[-1]=1
        return self.policy.episode(self.states,actions,self.masks,rewards)

    def test_initial_greedy_choices_preserve_parent_and_new_optimizer_is_fresh(self):
        for state,mask in zip(self.states,self.masks):
            self.assertEqual(self.policy.act(state,mask,False),self.parent.act(state,mask,False))
        self.assertEqual(self.policy.updates,0)
        self.assertTrue(all(not array.any() for array in self.policy.m+self.policy.v))
        for actual,expected in zip(self.policy.core.network,self.parent.network):
            np.testing.assert_array_equal(actual,expected)

    def test_sequence_reconstructs_behavior_and_rejects_different_action(self):
        data=self.episode()
        self.assertEqual(len(data['states']),12)
        wrong=data['chosen'].copy();wrong[3]=1-wrong[3]
        with self.assertRaises(AssertionError):
            self.policy.episode(self.states,wrong,self.masks,data['rewards'])
        self.assertAlmostEqual(data['returns'][0],self.policy.gamma**11)

    def test_active_checkpoint_resume_preserves_memory_and_random_choices(self):
        self.policy.core.actor[:]=.1
        for state,mask in zip(self.states[:5],self.masks[:5]):
            self.policy.act(state,mask,True)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'policy.npz';self.policy.save(path)
            resumed=RecurrentPolicy.load(path,self.parent.features,self.parent.actions)
            for state,mask in zip(self.states[5:],self.masks[5:]):
                self.assertEqual(self.policy.act(state,mask,True),resumed.act(state,mask,True))
                np.testing.assert_array_equal(self.policy.memory[0],resumed.memory[0])
            self.assertEqual(self.policy.trace,resumed.trace)

    def test_actual_ppo_update_changes_only_residual_and_resumes_adam(self):
        data=self.episode();before=[a.copy() for a in self.policy.core.network]
        result=update(self.policy,[data])
        self.assertEqual(result['updates'],4)
        self.assertEqual(self.policy.updates,4)
        self.assertTrue(self.policy.core.actor.any())
        for actual,expected in zip(self.policy.core.network,before):
            np.testing.assert_array_equal(actual,expected)
        fresh=self.episode()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'policy.npz';self.policy.save(path)
            resumed=RecurrentPolicy.load(path,self.parent.features,self.parent.actions)
            update(self.policy,[fresh]);update(resumed,[fresh])
            for a,b in zip(self.policy.parameters(),resumed.parameters()):
                np.testing.assert_array_equal(a,b)
            self.assertEqual(resumed.updates,8)

    def test_invalid_checkpoint_context_and_optimizer_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            good=Path(directory)/'good.npz';self.policy.save(good)
            with np.load(good,allow_pickle=False) as archive:
                original={key:archive[key] for key in archive.files}
            for i,(field,value) in enumerate([('gamma',1.5),('updates',-1),('memory_reset',1)]):
                data=dict(original);meta=json.loads(str(data['metadata']));meta[field]=value
                data['metadata']=np.array(json.dumps(meta));bad=Path(directory)/f'bad{i}.npz'
                np.savez(bad,**data)
                with self.assertRaises(AssertionError):
                    RecurrentPolicy.load(bad,self.parent.features,self.parent.actions)
            for i,(field,value) in enumerate([('v0',-np.ones_like(original['v0'])),('hidden',np.zeros(31)),('parameters4',np.full_like(original['parameters4'],np.nan))]):
                data=dict(original);data[field]=value;bad=Path(directory)/f'array{i}.npz';np.savez(bad,**data)
                with self.assertRaises(AssertionError):
                    RecurrentPolicy.load(bad,self.parent.features,self.parent.actions)

    def test_changed_returns_advantages_and_terminal_are_rejected_before_update(self):
        original=self.episode()
        for field in ['returns','advantages','terminal']:
            data={key:value.copy() for key,value in original.items()}
            if field=='terminal': data[field][0]=True
            else: data[field][0]+=1
            with self.assertRaises(AssertionError): update(self.policy,[data])
            self.assertEqual(self.policy.updates,0)

    def test_stale_behavior_is_rejected_before_any_further_update(self):
        data=self.episode()
        update(self.policy,[data])
        before=self.policy.updates
        with self.assertRaises(AssertionError):
            update(self.policy,[data])
        self.assertEqual(self.policy.updates,before)

    def test_memory_reset_control_and_numpy_torch_sequence_agree(self):
        from recurrent_policy import TorchCore
        import torch
        self.policy.core.actor[:]=.1;self.policy.core.value[:]=.2
        selected=np.arange(12)%2
        for reset in [False,True]:
            self.policy.memory_reset=reset
            logits,values=self.policy.sequence(self.states,selected)
            module=TorchCore(self.policy)
            actual,critic=module(torch.tensor(self.states),torch.tensor(selected))
            np.testing.assert_allclose(actual.detach().numpy(),logits,atol=1e-13,rtol=1e-13)
            np.testing.assert_allclose(critic.detach().numpy(),values,atol=1e-13,rtol=1e-13)


if __name__=='__main__':
    unittest.main()
