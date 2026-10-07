"""Supervised ability-identity ablation with all old argument inputs retained."""
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from src.learning.argument_train import collect
from src.learning.imitation import FactorPolicy
from src.learning.imitation_train import equal_replay_weights, metrics
from src.learning.teacher_states import teacher_states

root=Path('logs/roadmap');output=root/'arguments-direct-ability-01';output.mkdir(exist_ok=False)
macro_path=root/'imitation-prefix-240-01/policy.npz';macro=FactorPolicy.load(macro_path)
train=[root/f'issued-{i}' for i in [51574,51573,51958,51890,51891]]
validation=[root/'issued-50925',root/'issued-51960-p1']
contract={'scope':'supervised explicit selected-ability ablation; reused diagnostic validation, no live promotion',
          'epochs':600,'seed':5001,'train':[str(p) for p in train],'validation':[str(p) for p in validation],
          'change':'append chosen raw ability one-hot to all existing argument inputs; base-relative point labels unchanged',
          'gate':'lower valid-target error on both diagnostic games and no lower mode/alliance accuracy; no competent imitation or RL readiness claim',
          'macro_sha256':hashlib.sha256(macro_path.read_bytes()).hexdigest()}
(output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')

def augment(x,directories):
    abilities=[command['ability'] for d in directories for row,_ in teacher_states(d) for command in row['commands']]
    assert len(abilities)==len(x)
    chosen=np.zeros((len(x),macro.sizes['ability']),np.float32)
    chosen[np.arange(len(x)),abilities]=1
    return np.concatenate((x,chosen),axis=1)

start=time.monotonic()
x,labels,points,ranges,sources=collect(train,macro,None);x=augment(x,train)
policy=FactorPolicy(x.shape[1],1,macro.unit_types,seed=5001)
policy.feature_mean=x.mean(axis=0);policy.feature_scale=np.maximum(x.std(axis=0),.1)
weights=equal_replay_weights(np.ones(len(x)),ranges)
active=np.flatnonzero(np.any(x!=policy.feature_mean,axis=0));px=x[:,active]
rng=np.random.default_rng(5001)
for epoch in range(600):
    order=rng.permutation(len(x))
    for begin in range(0,len(x),128):
        ix=order[begin:begin+128]
        policy.learn(px[ix],{k:v[ix] for k,v in labels.items()},points[ix],weights=weights[ix],feature_indices=active)
    if epoch%100==0:print(json.dumps({'epoch':epoch,'wall_seconds':time.monotonic()-start}),flush=True)
baseline=FactorPolicy.load(root/'arguments-full-human-01/arguments.npz')
results=[]
for directory in validation:
    vx,vy,vpoints,_,vs=collect([directory],macro,None)
    assert not {s['sha256'] for s in sources}&{s['sha256'] for s in vs}
    old=metrics(baseline,vx,vy,vpoints);ax=augment(vx,[directory]);new=metrics(policy,ax,vy,vpoints)
    mask=(vy['mode']==1)&vy['point_valid'].astype(bool)
    old_point=baseline.predict(vx)['point'][:,:2];new_point=policy.predict(ax)['point'][:,:2]
    results.append({'dataset':str(directory),'baseline':old,'direct':new,'point_only':{'commands':int(mask.sum()),
                    'base_mean_error_tiles':float(np.linalg.norm(old_point[mask]-vpoints[mask],axis=1).mean()*128),
                    'direct_mean_error_tiles':float(np.linalg.norm(new_point[mask]-vpoints[mask],axis=1).mean()*128)}})
report=dict(contract,status='completed',sources=sources,commands=len(x),training=metrics(policy,x,labels,points),
            validation_results=results,wall_seconds=time.monotonic()-start,
            gate_passed=all(r['direct']['target_mean_error_tiles']<r['baseline']['target_mean_error_tiles'] and
                            all(r['direct']['head_accuracy'][k]>=r['baseline']['head_accuracy'][k] for k in ['mode','alliance']) for r in results),
            argument_input='group_features_plus_ability_onehot',point_origin='base')
policy.save(output/'arguments.npz',report)
report['checkpoint_sha256']=hashlib.sha256((output/'arguments.npz').read_bytes()).hexdigest()
(output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
