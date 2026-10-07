"""Event-conditional full-command fidelity; teacher history, no autonomous claim."""
import hashlib
import json
import gzip
from pathlib import Path
import time
import numpy as np
from src.learning.imitation import FactorPolicy,DELAYS
from src.learning.teacher_states import teacher_states,own_actors
from src.learning.global_imitation import global_features,coordinate_signs
from src.learning.actor_selection import actor_features,select_actors,group_features
from src.learning.imitation_play import decode_commands,replace_arguments

root=Path('logs/roadmap');out=root/'full-command-audit-rom-01';out.mkdir(exist_ok=False)
dataset=root/'issued-51482-rom-masked-01';capture=root/'replay-legality-rom-03'
paths=[root/'imitation-prefix-240-01/policy.npz',root/'actor-prefix-240-01/actors.npz',root/'arguments-prefix-240-01/arguments.npz']
macro,actors_policy,arguments=[FactorPolicy.load(p) for p in paths]
files=[Path(__file__),*paths,capture/'contract.json',capture/'report.json',capture/'availability.jsonl.gz']
files += [dataset/n for n in ('dataset.json','static.json','examples.jsonl.gz')]
files += [Path('src/learning')/(n+'.py') for n in ('imitation','teacher_states','global_imitation','actor_selection','imitation_play','gameplay','live')]
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=hashes()
contract={'scope':'frozen macro/actor/argument pipeline, no teacher ability/group; conditional on human event times and previous human commands; no spatial placement postprocessor or autonomous play',
 'dataset':str(dataset),'models':[str(p) for p in paths],
 'legality':'native pre-action availability from exact own-unit state match, resource requirements enabled',
 'fidelity':'ability + exact actor set + target unit or point within2tiles + queue + autocast; delay bucket reported separately, unknown timing masked',
 'no_fitting':True,'fresh_validation_51886_not_used':True,'files_before':before}
(out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
static=json.loads((dataset/'static.json').read_text());catalog={a['ability_id']:a for a in static['game_data']['abilities']}
with gzip.open(capture/'availability.jsonl.gz','rt') as f:legality={r['action_loop']:r for r in map(json.loads,f)}
start=time.monotonic();predictions=[];burst_rows=0
for row,state in teacher_states(dataset):
    record=legality[row['action_loop']];assert record['observation_loop']==state['game_loop']
    available={int(tag):set(entry['abilities']) for tag,entry in record['available'].items()}
    canonical=macro.evidence.get('coordinate_frame')=='base_toward_map_center'
    x,origin=global_features(state,macro.unit_types,macro.sizes['ability'],canonical=canonical,summarize=macro.evidence.get('entity_encoder')=='per_type_spatial_orders',semantics=macro.evidence.get('action_history_encoder')=='roles_targets_age',upgrade_count=macro.evidence.get('upgrade_count',0))
    output=macro.predict(x[None,:]);allowed=[0,*sorted(set().union(*available.values()))]
    assert max(allowed)<macro.sizes['ability']
    ability=int(allowed[int(output['ability'][0,allowed].argmax())])
    if ability!=int(output['ability'][0].argmax()):output=macro.predict(x[None,:],abilities=[ability])
    own=own_actors(state);group=[];actual=None;delay=None
    if ability:
        context=macro.command_context(x,ability)
        features=np.stack([actor_features(state,u,i,macro.unit_types,macro.sizes['ability'],origin,context) for i,u in enumerate(own)])
        group=select_actors(own,actors_policy.predict(features)['ability'],available,ability)
        if group:
            argument_x=group_features(state,group,macro.unit_types,macro.sizes['ability'],origin,context)
            output=replace_arguments(output,arguments.predict(argument_x[None,:]),coordinate_signs(state,origin) if canonical else [1.,1.])
            proxy=dict(group[0],position=[*origin,0.]);output['point']=output['point'][:,:2]
            commands,_=decode_commands(state,[proxy],output,{proxy['tag']:{ability}},catalog,macro.unit_types,state['map_size'],chosen_abilities=[ability])
            if commands:
                actual=commands[0].as_dict();actual['units']=[u['tag'] for u in group]
                delay=int(output['delay'][0].argmax())
    if len(row['commands'])>1:burst_rows+=1
    for truth in row['commands']:
        fields={name:bool(actual is not None and actual[name]==truth[name]) for name in ('ability','target_unit','queue','autocast')}
        fields['units']=bool(actual is not None and set(actual['units'])==set(truth['units']))
        fields['target_point']=bool(actual is not None and ((truth['target_point'] is None and actual['target_point'] is None) or (truth['target_point'] is not None and actual['target_point'] is not None and np.linalg.norm(np.asarray(truth['target_point'])-actual['target_point'])<=2)))
        gap=row.get('next_action_delay');timing=None if gap is None else delay==int(np.abs(DELAYS-gap).argmin())
        predictions.append({'action_loop':row['action_loop'],'teacher':truth,'predicted':actual,'fields_correct':fields,'complete_command':all(fields.values()),'delay_bucket_correct':timing})
assert hashes()==before
counts={field:sum(p['fields_correct'][field] for p in predictions) for field in predictions[0]['fields_correct']}
report=dict(contract,status='completed',commands=len(predictions),full_command_hits=sum(p['complete_command'] for p in predictions),field_hits=counts,burst_rows=burst_rows,
 timing_labeled=sum(p['delay_bucket_correct'] is not None for p in predictions),timing_hits=sum(p['delay_bucket_correct'] is True for p in predictions),predictions=predictions,files_after=hashes(),wall_seconds=time.monotonic()-start)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('predictions','files_before','files_after')}),flush=True)
