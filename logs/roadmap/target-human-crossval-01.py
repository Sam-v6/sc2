"""Fixed-design leave-one-human-game-out target pointer audit, no live use."""
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from src.learning.imitation import FactorPolicy
from src.learning.global_imitation import global_features
from src.learning.target_selection import target_features
from src.learning.teacher_states import teacher_states, own_actors

root=Path('logs/roadmap')
output=root/'target-human-crossval-01'
output.mkdir(exist_ok=False)
macro=FactorPolicy.load(root/'imitation-prefix-240-01/policy.npz')
ids=[51574,51573,51958,51890,51891,50925]
contract={'status':'declared','scope':'leave-one-whole-human-game-out unit-target imitation; no native skill',
          'replays':ids,'epochs':150,'seed':5004,'hyperparameters_unchanged':True,
          'baseline':'nearest selected-group center; no frozen argument baseline because its train sources overlap some folds',
          'gate':'diagnostic only; report all folds and combat strata; no live promotion or RL resumption'}
(output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')

def collect(replay):
    directory=root/f'issued-{replay}'
    receipt=json.loads((directory/'dataset.json').read_text())
    assert receipt['status']=='completed'
    rows,labels,weights,groups=[],[],[],[]
    missing=0
    for row,state in teacher_states(directory):
        actors={u['tag']:u for u in own_actors(state)}
        _,origin=global_features(state,macro.unit_types,macro.sizes['ability'],canonical=True,summarize=True)
        for command in row['commands']:
            if command['target_unit'] is None or command['autocast']:continue
            group=[actors[t] for t in command['units']]
            units,features=target_features(state,group,command['ability'],macro.unit_types,macro.sizes['ability'],origin)
            tags=[u['tag'] for u in units]
            if command['target_unit'] not in tags:
                missing+=1
                continue
            truth=tags.index(command['target_unit'])
            begin=len(labels)
            rows.append(features)
            labels.extend(int(i==truth) for i in range(len(tags)))
            weights.extend(1 if i==truth else 1/max(len(tags)-1,1) for i in range(len(tags)))
            positions=np.array([u['position'][:2] for u in units])
            center=np.array([u['position'][:2] for u in group]).mean(axis=0)
            groups.append({'begin':begin,'end':len(labels),'truth':truth,'ability':command['ability'],
                           'positions':positions,'alliance':units[truth]['alliance'],
                           'types':[u['unit_type'] for u in units],
                           'nearest':int(np.linalg.norm(positions-center,axis=1).argmin())})
    return np.concatenate(rows),np.array(labels),np.array(weights)/len(groups),groups,receipt['sha256'],missing

def audit(policy,x,groups):
    logits=policy.predict(x)['ability']
    strata={k:[] for k in ['all','enemy','attack_enemy']}
    for g in groups:
        score=logits[g['begin']:g['end']]
        predicted=int((score[:,1]-score[:,0]).argmax())
        truth=g['truth']
        result={'exact':predicted==truth,'type':g['types'][predicted]==g['types'][truth],
                'error':float(np.linalg.norm(g['positions'][predicted]-g['positions'][truth])),
                'nearest_exact':g['nearest']==truth}
        strata['all'].append(result)
        if g['alliance']==4:
            strata['enemy'].append(result)
            if g['ability']==23:strata['attack_enemy'].append(result)
    return {name:{'commands':len(v),**({k:float(np.mean([r[k] for r in v])) for k in v[0]} if v else {})}
            for name,v in strata.items()}

start=time.monotonic()
datasets={i:collect(i) for i in ids}
reports=[]
for held in ids:
    train=[i for i in ids if i!=held]
    assert datasets[held][4] not in [datasets[i][4] for i in train]
    x=np.concatenate([datasets[i][0] for i in train])
    y=np.concatenate([datasets[i][1] for i in train])
    w=np.concatenate([datasets[i][2] for i in train]);w*=len(w)/w.sum()
    policy=FactorPolicy(x.shape[1],2,[],seed=5004)
    policy.feature_mean=x.mean(axis=0);policy.feature_scale=np.maximum(x.std(axis=0),.1)
    active=np.flatnonzero(np.any(x!=policy.feature_mean,axis=0));px=x[:,active]
    labels={k:np.full(len(x),-1,dtype=int) for k in policy.sizes}
    labels.update(ability=y,point_valid=np.zeros(len(x),dtype=int))
    points=np.full((len(x),2),np.nan,np.float32)
    rng=np.random.default_rng(5004)
    for _ in range(150):
        order=rng.permutation(len(x))
        for begin in range(0,len(x),512):
            ix=order[begin:begin+512]
            policy.learn(px[ix],{k:v[ix] for k,v in labels.items()},points[ix],weights=w[ix],feature_indices=active)
    r={'held_replay':held,'train_replays':train,'sources':[datasets[i][4] for i in train],
       'held_source':datasets[held][4],'unavailable_held_targets':datasets[held][5],
       'held':audit(policy,datasets[held][0],datasets[held][3])}
    policy.save(output/f'held-{held}.npz',r)
    r['checkpoint_sha256']=hashlib.sha256((output/f'held-{held}.npz').read_bytes()).hexdigest()
    reports.append(r)
    (output/f'held-{held}.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r),flush=True)
report=dict(contract,status='completed',folds=reports,wall_seconds=time.monotonic()-start)
(output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
