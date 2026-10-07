"""Read-only player-visible context of frozen small-set actor mismatches."""
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np

from src.learning.entity_audit import audit_commands
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect
from src.learning.teacher_states import teacher_states

root=Path('logs/roadmap/professional-small-set-01')
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
contract=read(root/'contract.json')
report=read(root/'report.json')
assert sha(root/'policy.npz')==report['checkpoint_sha256']
assert sha(root/'contract.json')==report['contract_sha256']
configuration_path=Path('logs/roadmap/joint-professional-fit-05/configuration.json')
assert sha(configuration_path)==contract['parent_configuration_sha256']
configuration=read(configuration_path)
for p,h in contract['code_sha256'].items():assert sha(Path(p))==h
selected_by_game={}
for selected in contract['selected']:
    selected_by_game.setdefault(selected['game'],{})[selected['row']]=selected
policy,_=JointEntityPolicy.load(root/'policy.npz')
chosen=[]
failures=[]
counts=Counter()
for source in contract['sources']:
    directory=Path(source['dataset'])
    assert directory.name not in ('774','848','51483','51886')
    for p,h in source['bindings'].items():assert sha(Path(p))==h
    static=read(directory/'static.json')['game_data']
    names={a['ability_id']:a.get('friendly_name','') for a in static['abilities']}
    examples,_=collect([directory],configuration['vocabulary'],spatial=True,missing_fields=True)
    for index,(raw,state) in enumerate(teacher_states(directory)):
        if index not in selected_by_game.get(directory.name,{}):continue
        assert len(raw['commands'])==1 and state.get('history_quality')=='event_slots'
        inputs,label,command,reason=examples[index]
        assert command.ability==selected_by_game[directory.name][index]['ability']
        chosen.append(examples[index])
        predicted=policy.predict(inputs)
        if set(predicted['actors'])==set(label['actors']):continue
        units={u['tag']:u for u in state['units']+state['owned_memory']}
        human=[inputs['tags'][i] for i in label['actors']]
        alternate=[inputs['tags'][i] for i in predicted['actors']]
        target=command.target_point
        if command.target_unit is not None:
            target_unit=next((u for u in state['units'] if u['tag']==command.target_unit and u.get('display_type',1)==1),None)
            target=target_unit['position'][:2] if target_unit else None
        def describe(tag):
            u=units[tag]
            observed=tag in {v['tag'] for v in state['units']} and u.get('observed',True) and u.get('display_type',1)==1
            return dict(type=u['unit_type'],observed=observed,position=u['position'][:2],
                        build_progress=u.get('build_progress') if observed else None,
                        first_order=u.get('orders',[])[:1] if observed else None,
                        euclidean_target_distance=float(np.linalg.norm(np.asarray(u['position'][:2])-target)) if target is not None else None)
        entry=dict(game=directory.name,row=index,ability=command.ability,name=names[command.ability],
                   human=[describe(tag) for tag in human],alternate=[describe(tag) for tag in alternate],
                   target=target,unknown_unit_fields=state.get('unknown_fields',{}).get('units',[]))
        if len(human)==len(alternate)==1:
            same_type=entry['human'][0]['type']==entry['alternate'][0]['type']
            counts['single_same_type']+=same_type
            if target is not None:
                delta=entry['alternate'][0]['euclidean_target_distance']-entry['human'][0]['euclidean_target_distance']
                entry['distance_delta']=delta
                counts['single_actor_target_comparisons']+=1
                counts['alternate_farther_than_two_tiles']+=delta>2
                counts['alternate_closer_than_two_tiles']+=delta < -2
            counts['single_actor_different_first_order']+=entry['human'][0]['first_order']!=entry['alternate'][0]['first_order']
        failures.append(entry)
audit=audit_commands(policy,chosen)
assert len(chosen)==report['commands']==62
for key,value in audit.items():
    if key!='point_errors':assert value==report['final'][key],(key,value,report['final'][key])
mean_differences={}
for name,value in audit['point_errors'].items():
    expected=report['final']['point_errors'][name]
    assert value['count']==expected['count']
    difference=abs(value['mean']-expected['mean'])
    assert difference<1e-10,(name,value,expected)
    mean_differences[name]=difference
receipt=dict(checkpoint_sha256=sha(root/'policy.npz'),contract_sha256=sha(root/'contract.json'),
             helper_sha256=sha(Path(__file__)),counts=dict(counts),failures=failures,
             audit_point_mean_differences=mean_differences,
             scope='Selected human teaching states only; no hidden/future data, optimizer or other replay predictions. Euclidean distance is not path length or legal execution. Exact source-engine ability availability is unavailable; no equivalence/promotion claim.')
path=root/'actor-context.json'
assert not path.exists()
path.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
