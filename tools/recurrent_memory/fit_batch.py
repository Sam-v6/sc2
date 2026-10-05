"""Exactly four compatible on-policy episodes per strength-study PPO update."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from recurrent_policy import RecurrentPolicy,update


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fit(task):
    assert task['purpose']=='controlled-strength-study' and len(task['jobs'])==4
    for path,expected in task['hashes'].items():assert digest(path)==expected,path
    assert len({job['seed'] for job in task['jobs']})==4
    assert digest(task['behavior_checkpoint'])==task['behavior_sha256']
    episodes=[];metas=[]
    for job in task['jobs']:
        assert job['mode']=='train' and job['purpose']==task['purpose'] and job['role']==task['role']
        receipt=json.loads(Path(job['receipt']).read_text())
        assert all(receipt[key]==value for key,value in job.items()) and receipt['episode_audit']['passed']
        assert receipt['trajectory_sha256']==digest(job['trajectory'])
        with np.load(job['trajectory'],allow_pickle=False) as archive:data={key:archive[key] for key in archive.files}
        meta=json.loads(str(data.pop('metadata')))
        assert all(meta[key]==value for key,value in job.items()) and meta['result']==receipt['result']
        assert job['behavior_checkpoint']==task['behavior_checkpoint'] and job['behavior_checkpoint_sha256']==task['behavior_sha256']
        episodes.append(data);metas.append(meta)
    first=metas[0];policy=RecurrentPolicy.load(task['behavior_checkpoint'],first['features'],first['actions_schema'])
    for meta in metas:
        assert meta['features']==policy.features and meta['actions_schema']==policy.actions
        assert meta['updates']==policy.updates and meta['gamma']==policy.gamma and meta['memory_reset']==policy.memory_reset
        assert meta['reward_version']==policy.reward_version and meta['reward_scale']==policy.reward_scale
    before=policy.updates;result=update(policy,episodes)
    assert policy.updates-before==16 and result['updates']==16
    policy.save(task['target'])
    for path,expected in task['hashes'].items():assert digest(path)==expected,path
    result.update(status='completed',role=task['role'],checkpoint=task['target'],sha256=digest(task['target']),
                  updates_before=before,optimizer_clock=policy.updates,episodes=policy.episodes,attempts=policy.attempts,
                  input_task_sha256=digest(task['task_path']),purpose=task['purpose'])
    path=Path(task['fit_receipt']);assert not path.exists()
    with path.open('x') as file:json.dump(result,file,indent=2,allow_nan=False);file.write('\n')
    return result


if __name__=='__main__':
    path=Path(sys.argv[1]);task=json.loads(path.read_text());assert task['task_path']==str(path.resolve())
    print(json.dumps(fit(task)),flush=True)
