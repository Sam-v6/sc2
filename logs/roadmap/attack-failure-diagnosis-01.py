"""Component errors and fog-safe spatial cues, without fitting any model."""
import hashlib
import json
from pathlib import Path
import numpy as np
from src.learning.actor_selection import group_features
from src.learning.global_imitation import global_features, coordinate_signs
from src.learning.imitation import FactorPolicy
from src.learning.imitation_play import decode_commands, replace_arguments
from src.learning.teacher_states import teacher_states, own_actors
root = Path('logs/roadmap')
macro = FactorPolicy.load(root/'imitation-prefix-240-01/policy.npz')
models = {'baseline':root/'arguments-full-human-01/arguments.npz', 'coverage':root/'arguments-matchup-coverage-01/arguments.npz'}
policies = {k:FactorPolicy.load(v) for k,v in models.items()}
report = {'scope':'attack argument diagnosis; oracle ability and actor group, no training or hidden enemy information', 'models':{k:{'path':str(v),'sha256':hashlib.sha256(v.read_bytes()).hexdigest()} for k,v in models.items()}, 'games':[]}
for directory in (root/'issued-50925',root/'issued-51960-p1',root/'issued-51959-held-01'):
    static=json.loads((directory/'static.json').read_text());catalog={a['ability_id']:a for a in static['game_data']['abilities']}
    bindings={str(directory/name):hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in ('dataset.json','static.json','examples.jsonl.gz')}
    rows=[]
    for row,state in teacher_states(directory):
        actors={u['tag']:u for u in own_actors(state)}
        x,origin=global_features(state,macro.unit_types,macro.sizes['ability'],canonical=True,summarize=True)
        for truth in row['commands']:
            if truth['ability']!=23:continue
            group=[actors[t] for t in truth['units']]
            features=group_features(state,group,macro.unit_types,macro.sizes['ability'],origin,macro.command_context(x,23))
            result={'point':truth['target_point'] is not None,'models':{}}
            if truth['target_point'] is not None:
                target=np.array(truth['target_point'])
                for label,units in [('visible_enemy', [u for u in state['units'] if u['alliance']==4]),('enemy_memory',state.get('memory',[]))]:
                    distances=[float(np.linalg.norm(np.array(u['position'][:2])-target)) for u in units]
                    result[label+'_distance']=min(distances) if distances else None
            for name,policy in policies.items():
                prediction=replace_arguments({},policy.predict(features[None,:]),coordinate_signs(state,origin));prediction['ability']=np.zeros((1,macro.sizes['ability']));prediction['point']=prediction['point'][:,:2]
                commands,_=decode_commands(state,[dict(group[0],position=[*origin,0])],prediction,{group[0]['tag']:{23}},catalog,macro.unit_types,state['map_size'],chosen_abilities=[23])
                assert len(commands)==1
                c=commands[0];mode_correct=(c.target_unit is not None)==(truth['target_unit'] is not None) and (c.target_point is not None)==(truth['target_point'] is not None) and c.autocast==truth['autocast']
                detail={'mode_correct':bool(mode_correct),'queue_correct':c.queue==truth['queue'],'unit_identity_correct':c.target_unit==truth['target_unit'] if truth['target_unit'] is not None else None,'point_error':None}
                if truth['target_point'] is not None and c.target_point is not None:detail['point_error']=float(np.linalg.norm(np.array(c.target_point)-truth['target_point']))
                result['models'][name]=detail
            rows.append(result)
    summary={}
    for name in models:
        details=[r['models'][name] for r in rows];point=[r['point_error'] for r in details if r['point_error'] is not None];unit=[r['unit_identity_correct'] for r in details if r['unit_identity_correct'] is not None]
        summary[name]={'mode_accuracy':float(np.mean([r['mode_correct'] for r in details])),'queue_accuracy':float(np.mean([r['queue_correct'] for r in details])),'unit_targets':len(unit),'unit_identity_accuracy':float(np.mean(unit)) if unit else None,'decoded_point_commands':len(point),'point_within_2_tiles':sum(d<=2 for d in point),'point_median_error_tiles':float(np.median(point)) if point else None}
    pointrows=[r for r in rows if r['point']]
    cues={}
    for label in ('visible_enemy','enemy_memory'):
        values=[r[label+'_distance'] for r in pointrows if r[label+'_distance'] is not None]
        cues[label]={'point_commands_with_candidate':len(values),'within_5_tiles':sum(v<=5 for v in values),'median_distance_tiles':float(np.median(values)) if values else None}
    assert bindings=={path:hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in bindings}
    report['games'].append({'dataset':str(directory),'bindings':bindings,'attack_commands':len(rows),'point_commands':len(pointrows),'components':summary,'fog_safe_cues':cues})
report['status']='completed_without_fitting'
(root/'attack-failure-diagnosis-01.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['games'],indent=2))
