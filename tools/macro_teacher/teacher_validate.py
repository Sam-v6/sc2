"""Validate scripted requests, ordinary rewards and native demonstration evidence."""
import json
from pathlib import Path
import numpy as np
from sc2.main import get_replay_version
from src.rl.terran import ACTIONS,FEATURES,encode,capacity_potential
from selector import choose
from recurrent_worker import digest


def validate(job,receipt):
    assert receipt['status'] in ['completed','truncated'] and receipt['result'] in ['Victory','Defeat','Tie']
    assert (receipt['status']=='truncated')==(receipt['result']=='Tie')
    assert receipt['updates_before']==receipt['updates_after']==0 and job['mode']=='evaluate'
    assert digest(job['behavior_checkpoint'])==job['behavior_checkpoint_sha256']
    assert digest(job['teacher_source'])==job['teacher_source_sha256'] and job['checkpoint_role']=='context_only_not_teacher_weights'
    rows=[json.loads(line) for line in Path(job['actions']).read_text().splitlines()];n=len(rows)
    assert n==receipt['decisions']==receipt['transitions']>0
    states=np.array([encode(row['snapshot']) for row in rows])
    legal=np.array([[a in row['legal'] for a in ACTIONS] for row in rows]);chosen=np.array([ACTIONS.index(row['action']) for row in rows])
    rewards=np.array([row['reward'] for row in rows])
    for i,row in enumerate(rows):
        assert choose(states[i],legal[i])==chosen[i] and isinstance(row['executed'],bool)
        c=row['reward_components'];old=capacity_potential(states[i]);nxt=0 if i==n-1 else capacity_potential(states[i+1])
        bonus=100 if i==n-1 and receipt['result']=='Victory' else 0
        np.testing.assert_allclose([c['potential_previous'],c['potential_next']],[old,nxt],atol=1e-12,rtol=0)
        assert c['scale']==job['reward_scale'] and c['terminal']==bonus
        if i:assert c['combat_previous']==rows[i-1]['reward_components']['combat_next']
        event=(c['combat_next']['killed']-c['combat_previous']['killed'])/100
        assert event>=0 and abs(event-c['combat_event'])<1e-12
        assert abs(row['reward']-job['reward_scale']*(bonus+job['gamma']*nxt-old+event))<1e-12
    assert abs(sum(rewards)-receipt['reward'])<1e-10
    journal=[json.loads(line) for line in Path(job['journal']).read_text().splitlines()]
    assert len(journal)==2*n and Path(job['journal']).stat().st_size==receipt['journal_bytes']
    for i,row in enumerate(rows):
        assert journal[2*i]=={'event':'decision','index':i,'decision':{k:v for k,v in row.items() if k not in ['reward','reward_components']}}
        assert journal[2*i+1]=={'event':'transition','index':i,'reward':row['reward'],'components':row['reward_components']}
    assert list(get_replay_version(job['replay']))==list(receipt['replay_version'])==['Base75689','B89B5D6FA7CBF6452E721311BFBC6CB2']
    assert Path(job['replay']).stat().st_size==receipt['replay_bytes']>0
    with np.load(job['trajectory'],allow_pickle=False) as archive:data={key:archive[key] for key in archive.files}
    meta=json.loads(str(data.pop('metadata')))
    assert all(meta[key]==value for key,value in job.items()) and meta['result']==receipt['result']
    assert meta['algorithm']=='macro-teacher-v1' and meta['features']==FEATURES and meta['actions_schema']==ACTIONS
    assert meta['on_policy_ppo_reuse_allowed'] is False and meta['scripted_macro'] is True
    terminal=np.zeros(n,dtype=bool);terminal[-1]=True
    expected={'states':states,'chosen':chosen,'legal':legal,'rewards':rewards,'terminal':terminal}
    assert set(data)==set(expected)
    for key,array in expected.items():np.testing.assert_array_equal(data[key],array)
    assert digest(job['trajectory'])==receipt['trajectory_sha256'] and receipt['trajectory_rows']==n
    production=[json.loads(line) for line in Path(job['production']).read_text().splitlines()]
    assert production and Path(job['production']).stat().st_size==receipt['production_bytes']
    for event in production:
        assert event['event'] in ['unit_appeared','building_completed'] and 0<=event['time']<=receipt['game_seconds']
        assert isinstance(event['tag'],int) and event['tag']>0 and isinstance(event['type'],str)
    assert len({(e['event'],e['tag']) for e in production})==len(production)
    commands=[json.loads(line) for line in Path(job['commands']).read_text().splitlines()]
    assert commands and Path(job['commands']).stat().st_size==receipt['command_bytes']
    assert all(0<=row['time']<=receipt['game_seconds'] and 0<=row['decision_index']<n for row in commands)
    assert all(isinstance(c['unit'],int) and c['unit']>0 and isinstance(c['queue'],bool) and isinstance(c['ability'],str)
               for row in commands for c in row['queued'])
    return {'passed':True,'discounted_return':float(np.dot(rewards,job['gamma']**np.arange(n))),
            'accepted_requests':sum(row['executed'] for row in rows),'observed_unit_events':sum(e['event']=='unit_appeared' for e in production),
            'observed_complete_building_events':sum(e['event']=='building_completed' for e in production)}
