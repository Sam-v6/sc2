"""Collect recurrent episodes through unchanged SC2 rewards and command execution."""
import hashlib
import json
from pathlib import Path
import numpy as np
from recurrent_policy import RecurrentPolicy
from src.rl import train as ordinary
from src.rl.terran import TerranLearner,FEATURES,ACTIONS


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class JournalLearner(TerranLearner):
    def __init__(self,*args,journal,**kwargs):
        super().__init__(*args,**kwargs)
        self.journal=Path(journal)

    def event(self,row):
        with self.journal.open('a') as file:
            file.write(json.dumps(row)+'\n')

    def transition(self,*args,**kwargs):
        before=len(self.transitions)
        super().transition(*args,**kwargs)
        if len(self.transitions)>before:
            row=self.decisions[-1]
            self.event({'event':'transition','index':len(self.decisions)-1,
                        'reward':row['reward'],'components':row['reward_components']})

    async def custom_on_step(self,iteration):
        before=len(self.decisions)
        await super().custom_on_step(iteration)
        if len(self.decisions)>before:
            self.event({'event':'decision','index':len(self.decisions)-1,'decision':self.decisions[-1]})


def entrypoint_probe():
    return {'file':__file__,'episode_module':episode.__module__,'games_launched':0}


def episode(job):
    assert job['mode'] in ['train','evaluate','sample']
    assert job['macro_seconds']==1 and job['game_limit']==1200
    assert digest(job['behavior_checkpoint'])==job['behavior_checkpoint_sha256']
    for name in ['journal','trajectory']:
        assert not Path(job[name]).exists()
        Path(job[name]).parent.mkdir(parents=True,exist_ok=True)
    policy=RecurrentPolicy.load(job['behavior_checkpoint'],FEATURES,ACTIONS)
    assert policy.gamma==job['gamma'] and policy.reward_scale==job['reward_scale']
    assert policy.reward_version==job['reward_version'] and policy.macro_seconds==job['macro_seconds']
    assert policy.memory_reset==job['memory_reset']
    policy.reset_episode();policy.rng=np.random.default_rng(job['policy_seed'])
    before=[array.copy() for array in policy.core.network+policy.parameters()+policy.m+policy.v]
    bots=[]
    def load(path,features,actions):
        assert str(path)==job['behavior_checkpoint'] and features==FEATURES and actions==ACTIONS
        return policy
    def bot(*args,**kwargs):
        instance=JournalLearner(*args,journal=job['journal'],**kwargs)
        bots.append(instance);return instance
    original_load,original_bot=ordinary.load_policy,ordinary.TerranLearner
    ordinary.load_policy,ordinary.TerranLearner=load,bot
    try:
        # Sampling collects identical ordinary rewards without calling its
        # feedforward-only optimizer/checkpoint path. PPO runs in the parent.
        result=ordinary.episode({**job,'mode':'sample' if job['mode']=='train' else job['mode']})
    finally:
        ordinary.load_policy,ordinary.TerranLearner=original_load,original_bot
    assert len(bots)==1 and bots[0].transitions[-1][-1]
    for actual,expected in zip(policy.core.network+policy.parameters()+policy.m+policy.v,before):
        np.testing.assert_array_equal(actual,expected)
    assert result['updates_before']==result['updates_after']==policy.updates
    assert digest(job['behavior_checkpoint'])==job['behavior_checkpoint_sha256']
    if job['mode']=='train':
        transitions=bots[0].transitions
        assert not any(row[-1] for row in transitions[:-1])
        masks=np.array([[name in row['legal'] for name in ACTIONS] for row in bots[0].decisions])
        data=policy.episode(np.array([row[0] for row in transitions]),[row[1] for row in transitions],masks,[row[2] for row in transitions])
        metadata={**job,'algorithm':policy.algorithm,'features':FEATURES,'actions_schema':ACTIONS,
                  'memory_reset':policy.memory_reset,'gamma':policy.gamma,'reward_scale':policy.reward_scale,
                  'reward_version':policy.reward_version,'updates':policy.updates,'result':result['result']}
        with Path(job['trajectory']).open('xb') as file:
            np.savez_compressed(file,metadata=np.array(json.dumps(metadata)),**data)
        result.update(trajectory_sha256=digest(job['trajectory']),trajectory_rows=len(data['chosen']))
    result['journal_bytes']=Path(job['journal']).stat().st_size
    return result
