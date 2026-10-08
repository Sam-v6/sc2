"""Fixed supervised target-pointer comparison on whole-human-game splits."""
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from src.learning.imitation import FactorPolicy
from src.learning.global_imitation import global_features, coordinate_signs
from src.learning.actor_selection import group_features
from src.learning.imitation_play import decode_commands, replace_arguments
from src.learning.target_selection import target_features
from src.learning.teacher_states import teacher_states, own_actors

root = Path('logs/roadmap')
output = root / 'target-human-fit-01'
output.mkdir(exist_ok=False)
macro_path = root / 'imitation-prefix-240-01/policy.npz'
argument_path = root / 'arguments-full-human-01/arguments.npz'
macro = FactorPolicy.load(macro_path)
arguments = FactorPolicy.load(argument_path)
contract = {'scope': 'supervised current-target identity with human ability/group/mode supplied; no live strength',
            'train': [51574,51573,51958,51890,51891], 'held': [50925],
            'epochs': 150, 'seed': 5004, 'seconds': None,
            'gate': 'held exact-target accuracy higher than frozen full-human arguments AND held target-distance lower; no live promotion',
            'macro_sha256': hashlib.sha256(macro_path.read_bytes()).hexdigest(),
            'argument_sha256': hashlib.sha256(argument_path.read_bytes()).hexdigest()}
(output / 'contract.json').write_text(json.dumps(contract, indent=2)+'\n')

def collect(ids):
    rows, labels, weights, groups, sources, unavailable = [], [], [], [], [], 0
    for replay in ids:
        directory = root / f'issued-{replay}'
        receipt = json.loads((directory/'dataset.json').read_text())
        assert receipt['status'] == 'completed'
        sources.append(receipt['sha256'])
        static = json.loads((directory/'static.json').read_text())
        catalog = {a['ability_id']:a for a in static['game_data']['abilities']}
        first = len(labels)
        commands = 0
        for row, state in teacher_states(directory):
            actors = {u['tag']:u for u in own_actors(state)}
            x, origin = global_features(state,macro.unit_types,macro.sizes['ability'],canonical=True,summarize=True)
            for command in row['commands']:
                target = command['target_unit']
                if target is None or command['autocast']:continue
                group = [actors[t] for t in command['units']]
                units, features = target_features(state,group,command['ability'],macro.unit_types,macro.sizes['ability'],origin)
                tags = [u['tag'] for u in units]
                if target not in tags:
                    unavailable += 1
                    continue
                truth = np.array([tag==target for tag in tags])
                begin = len(labels)
                rows.append(features)
                labels.extend(truth.astype(int))
                weights.extend(np.where(truth,1.,1./max(len(tags)-1,1)))
                context = macro.command_context(x,command['ability'])
                argument_x = group_features(state,group,macro.unit_types,macro.sizes['ability'],origin,context)
                prediction = replace_arguments({},arguments.predict(argument_x[None,:]),coordinate_signs(state,origin))
                prediction['ability'] = np.zeros((1,macro.sizes['ability']))
                prediction['point'] = prediction['point'][:,:2]
                prediction['mode'][:] = -100
                prediction['mode'][0,2] = 100
                decoded,_ = decode_commands(state,[dict(group[0],position=[*origin,0])],prediction,{group[0]['tag']:{command['ability']}},catalog,macro.unit_types,state['map_size'],chosen_abilities=[command['ability']])
                positions = np.array([u['position'][:2] for u in units])
                center = np.array([u['position'][:2] for u in group]).mean(axis=0)
                groups.append({'begin':begin,'end':len(labels),'tags':tags,'positions':positions,
                               'truth':tags.index(target),'ability':command['ability'],
                               'nearest':int(np.linalg.norm(positions-center,axis=1).argmin()),
                               'arguments': tags.index(decoded[0].target_unit) if decoded and decoded[0].target_unit in tags else None})
                commands += 1
        weights[first:] = [w/max(commands,1) for w in weights[first:]]
    return np.concatenate(rows),np.array(labels),np.array(weights),groups,sources,unavailable

def audit(policy,x,groups):
    logits = policy.predict(x)['ability']
    metrics = {k:[] for k in ['pointer','arguments','nearest']}
    by_ability = {}
    for group in groups:
        score = logits[group['begin']:group['end']]
        chosen = int((score[:,1]-score[:,0]).argmax())
        for name,index in [('pointer',chosen),('arguments',group['arguments']),('nearest',group['nearest'])]:
            error = None if index is None else float(np.linalg.norm(group['positions'][index]-group['positions'][group['truth']]))
            metrics[name].append((index==group['truth'],error))
        by_ability.setdefault(str(group['ability']),[]).append(chosen==group['truth'])
    return {'commands':len(groups), 'models':{name:{'exact_target_accuracy':float(np.mean([r[0] for r in values])),
            'mean_target_error_tiles':float(np.mean([r[1] for r in values if r[1] is not None])),
            'undecodable':sum(r[1] is None for r in values)} for name,values in metrics.items()},
            'pointer_by_ability':{k:{'commands':len(v),'accuracy':float(np.mean(v))} for k,v in by_ability.items()}}

start = time.monotonic()
x,y,w,groups,sources,missing = collect(contract['train'])
vx,_,_,vg,vs,vmissing = collect(contract['held'])
assert not set(sources)&set(vs)
policy = FactorPolicy(x.shape[1],2,[],seed=5004)
policy.feature_mean = x.mean(axis=0)
policy.feature_scale = np.maximum(x.std(axis=0),.1)
active = np.flatnonzero(np.any(x!=policy.feature_mean,axis=0))
train_x = x[:,active]
w *= len(w)/w.sum()
labels = {k:np.full(len(x),-1,dtype=int) for k in policy.sizes}
labels.update(ability=y,point_valid=np.zeros(len(x),dtype=int))
points = np.full((len(x),2),np.nan,np.float32)
rng = np.random.default_rng(5004)
for epoch in range(contract['epochs']):
    order = rng.permutation(len(x))
    for begin in range(0,len(x),512):
        index = order[begin:begin+512]
        policy.learn(train_x[index],{k:v[index] for k,v in labels.items()},points[index],weights=w[index],feature_indices=active)
    if epoch%25==0:print(json.dumps({'epoch':epoch,'wall_seconds':time.monotonic()-start}),flush=True)
report = dict(contract,status='completed',sources=sources,held_sources=vs,unavailable_training_targets=missing,
              unavailable_held_targets=vmissing,training=audit(policy,x,groups),held=audit(policy,vx,vg),wall_seconds=time.monotonic()-start)
h=report['held']['models'];report['gate_passed']=h['pointer']['exact_target_accuracy']>h['arguments']['exact_target_accuracy'] and h['pointer']['mean_target_error_tiles']<h['arguments']['mean_target_error_tiles']
policy.save(output/'targets.npz',report)
report['checkpoint_sha256']=hashlib.sha256((output/'targets.npz').read_bytes()).hexdigest()
(output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
