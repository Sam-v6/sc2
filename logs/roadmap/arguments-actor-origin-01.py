"""Controlled point-reference ablation; unchanged teaching inputs and fit budget."""
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from src.learning.argument_train import collect
from src.learning.global_imitation import global_features, coordinate_signs
from src.learning.imitation import FactorPolicy
from src.learning.imitation_train import equal_replay_weights, metrics
from src.learning.teacher_states import teacher_states, own_actors

root=Path('logs/roadmap');output=root/'arguments-actor-origin-01';output.mkdir(exist_ok=False)
macro_path=root/'imitation-prefix-240-01/policy.npz';macro=FactorPolicy.load(macro_path)
train=[root/f'issued-{i}' for i in [51574,51573,51958,51890,51891]]
validation=[root/'issued-50925',root/'issued-51960-p1']
contract={'scope':'supervised actor-centroid versus base-origin target reference; reused diagnostic validation, no live promotion',
          'epochs':600,'seed':5001,'train':[str(p) for p in train],'validation':[str(p) for p in validation],
          'change':'point labels relative to selected-group centroid; all other inputs, heads, normalization, weights and optimizer unchanged',
          'gate':'mean valid-target distance lower in both diagnostic held games; no competent imitation or RL readiness claim',
          'macro_sha256':hashlib.sha256(macro_path.read_bytes()).hexdigest()}
(output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')

def offsets(directories):
    values=[]
    for directory in directories:
        for row,state in teacher_states(directory):
            actors={u['tag']:u for u in own_actors(state)}
            _,origin=global_features(state,macro.unit_types,macro.sizes['ability'],canonical=True,summarize=True)
            signs=coordinate_signs(state,origin)
            for command in row['commands']:
                center=np.array([actors[t]['position'][:2] for t in command['units']]).mean(axis=0)
                values.append((center-origin)*signs/128)
    return np.array(values)

start=time.monotonic()
x,labels,points,ranges,sources=collect(train,macro,None)
shift=offsets(train);assert shift.shape==points.shape
relative=points-shift
policy=FactorPolicy(x.shape[1],1,macro.unit_types,seed=5001)
policy.feature_mean=x.mean(axis=0);policy.feature_scale=np.maximum(x.std(axis=0),.1)
weights=equal_replay_weights(np.ones(len(x)),ranges)
rng=np.random.default_rng(5001)
for epoch in range(600):
    order=rng.permutation(len(x))
    for begin in range(0,len(x),128):
        ix=order[begin:begin+128]
        policy.learn(x[ix],{k:v[ix] for k,v in labels.items()},relative[ix],weights=weights[ix])
    if epoch%100==0:print(json.dumps({'epoch':epoch,'wall_seconds':time.monotonic()-start}),flush=True)
baseline=FactorPolicy.load(root/'arguments-full-human-01/arguments.npz')
results=[]
for directory in validation:
    vx,vy,vpoints,_,vs=collect([directory],macro,None)
    assert not {s['sha256'] for s in sources}&{s['sha256'] for s in vs}
    vshift=offsets([directory]);actual=policy.predict(vx)['point'][:,:2]+vshift
    original=baseline.predict(vx)['point'][:,:2]
    valid=vy['point_valid'].astype(bool)
    results.append({'dataset':str(directory),'commands':len(vx),'valid_targets':int(valid.sum()),
                    'base_mean_error_tiles':float(np.linalg.norm(original[valid]-vpoints[valid],axis=1).mean()*128),
                    'actor_mean_error_tiles':float(np.linalg.norm(actual[valid]-vpoints[valid],axis=1).mean()*128),
                    'actor_heads':metrics(policy,vx,vy,vpoints-vshift)['head_accuracy']})
report=dict(contract,status='completed',sources=sources,commands=len(x),training=metrics(policy,x,labels,relative),
            validation_results=results,wall_seconds=time.monotonic()-start,
            gate_passed=all(r['actor_mean_error_tiles']<r['base_mean_error_tiles'] for r in results),
            point_origin='selected_group_centroid')
policy.save(output/'arguments.npz',report)
report['checkpoint_sha256']=hashlib.sha256((output/'arguments.npz').read_bytes()).hexdigest()
(output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
