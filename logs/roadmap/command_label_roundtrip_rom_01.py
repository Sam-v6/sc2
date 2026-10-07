"""Check whether perfect supervised labels survive the live decoder."""
import hashlib
import json
from pathlib import Path
import numpy as np
from src.learning.imitation import FactorPolicy, action_labels
from src.learning.teacher_states import teacher_states, own_actors
from src.learning.global_imitation import global_features, coordinate_signs
from src.learning.imitation_play import decode_commands
root=Path('logs/roadmap');out=root/'command-label-roundtrip-rom-01';out.mkdir(exist_ok=False)
dataset=root/'issued-51482-rom-masked-01';path=root/'imitation-prefix-240-01/policy.npz';macro=FactorPolicy.load(path)
files=[Path(__file__),path,*(dataset/n for n in ('dataset.json','static.json','examples.jsonl.gz')),*sorted(Path('src/learning').glob('*.py'))]
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=hashes();static=json.loads((dataset/'static.json').read_text());catalog={a['ability_id']:a for a in static['game_data']['abilities']};records=[]
for row,state in teacher_states(dataset):
    _,origin=global_features(state,macro.unit_types,macro.sizes['ability'],canonical=True,summarize=True,semantics=macro.evidence.get('action_history_encoder')=='roles_targets_age',upgrade_count=macro.evidence.get('upgrade_count',0))
    by_tag={u['tag']:u for u in own_actors(state)}
    for truth in row['commands']:
        labels,point=action_labels(truth,state,{'position':origin},macro.unit_types,row.get('next_action_delay'))
        # Deliberately supply teacher labels; this tests representability only.
        output={name:np.full((1,size),-1000.,dtype=np.float32) for name,size in macro.sizes.items()}
        for name,value in labels.items():
            if name in output:output[name][0,max(0,value)]=1000.
        canonical_point=point*coordinate_signs(state,origin)
        output['point']=(canonical_point*coordinate_signs(state,origin))[None,:]
        proxy=dict(by_tag[truth['units'][0]],position=[*origin,0.])
        commands,_=decode_commands(state,[proxy],output,{proxy['tag']:{truth['ability']}},catalog,macro.unit_types,state['map_size'],chosen_abilities=[truth['ability']])
        actual=commands[0].as_dict() if commands else None
        if actual:actual['units']=truth['units']
        error=None
        if truth['target_point'] is not None and actual is not None and actual['target_point'] is not None:error=float(np.linalg.norm(np.asarray(truth['target_point'])-actual['target_point']))
        fields={name:bool(actual is not None and actual[name]==truth[name]) for name in ('ability','units','target_unit','queue','autocast')}
        fields['target_point']=bool(actual is not None and ((truth['target_point'] is None and actual['target_point'] is None) or (error is not None and error<=0.0001)))
        records.append({'action_loop':row['action_loop'],'teacher':truth,'predicted':actual,'fields_correct':fields,'point_error':error,'target_unit_in_current_entities':truth['target_unit'] is None or any(u['tag']==truth['target_unit'] for u in state['units'])})
assert hashes()==before
report={'status':'completed','scope':'teacher labels, ability, actors and synthetic ability availability; label/decoder representability only, not native legality or learned competence','commands':len(records),'complete_hits':sum(all(r['fields_correct'].values()) for r in records),'field_hits':{name:sum(r['fields_correct'][name] for r in records) for name in records[0]['fields_correct']},'target_units_absent':sum(not r['target_unit_in_current_entities'] for r in records),'maximum_point_error':max(r['point_error'] or 0 for r in records),'records':records,'files_before':before,'files_after':hashes()}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('records','files_before','files_after')},indent=2))
