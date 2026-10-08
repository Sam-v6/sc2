"""One frozen, CPU-only professional human imitation experiment."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch

from src.learning.actor_selection import construction_products
from src.learning.entity_audit import audit_commands
from src.learning.entity_examples import decode_command
from src.learning.entity_train import DELAYS, collect, validate_datasets
from src.learning.goal_first_policy import GoalFirstPolicy
from src.learning.goal_first_train import fit_goal_first, prediction_history_examples, retained_history_examples, teaching_support
from src.learning.teacher_states import teacher_states


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


root = Path('logs/roadmap')
output = root / 'professional-retained-history-01'
assert not output.exists()
assert os.environ['CUDA_VISIBLE_DEVICES'] == ''
assert os.environ['OPENBLAS_NUM_THREADS'] == os.environ['OMP_NUM_THREADS'] == '2'
torch.set_num_threads(2)
torch.set_num_interop_threads(2)
assert not torch.cuda.is_initialized()
configuration_path = root / 'joint-professional-fit-05/configuration.json'
configuration = read(configuration_path)
baseline_path = root / 'joint-professional-fit-05/report.json'
baseline = read(baseline_path)
assert sha(baseline_path.parent / 'policy.npz') == baseline['checkpoint_sha256']
control_path = root / 'professional-context-query-01/contract.json'
control = read(control_path)
control_comparison_path = control_path.parent / 'comparison.json'
assert sha(control_path) == read(control_comparison_path)['contract_sha256']
teach = [Path(s['dataset']) for s in configuration['sources'] if s['role'] == 'teaching']
diagnostic = [Path(s['dataset']) for s in configuration['sources'] if s['role'] == 'diagnostic']
assert len(teach) == 9 and [p.name for p in diagnostic] == ['774']
assert not any(p.name in ('848', '51483', '51886') for p in teach + diagnostic)
bindings = {str(configuration_path): sha(configuration_path), str(baseline_path): sha(baseline_path),
            str(control_path): sha(control_path), str(control_comparison_path): sha(control_comparison_path),
            str(baseline_path.parent / 'policy.npz'): baseline['checkpoint_sha256']}
for source in configuration['sources']:
    bindings.update(source['bindings'])
code = [*configuration['code_before'], 'src/learning/goal_first_policy.py',
        'src/learning/goal_first_train.py', __file__, os.environ['SC2_IMITATION_WATCHDOG']]
bindings.update({str(p): sha(p) for p in code})
for path, digest in bindings.items():
    assert sha(path) == digest
previous_root = root / 'professional-goal-first-01'
previous_paths = [previous_root / n for n in ('policy.npz', 'report.json', 'comparison.json', 'verification.json', 'retained-history-oracle.json')]
previous_verified = read(previous_root / 'verification.json')
assert previous_verified['status'] == 'verified_completed_failure'
assert sha(previous_root / 'policy.npz') == previous_verified['checkpoint_sha256']
assert sha(previous_root / 'report.json') == previous_verified['report_sha256']
assert sha(previous_root / 'comparison.json') == previous_verified['comparison_sha256']
bindings.update({str(p):sha(p) for p in previous_paths})
retained_oracle = read(previous_root / 'retained-history-oracle.json')
assert retained_oracle['checkpoint_sha256'] == previous_verified['checkpoint_sha256']
assert retained_oracle['report_sha256'] == previous_verified['report_sha256']
previous_policy, _ = GoalFirstPolicy.load(previous_root / 'policy.npz')
sources = validate_datasets(teach, diagnostic, missing_fields=True)
started = time.monotonic()
games = {}
for directory in teach + diagnostic:
    original = collect([directory], configuration['vocabulary'], spatial=True, missing_fields=True)[0]
    products = construction_products(read(directory / 'static.json')['game_data'])
    games[directory.name] = retained_history_examples(original, teacher_states(directory), configuration['vocabulary'], products)
    oracle_predictions = [r['prediction'] for r in retained_oracle['games'][directory.name]['records']]
    assert json.loads(json.dumps([previous_policy.predict(x) for x, _, _, _ in games[directory.name]])) == oracle_predictions
    del original
    print(json.dumps(dict(stage='loaded', game=directory.name, commands=len(games[directory.name]))), flush=True)
del previous_policy
all_teaching = [e for p in teach for e in games[p.name]]
fitting = [(x, y) for x, y, _, _ in all_teaching if y is not None]
assert len(all_teaching) == 4513 and len(fitting) == 4510 and len(games['774']) == 292
policy = GoalFirstPolicy((188, 618, 9, 1970, 3801, 401), DELAYS, hidden=64, seed=8140)
support = teaching_support(policy, fitting)
# Check supervised score parity on a deterministic teaching sample. Clearing
# unused input weights does not claim parity for untaught predicted abilities.
parity_rows = fitting[::100]
before = [{k: v.detach().numpy().copy() for k, v in policy._forward(x, y)[0].items() if v is not None} for x, y in parity_rows]
policy.clear_unseen_inputs(support)
for (x, y), old in zip(parity_rows, before, strict=True):
    for key, value in policy._forward(x, y)[0].items():
        if value is not None:
            np.testing.assert_array_equal(value.detach().numpy(), old[key])
del before
abilities = {a['ability_id']: a for a in read(teach[0] / 'static.json')['game_data']['abilities']}
macro_ids = {i for i, a in abilities.items() if any(k in a.get('friendly_name', '').upper() for k in ('BUILD ', 'TRAIN ', 'RESEARCH '))}
assert sum(command.ability in macro_ids for _, _, command, _ in games['774']) == 91
contract = dict(bindings=bindings, sources=sources, vocabulary=configuration['vocabulary'],
                dimensions=list(policy.dimensions), hidden=64, model_seed=8140, shuffle_seed=8142,
                epochs_max=100, optimizer_seconds_max=1800, batch_size=16, rate=.001,
                runtime=dict(executable=sys.executable, torch=torch.__version__, numpy=np.__version__,
                             device='cpu', cpu_threads=2, cuda_initialized=False),
                support_counts={k:int(v.sum()) for k,v in support.items()},
                supervised_support_parity_rows=len(parity_rows),
                baseline_teaching=baseline['teaching']['predicted'], baseline_diagnostic=baseline['validation']['predicted'],
                baseline_per_game=control['initial_per_game'],
                input_history='At most32previous retained human commands, appended after current inputs; no unresolved original event slots',
                baseline_retained={k:v['audit']['predicted'] for k,v in retained_oracle['games'].items()},
                baseline_own_history={k:v['prediction_history'] for k,v in retained_oracle['games'].items()},
                gates=dict(teaching_actors=2546, teaching_complete=1277, teaching_games=7,
                           diagnostic_actors=73, diagnostic_complete=24, diagnostic_target=62,
                           diagnostic_ability=170, diagnostic_macro_ability=20,
                           own_teaching_complete=1000, own_diagnostic_ability=170, own_diagnostic_actors=73,
                           own_diagnostic_target=62, own_diagnostic_complete=24, own_diagnostic_macro_ability=20),
                scope='Representation-only human replay supervised fit, unchanged controller/loss/optimizer. Past retained human command history used for teaching. Reused774 diagnostic evaluated after fitting; reserved games untouched. Own-history tests retain human states and decision times; hypothetical commands, no native games or RL.')
output.mkdir()
np.savez_compressed(output / 'teaching-support.npz', **support)
contract['support_archive_sha256'] = sha(output / 'teaching-support.npz')
write(output / 'contract.json', contract)
policy.save(output / 'initial.npz', dict(contract_sha256=sha(output / 'contract.json'), stage='initial'))
print(json.dumps(dict(stage='preflight_passed', parameters=sum(p.numel() for p in policy.parameters()), contract_sha256=sha(output / 'contract.json'))), flush=True)
report = fit_goal_first(policy, fitting, epochs=100, batch_size=16, rate=.001, seconds=1800, seed=8142)
write(output / 'fit.json', report)
print(json.dumps(dict(stage='fit_finished', **{k:v for k,v in report.items() if k != 'history'})), flush=True)
policy.save(output / 'policy.npz', dict(contract_sha256=sha(output / 'contract.json'), status=report['status']))
loaded, _ = GoalFirstPolicy.load(output / 'policy.npz')
report.update(checkpoint_sha256=sha(output / 'policy.npz'), teaching=audit_commands(policy, all_teaching),
              diagnostic=audit_commands(policy, games['774']), per_game={}, families={}, own_history={})
commands = []
for directory in teach + diagnostic:
    game = directory.name
    examples = games[game]
    report['per_game'][game] = audit_commands(policy, examples)['predicted']
    families = {}
    for index, (x, _, command, reason) in enumerate(examples):
        prediction = policy.predict(x)
        assert prediction == loaded.predict(x)
        decode_command(prediction, x)
        commands.append(dict(game=game, row=index, prediction=prediction, command=command.as_dict(), exclusion=reason))
        name = abilities[command.ability].get('friendly_name', abilities[command.ability]['link_name'])
        families.setdefault(name, []).append(examples[index])
    report['families'][game] = {name:audit_commands(policy, rows) for name, rows in families.items()}
    products = construction_products(read(directory / 'static.json')['game_data'])
    rebuilt, records = prediction_history_examples(policy, examples, teacher_states(directory), configuration['vocabulary'], products)
    for (x, _, _, _), record in zip(rebuilt, records, strict=True):
        assert loaded.predict(x) == record['prediction']
    report['own_history'][game] = audit_commands(policy, rebuilt)
    write(output / f'{game}-own-history.json', records)
    del rebuilt, records
    print(json.dumps(dict(stage='evaluated', game=game, predicted=report['per_game'][game], own_history=report['own_history'][game]['predicted'])), flush=True)
report.update(commands=commands, reloaded_predictions_match=True, native_games=0, rl_updates=0)
write(output / 'report.json', report)
for path, digest in bindings.items():
    assert sha(path) == digest
assert validate_datasets(teach, diagnostic, missing_fields=True) == sources
assert sha(output / 'teaching-support.npz') == contract['support_archive_sha256']
assert not torch.cuda.is_initialized()
t, d, g = report['teaching']['predicted'], report['diagnostic']['predicted'], contract['gates']
improved = sum(report['per_game'][p.name]['complete'] > contract['baseline_per_game'][p.name]['complete'] for p in teach)
macro_correct = sum(row['command']['ability'] in macro_ids and row['prediction']['ability'] == row['command']['ability'] for row in commands if row['game'] == '774')
gates = dict(teaching_actors=t['actors'] >= g['teaching_actors'], teaching_complete=t['complete'] >= g['teaching_complete'],
             teaching_games=improved >= g['teaching_games'], diagnostic_actors=d['actors'] >= g['diagnostic_actors'],
             diagnostic_complete=d['complete'] >= g['diagnostic_complete'], diagnostic_target=d['target'] >= g['diagnostic_target'],
             diagnostic_ability=d['ability'] >= g['diagnostic_ability'], diagnostic_macro_ability=macro_correct >= g['diagnostic_macro_ability'])
own_teaching_complete = sum(report['own_history'][p.name]['predicted']['complete'] for p in teach)
own_diagnostic = report['own_history']['774']['predicted']
own_records = read(output / '774-own-history.json')
diagnostic_commands = [r for r in commands if r['game'] == '774']
own_macro_correct = sum(r['command']['ability'] in macro_ids and o['prediction']['ability'] == r['command']['ability'] for r, o in zip(diagnostic_commands, own_records, strict=True))
gates.update(own_teaching_complete=own_teaching_complete >= g['own_teaching_complete'],
             own_diagnostic_ability=own_diagnostic['ability'] >= g['own_diagnostic_ability'],
             own_diagnostic_actors=own_diagnostic['actors'] >= g['own_diagnostic_actors'],
             own_diagnostic_target=own_diagnostic['target'] >= g['own_diagnostic_target'],
             own_diagnostic_complete=own_diagnostic['complete'] >= g['own_diagnostic_complete'],
             own_diagnostic_macro_ability=own_macro_correct >= g['own_diagnostic_macro_ability'])
comparison = dict(status='completed', fit_status=report['status'], gates=gates, all_gates_passed=all(gates.values()),
                  teaching_games_improved=improved, diagnostic_macro_ability=macro_correct, diagnostic_macro_rows=91,
                  own_teaching_complete=own_teaching_complete, own_diagnostic=own_diagnostic, own_diagnostic_macro_ability=own_macro_correct,
                  contract_sha256=sha(output / 'contract.json'), report_sha256=sha(output / 'report.json'),
                  fit_sha256=sha(output / 'fit.json'), support_archive_sha256=contract['support_archive_sha256'],
                  checkpoint_sha256=report['checkpoint_sha256'], elapsed_seconds=time.monotonic()-started,
                  bindings_unchanged=True, promoted=False, native_games=0, rl_updates=0)
write(output / 'comparison.json', comparison)
print(json.dumps(comparison), flush=True)
