"""Diagnose frozen command heads with explicit teacher-field interventions."""
import gzip
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from src.learning.imitation import FactorPolicy
from src.learning.teacher_states import teacher_states, own_actors
from src.learning.global_imitation import global_features, coordinate_signs
from src.learning.actor_selection import actor_features, select_actors, group_features
from src.learning.imitation_play import decode_commands, replace_arguments

root=Path('logs/roadmap');out=root/'command-stage-consistent-fullgame-01';out.mkdir(exist_ok=False)
ids=[51574,51573,51958,51890,51891]
paths=[root/'consistent-fullgame-01/macro/policy.npz',root/'consistent-fullgame-01/actors/actors.npz',root/'consistent-fullgame-01/arguments/arguments.npz']
macro,actors,arguments=[FactorPolicy.load(p) for p in paths]
dirs={i:root/'issued-timing-masked-01'/f'issued-{i}' for i in ids}
files=[Path(__file__),*paths,*sorted(Path('src/learning').glob('*.py')),*[directory/name for directory in dirs.values() for name in ('dataset.json','static.json','examples.jsonl.gz')]]
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=hashes();start=time.monotonic();records=[]
contract={'scope':'unmasked component reconstruction on teaching games, human event times/history; correct-ability/group interventions are oracle diagnostics; no native availability, no placement, no autonomous play or fitting', 'models':[str(p) for p in paths], 'train_sources':ids,'cutoff_game_seconds':240,'reserved_51886_unused':True,'decision':'If joint teaching reconstruction is poor, stop transfer sweeps and repair failing training/component contract; if only transfer is poor, widen independent-player teaching. Do not promote from reconstruction alone.','files_before':before}
(out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
for replay in ids:
    dataset=dirs[replay];static=json.loads((dataset/'static.json').read_text());catalog={a['ability_id']:a for a in static['game_data']['abilities']}
    for row, state in teacher_states(dataset):
        available = {unit['tag']: set(catalog) for unit in own_actors(state)}
        canonical = macro.evidence.get('coordinate_frame') == 'base_toward_map_center'
        x, origin = global_features(state, macro.unit_types, macro.sizes['ability'], canonical=canonical, summarize=macro.evidence.get('entity_encoder') == 'per_type_spatial_orders', semantics=macro.evidence.get('action_history_encoder') == 'roles_targets_age', upgrade_count=macro.evidence.get('upgrade_count', 0))
        own = own_actors(state)
        by_tag = {u['tag']: u for u in own}
        for truth in row['commands']:
            result = {'action_loop': row['action_loop'], 'teacher': truth, 'replay': replay, 'period': 'prefix_240' if row['action_loop'] <= 240*22.4 else 'after_240', 'stages': {}}
            for stage in ('joint', 'teacher_ability', 'teacher_ability_and_group'):
                output = macro.predict(x[None, :])
                allowed = [0, *sorted(set().union(*available.values()))]
                ability = int(output['ability'][0].argmax()) if stage == 'joint' else truth['ability']
                if ability != int(output['ability'][0].argmax()):
                    output = macro.predict(x[None, :], abilities=[ability])
                actual = None
                if ability and ability in catalog:
                    context = macro.command_context(x, ability)
                    features = np.stack([actor_features(state, u, i, macro.unit_types, macro.sizes['ability'], origin, context) for i, u in enumerate(own)])
                    group = select_actors(own, actors.predict(features)['ability'], available, ability)
                    if stage == 'teacher_ability_and_group':
                        group = [by_tag[tag] for tag in truth['units']]
                    if group:
                        arg_x = group_features(state, group, macro.unit_types, macro.sizes['ability'], origin, context)
                        output = replace_arguments(output, arguments.predict(arg_x[None, :]), coordinate_signs(state, origin) if canonical else [1., 1.])
                        proxy = dict(group[0], position=[*origin, 0.])
                        output['point'] = output['point'][:, :2]
                        commands, _ = decode_commands(state, [proxy], output, {proxy['tag']: {ability}}, catalog, macro.unit_types, state['map_size'], chosen_abilities=[ability])
                        if commands:
                            actual = commands[0].as_dict()
                            actual['units'] = [u['tag'] for u in group]
                fields = {name: bool(actual is not None and actual[name] == truth[name]) for name in ('ability', 'target_unit', 'queue', 'autocast')}
                fields['units'] = bool(actual is not None and set(actual['units']) == set(truth['units']))
                point_error = None
                if truth['target_point'] is not None and actual is not None and actual['target_point'] is not None:
                    point_error = float(np.linalg.norm(np.asarray(truth['target_point']) - actual['target_point']))
                fields['target_point'] = bool(actual is not None and ((truth['target_point'] is None and actual['target_point'] is None) or (point_error is not None and point_error <= 2)))
                result['stages'][stage] = {'predicted': actual, 'fields_correct': fields, 'complete_command': all(fields.values()), 'point_error': point_error}
            records.append(result)

def summarize(rows):
    summary={'commands':len(rows),'stages':{}}
    for stage in ('joint','teacher_ability','teacher_ability_and_group'):
        summary['stages'][stage]={
            'complete_hits':sum(r['stages'][stage]['complete_command'] for r in rows),
            'ability_hits':sum(r['stages'][stage]['fields_correct']['ability'] for r in rows),
            'actor_set_hits':sum(r['stages'][stage]['fields_correct']['units'] for r in rows),
            'point_commands':sum(r['teacher']['target_point'] is not None for r in rows),
            'point_hits':sum(r['stages'][stage]['fields_correct']['target_point'] for r in rows if r['teacher']['target_point'] is not None),
            'unit_target_commands':sum(r['teacher']['target_unit'] is not None for r in rows),
            'unit_target_hits':sum(r['stages'][stage]['fields_correct']['target_unit'] for r in rows if r['teacher']['target_unit'] is not None)}
    return summary
results={str(i):{period:summarize([r for r in records if r['replay']==i and r['period']==period]) for period in ('prefix_240','after_240')} for i in ids}
aggregate={period:summarize([r for r in records if r['period']==period]) for period in ('prefix_240','after_240')}
assert hashes()==before
report=dict(contract,status='completed',results=results,aggregate=aggregate,records=records,files_after=hashes(),wall_seconds=time.monotonic()-start)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'aggregate':aggregate,'wall_seconds':report['wall_seconds']},indent=2))
