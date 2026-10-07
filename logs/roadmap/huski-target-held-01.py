"""Use the original comparison helpers unchanged on the fresh Huski game."""
import ast
import hashlib
import json
from pathlib import Path
import numpy as np
from src.learning.imitation import FactorPolicy
from src.learning.global_imitation import global_features, coordinate_signs
from src.learning.actor_selection import group_features
from src.learning.imitation_play import decode_commands, replace_arguments
from src.learning.target_selection import target_features
from src.learning.teacher_states import teacher_states, own_actors

root=Path('logs/roadmap')
contract=json.loads((root/'huski-target-held-01-contract.json').read_text())
for component in contract['models'].values():
    assert hashlib.sha256(Path(component['path']).read_bytes()).hexdigest()==component['sha256']
macro=FactorPolicy.load(contract['models']['macro']['path'])
arguments=FactorPolicy.load(contract['models']['arguments']['path'])
pointer=FactorPolicy.load(contract['models']['target']['path'])
source=root/'target-human-fit-01.py'
tree=ast.parse(source.read_text())
helpers=ast.Module(body=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ['collect','audit']],type_ignores=[])
exec(compile(helpers,str(source),'exec'))
x,_,_,groups,sources,missing=collect(['51960-p1'])
result=audit(pointer,x,groups)
coverage={}
target_alliances=[]
for row,state in teacher_states(root/'issued-51960-p1'):
    units={u['tag']:u for u in state['units']}
    for c in row['commands']:
        if c['target_unit'] is not None and not c['autocast'] and c['target_unit'] in units:
            target_alliances.append(units[c['target_unit']]['alliance'])
        if c['ability']==23:
            alliance=units.get(c['target_unit'],{}).get('alliance','point_or_unseen')
            coverage[str(alliance)]=coverage.get(str(alliance),0)+1
h=result['models']
assert len(target_alliances)==len(groups)
enemy=[g for g,a in zip(groups,target_alliances) if a==4]
attack=[g for g in enemy if g['ability']==23]
report=dict(contract,status='completed',sources=sources,unavailable_targets=missing,held=result,
            enemy_held=audit(pointer,x,enemy),attack_enemy_held=audit(pointer,x,attack),
            attack_target_alliance_coverage=coverage,comparison_helper_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            gate_passed=h['pointer']['exact_target_accuracy']>h['arguments']['exact_target_accuracy'] and h['pointer']['mean_target_error_tiles']<h['arguments']['mean_target_error_tiles'])
with (root/'huski-target-held-01-with-strata.json').open('x') as stream:json.dump(report,stream,indent=2)
print(json.dumps({'held':result,'attack_enemy':report['attack_enemy_held'],'attack_coverage':coverage,'gate_passed':report['gate_passed']}))
