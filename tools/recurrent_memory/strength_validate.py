"""Verify frozen policy choices and ordinary game evidence before learning/scoring."""
import json
from pathlib import Path
import numpy as np
from recurrent_policy import RecurrentPolicy
from recurrent_worker import digest
from src.rl.terran import FEATURES,ACTIONS,encode,capacity_potential
from sc2.main import get_replay_version


def validate(job,receipt):
    assert receipt['status'] in ['completed','truncated'] and receipt['result'] in ['Victory','Defeat','Tie']
    assert (receipt['status']=='truncated')==(receipt['result']=='Tie')
    assert digest(job['behavior_checkpoint'])==job['behavior_checkpoint_sha256']
    policy=RecurrentPolicy.load(job['behavior_checkpoint'],FEATURES,ACTIONS)
    assert policy.updates==receipt['updates_before']==receipt['updates_after']==job['model_updates']
    assert policy.gamma==job['gamma'] and policy.memory_reset==job['memory_reset']
    policy.reset_episode();policy.rng=np.random.default_rng(job['policy_seed'])
    rows=[json.loads(x) for x in Path(job['actions']).read_text().splitlines()];n=len(rows)
    assert n==receipt['decisions']==receipt['transitions']>0
    states=np.array([encode(x['snapshot']) for x in rows])
    legal=np.array([[name in x['legal'] for name in ACTIONS] for x in rows])
    chosen=np.array([ACTIONS.index(x['action']) for x in rows])
    for state,mask,action in zip(states,legal,chosen):
        assert policy.act(state,mask,job['mode']!='evaluate')==action
    rewards=np.array([x['reward'] for x in rows]);events=[]
    for i,row in enumerate(rows):
        c=row['reward_components']
        assert set(c)=={'terminal','potential_previous','potential_next','scale','combat_previous','combat_next','combat_event'}
        old=capacity_potential(states[i]);nxt=0 if i==n-1 else capacity_potential(states[i+1])
        bonus=100 if i==n-1 and receipt['result']=='Victory' else 0
        np.testing.assert_allclose([c['potential_previous'],c['potential_next']],[old,nxt],atol=1e-12,rtol=0)
        assert c['scale']==job['reward_scale']==policy.reward_scale and c['terminal']==bonus
        if i:assert c['combat_previous']==rows[i-1]['reward_components']['combat_next']
        event=(c['combat_next']['killed']-c['combat_previous']['killed'])/100
        assert event>=0 and abs(event-c['combat_event'])<1e-12;events.append(event)
        assert abs(row['reward']-policy.reward_scale*(bonus+policy.gamma*nxt-old+event))<1e-12
    assert abs(sum(rewards)-receipt['reward'])<1e-10
    discounted=float(np.dot(rewards,policy.gamma**np.arange(n)))
    telescope=-policy.reward_scale*capacity_potential(states[0])+policy.reward_scale*sum(policy.gamma**i*x for i,x in enumerate(events))
    if receipt['result']=='Victory':telescope+=policy.gamma**(n-1)
    assert abs(discounted-telescope)<1e-10
    journal=[json.loads(x) for x in Path(job['journal']).read_text().splitlines()]
    assert len(journal)==2*n and Path(job['journal']).stat().st_size==receipt['journal_bytes']
    for i,row in enumerate(rows):
        assert journal[2*i]=={'event':'decision','index':i,'decision':{k:v for k,v in row.items() if k not in ['reward','reward_components']}}
        assert journal[2*i+1]=={'event':'transition','index':i,'reward':row['reward'],'components':row['reward_components']}
    version=list(get_replay_version(job['replay']))
    assert version==list(receipt['replay_version'])==['Base75689','B89B5D6FA7CBF6452E721311BFBC6CB2']
    assert Path(job['replay']).stat().st_size==receipt['replay_bytes']>0
    if job['mode']=='train':
        with np.load(job['trajectory'],allow_pickle=False) as archive:data={k:archive[k] for k in archive.files}
        metadata=json.loads(str(data.pop('metadata')))
        assert all(metadata[k]==v for k,v in job.items() if k!='model_updates') and metadata['result']==receipt['result']
        assert metadata['updates']==job['model_updates']
        if 'model_updates' in metadata:assert metadata['model_updates']==job['model_updates']
        assert metadata['features']==FEATURES and metadata['actions_schema']==ACTIONS and metadata['algorithm']==policy.algorithm
        expected=policy.episode(states,chosen,legal,rewards)
        assert set(data)==set(expected)
        for key,value in expected.items():np.testing.assert_array_equal(data[key],value)
        assert digest(job['trajectory'])==receipt['trajectory_sha256'] and receipt['trajectory_rows']==n
    else:assert not Path(job['trajectory']).exists()
    return {'passed':True,'discounted_return':discounted,'decisions':n,'choices_rewards_journal_replay_verified':True}
