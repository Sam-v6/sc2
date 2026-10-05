"""Single real-episode backend smoke; not the controlled strength experiment."""
import json
import hashlib
from pathlib import Path
import sys
import numpy as np
from recurrent_policy import RecurrentPolicy,update

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()



def fit(job,receipt):
    assert job['purpose']=='engineering-smoke-only' and job['mode']=='train'
    assert digest(job['behavior_checkpoint'])==job['behavior_checkpoint_sha256']
    assert digest(job['trajectory'])==receipt['trajectory_sha256']
    with np.load(job['trajectory'],allow_pickle=False) as archive:
        data={key:archive[key] for key in archive.files}
    metadata=json.loads(str(data.pop('metadata')))
    assert all(metadata[key]==value for key,value in job.items())
    policy=RecurrentPolicy.load(job['behavior_checkpoint'],metadata['features'],metadata['actions_schema'])
    assert policy.memory_reset==job['memory_reset']
    assert metadata['gamma']==policy.gamma and metadata['updates']==policy.updates
    assert metadata['result']==receipt['result']
    result=update(policy,[data])
    target=Path(job['fitted_checkpoint']);policy.save(target)
    result.update(status='completed',role=job['role'],checkpoint=str(target),sha256=digest(target),
                  behavior_sha256=job['behavior_checkpoint_sha256'],trajectory_sha256=receipt['trajectory_sha256'],
                  episodes=policy.episodes,optimizer_clock=policy.updates,purpose=job['purpose'])
    output=Path(job['fit_receipt']);assert not output.exists()
    with output.open('x') as file:
        json.dump(result,file,indent=2,allow_nan=False);file.write('\n')
    return result


if __name__=='__main__':
    inputs=json.loads(Path(sys.argv[1]).read_text());job=inputs['jobs'][int(sys.argv[2])]
    receipt=json.loads(Path(job['receipt']).read_text())
    print(json.dumps(fit(job,receipt)))
