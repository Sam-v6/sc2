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

root = Path('logs/roadmap')
out = root / 'command-stage-diagnosis-rom-01'
out.mkdir(exist_ok=False)
dataset = root / 'issued-51482-rom-masked-01'
capture = root / 'replay-legality-rom-04'
paths = [root / 'imitation-prefix-240-01/policy.npz', root / 'actor-prefix-240-01/actors.npz', root / 'arguments-prefix-240-01/arguments.npz']
macro, actors, arguments = [FactorPolicy.load(p) for p in paths]
files = [Path(__file__), *paths, *(dataset / n for n in ('dataset.json', 'static.json', 'examples.jsonl.gz')), *(capture / n for n in ('contract.json', 'report.json', 'availability.jsonl.gz')), root / 'full-command-audit-rom-01/report.json', *sorted(Path('src/learning').glob('*.py'))]
def hashes():
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before = hashes()
static = json.loads((dataset / 'static.json').read_text())
catalog = {a['ability_id']: a for a in static['game_data']['abilities']}
with gzip.open(capture / 'availability.jsonl.gz', 'rt') as f:
    masks = {r['action_loop']: r for r in map(json.loads, f)}
prior = json.loads((root / 'full-command-audit-rom-01/report.json').read_text())['predictions']
records = []
start = time.monotonic()
for row, state in teacher_states(dataset):
    available = {int(tag): set(entry['abilities']) for tag, entry in masks[row['action_loop']]['available'].items()}
    canonical = macro.evidence.get('coordinate_frame') == 'base_toward_map_center'
    x, origin = global_features(state, macro.unit_types, macro.sizes['ability'], canonical=canonical, summarize=macro.evidence.get('entity_encoder') == 'per_type_spatial_orders', semantics=macro.evidence.get('action_history_encoder') == 'roles_targets_age', upgrade_count=macro.evidence.get('upgrade_count', 0))
    own = own_actors(state)
    by_tag = {u['tag']: u for u in own}
    for truth in row['commands']:
        result = {'action_loop': row['action_loop'], 'teacher': truth, 'teacher_ability_available_for_all_actors': all(truth['ability'] in available.get(tag, set()) for tag in truth['units']), 'stages': {}}
        for stage in ('joint', 'teacher_ability', 'teacher_ability_and_group'):
            output = macro.predict(x[None, :])
            allowed = [0, *sorted(set().union(*available.values()))]
            ability = int(allowed[int(output['ability'][0, allowed].argmax())]) if stage == 'joint' else truth['ability']
            if ability != int(output['ability'][0].argmax()):
                output = macro.predict(x[None, :], abilities=[ability])
            actual = None
            if ability:
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
assert len(records) == len(prior)
for record, old in zip(records, prior):
    assert record['action_loop'] == old['action_loop'] and record['teacher'] == old['teacher']
    assert record['stages']['joint']['predicted'] == old['predicted']
    assert record['stages']['joint']['fields_correct'] == old['fields_correct']
summaries = {}
for stage in records[0]['stages']:
    predictions = [r['stages'][stage] for r in records]
    points = [(r, p) for r, p in zip(records, predictions) if r['teacher']['target_point'] is not None]
    units = [(r, p) for r, p in zip(records, predictions) if r['teacher']['target_unit'] is not None]
    summaries[stage] = {'complete_hits': sum(p['complete_command'] for p in predictions), 'field_hits': {name: sum(p['fields_correct'][name] for p in predictions) for name in predictions[0]['fields_correct']}, 'point_commands': len(points), 'point_hits': sum(p['fields_correct']['target_point'] for _, p in points), 'point_predictions_present': sum(p['point_error'] is not None for _, p in points), 'mean_point_error_when_present': float(np.mean([p['point_error'] for _, p in points if p['point_error'] is not None])), 'unit_target_commands': len(units), 'unit_target_hits': sum(p['fields_correct']['target_unit'] for _, p in units)}
assert hashes() == before
report = {'status': 'completed', 'scope': 'Frozen heads at human command times and teacher history; teacher ability/group interventions are oracle diagnostics, not autonomous competence. No spatial placement or execution checks. No fitting; reserved 51886 untouched.', 'commands': len(records), 'teacher_native_unavailable_commands': sum(not r['teacher_ability_available_for_all_actors'] for r in records), 'joint_reproduces_previous_audit': True, 'stages': summaries, 'records': records, 'files_before': before, 'files_after': hashes(), 'wall_seconds': time.monotonic() - start}
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k not in ('records', 'files_before', 'files_after')}, indent=2))
