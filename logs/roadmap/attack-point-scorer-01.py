"""Supervised attack-point component experiment; no live policy replacement."""
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from src.learning.global_imitation import global_features, coordinate_signs
from src.learning.imitation import FactorPolicy
from src.learning.actor_selection import group_features
from src.learning.spatial_construction import candidate_features, decode_terrain, spatial_candidates
from src.learning.teacher_states import teacher_states, own_actors

root = Path('logs/roadmap')
out = root / 'attack-point-scorer-01'
out.mkdir(exist_ok=False)
train = [root / f'issued-{i}' for i in (51574, 51573, 51958, 51890, 51891)] + [root / 'issued-51957-p1']
validation = [root / 'issued-50925', root / 'issued-51960-p1', root / 'issued-51959-held-01']
macro_path = root / 'imitation-prefix-240-01/policy.npz'
argument_path = root / 'arguments-full-human-01/arguments.npz'
macro = FactorPolicy.load(macro_path)
arguments = FactorPolicy.load(argument_path)
structures = json.loads((root / 'spatial-prefix-240-01/report.json').read_text())['structure_types']
files = [Path(__file__), macro_path, argument_path, root / 'spatial-prefix-240-01/report.json']
files += [Path('src/learning') / (n + '.py') for n in ('global_imitation','imitation','actor_selection','spatial_construction','teacher_states','gameplay')]
for directory in train + validation:
    files += [directory / n for n in ('dataset.json','static.json','examples.jsonl.gz')]
def inventory():
    return {str(p): {'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files}
bindings = inventory()
train_hashes = {json.loads((p/'dataset.json').read_text())['sha256'] for p in train}
held_hashes = {json.loads((p/'dataset.json').read_text())['sha256'] for p in validation}
assert not train_hashes & held_hashes
# Vocabulary is derived only from selected actors in the training games.
types = set()
for directory in train:
    for row,state in teacher_states(directory):
        own={u['tag']:u for u in own_actors(state)}
        for c in row['commands']:
            if c['ability']==23 and c['target_point'] is not None:
                types.update(own[t]['unit_type'] for t in c['units'])
vocab = sorted(types)
contract = {'scope':'supervised Attack point component, human ability/group/point-mode supplied; all three games are diagnostic validation',
    'train':[str(p) for p in train],'validation':[str(p) for p in validation],
    'epochs':100,'seed':5007,'negative_candidates_per_command':64,'candidate_spacing_tiles':2,
    'gate':'at least 10 percentage points higher within-2-tile point accuracy AND at least 10 percent lower mean point error in each diagnostic game',
    'stop':'one fixed fit, no epoch/capacity sweep or live promotion; does not establish full-command imitation or RL readiness',
    'features':'existing terrain/local observed-unit candidate features plus training-derived selected actor type composition and group size; frozen macro context',
    'selected_type_vocabulary':vocab,'files_before':bindings,'point_origin':'absolute map grid'}
(out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')

def rows(directory):
    receipt=json.loads((directory/'dataset.json').read_text())
    assert receipt['status']=='completed' and not receipt['disable_fog']
    static=json.loads((directory/'static.json').read_text())
    terrain=decode_terrain(static['terrain'])
    for row,state in teacher_states(directory):
        own={u['tag']:u for u in own_actors(state)}
        x,origin=global_features(state,macro.unit_types,macro.sizes['ability'],canonical=True,summarize=True)
        for truth in row['commands']:
            if truth['ability']!=23 or truth['target_point'] is None:continue
            group=[own[t] for t in truth['units']]
            yield state,group,origin,macro.command_context(x,23),terrain,np.asarray(truth['target_point']),truth

def features(state,group,origin,context,points,terrain):
    base=candidate_features(state,group,origin,context,points,terrain,0,structures)
    composition=np.zeros(len(vocab)+2,dtype=np.float32)
    for unit in group:
        composition[vocab.index(unit['unit_type'])+1 if unit['unit_type'] in vocab else 0]+=1/len(group)
    composition[-1]=np.log1p(len(group))/3
    return np.concatenate((base,np.broadcast_to(composition,(len(points),len(composition)))),axis=1)

start=time.monotonic();rng=np.random.default_rng(5007)
xs=[];ys=[];ws=[];training_coverage=[]
for directory in train:
    begin=len(xs);quantization=[]
    for state,group,origin,context,terrain,truth,_ in rows(directory):
        points=spatial_candidates(state['map_size'],0,spacing=2)
        d=np.linalg.norm(points-truth,axis=1);positive=int(d.argmin());quantization.append(float(d[positive]))
        eligible=np.flatnonzero(np.arange(len(points))!=positive)
        global_neg=rng.choice(eligible,32,replace=False)
        local=np.argsort(d)[1:65];local_neg=rng.choice(local,16,replace=False)
        center=np.asarray([u['position'][:2] for u in group]).mean(axis=0)
        near=np.argsort(np.linalg.norm(points-center,axis=1));near=near[near!=positive][:256]
        actor_neg=rng.choice(near,16,replace=False)
        indices=np.concatenate(([positive],global_neg,local_neg,actor_neg))
        xs.append(features(state,group,origin,context,points[indices],terrain))
        ys.append(np.r_[1,np.zeros(64,dtype=int)]);ws.append(np.r_[1.,np.full(64,1/64)])
    count=len(xs)-begin
    assert count>0
    for i in range(begin,len(xs)):ws[i]/=count
    training_coverage.append({'dataset':str(directory),'commands':count,'candidate_within_2_tiles':sum(d<=2 for d in quantization),'max_quantization_error_tiles':max(quantization)})
x=np.concatenate(xs);y=np.concatenate(ys);weights=np.concatenate(ws);weights*=len(weights)/weights.sum()
policy=FactorPolicy(x.shape[1],2,[],seed=5007)
policy.feature_mean=x.mean(axis=0);policy.feature_scale=np.maximum(x.std(axis=0),.1)
active=np.flatnonzero(np.any(x!=policy.feature_mean,axis=0));px=x[:,active]
labels={k:np.full(len(x),-1,dtype=int) for k in policy.sizes};labels.update(ability=y,point_valid=np.zeros(len(x),dtype=int))
empty_points=np.full((len(x),2),np.nan,np.float32)
for epoch in range(100):
    order=rng.permutation(len(x))
    for begin in range(0,len(x),512):
        ix=order[begin:begin+512]
        policy.learn(px[ix],{k:v[ix] for k,v in labels.items()},empty_points[ix],weights=weights[ix],feature_indices=active)
    if epoch%20==0:print(json.dumps({'epoch':epoch,'wall_seconds':time.monotonic()-start}),flush=True)
results=[]
for directory in validation:
    errors=[];baseline_errors=[];quantization=[];selected=[]
    for state,group,origin,context,terrain,truth,c in rows(directory):
        points=spatial_candidates(state['map_size'],0,spacing=2)
        fx=features(state,group,origin,context,points,terrain)
        logits=policy.predict(fx)['ability'];chosen=points[int((logits[:,1]-logits[:,0]).argmax())]
        ax=group_features(state,group,macro.unit_types,macro.sizes['ability'],origin,context)
        original=origin+128*arguments.predict(ax[None,:])['point'][0,:2]*coordinate_signs(state,origin)
        original=np.clip(original,[0,0],np.asarray(state['map_size'])-.01)
        errors.append(float(np.linalg.norm(chosen-truth)));baseline_errors.append(float(np.linalg.norm(original-truth)))
        quantization.append(float(np.linalg.norm(points-truth,axis=1).min()))
        selected.append({'loop':state['game_loop'],'teacher_point':truth.tolist(),'chosen_point':chosen.tolist(),'error_tiles':errors[-1]})
    def stats(values):return {'commands':len(values),'within_2_tiles':sum(v<=2 for v in values),'within_2_accuracy':float(np.mean(np.asarray(values)<=2)),'mean_error_tiles':float(np.mean(values)),'median_error_tiles':float(np.median(values))}
    result={'dataset':str(directory),'scorer':stats(errors),'baseline':stats(baseline_errors),'quantization':stats(quantization),'predictions':selected}
    results.append(result);print(json.dumps({k:v for k,v in result.items() if k!='predictions'}),flush=True)
assert inventory()==bindings
passed=all(r['scorer']['within_2_accuracy']>=r['baseline']['within_2_accuracy']+.1 and r['scorer']['mean_error_tiles']<=.9*r['baseline']['mean_error_tiles'] for r in results)
report=dict(contract,status='completed',training_commands=len(xs),training_candidates=len(x),training_quantization=training_coverage,validation_results=results,gate_passed=passed,wall_seconds=time.monotonic()-start,files_after=inventory())
policy.save(out/'points.npz',report)
report['checkpoint_sha256']=hashlib.sha256((out/'points.npz').read_bytes()).hexdigest()
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'completed','gate_passed':passed,'wall_seconds':report['wall_seconds']}),flush=True)
