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
from src.learning.goal_first_train import fit_goal_first, mixed_history_examples, prediction_history_examples, retained_history_examples, teaching_support
from src.learning.teacher_states import teacher_states


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


root = Path('logs/roadmap')
output = root / 'professional-mixed-history-01'
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
previous_root = root / 'professional-retained-history-01'
previous_paths = [previous_root / n for n in ('policy.npz', 'report.json', 'comparison.json', 'verification.json', 'history-ablation.json')]
previous_verified = read(previous_root / 'verification.json')
assert previous_verified['status'] == 'verified_completed_failure'
assert sha(previous_root / 'policy.npz') == previous_verified['checkpoint_sha256']
assert sha(previous_root / 'report.json') == previous_verified['report_sha256']
assert sha(previous_root / 'comparison.json') == previous_verified['comparison_sha256']
bindings.update({str(p):sha(p) for p in previous_paths})
parent_report = read(previous_root / 'report.json')
previous_policy, _ = GoalFirstPolicy.load(previous_root / 'policy.npz')
sources = validate_datasets(teach, diagnostic, missing_fields=True)
started = time.monotonic()
games = {}
for directory in teach + diagnostic:
    original = collect([directory], configuration['vocabulary'], spatial=True, missing_fields=True)[0]
    products = construction_products(read(directory / 'static.json')['game_data'])
    games[directory.name] = retained_history_examples(original, teacher_states(directory), configuration['vocabulary'], products)
    oracle_predictions = [r['prediction'] for r in parent_report['commands'] if r['game'] == directory.name]
    assert json.loads(json.dumps([previous_policy.predict(x) for x, _, _, _ in games[directory.name]])) == oracle_predictions
    del original
    print(json.dumps(dict(stage='loaded', game=directory.name, commands=len(games[directory.name]))), flush=True)
del previous_policy
all_teaching = [e for p in teach for e in games[p.name]]
fitting = [(x, y) for x, y, _, _ in all_teaching if y is not None]
assert len(all_teaching) == 4513 and len(fitting) == 4510 and len(games['774']) == 292
policy, _ = GoalFirstPolicy.load(previous_root / 'policy.npz')
support = teaching_support(policy, fitting)
# Descriptive human teaching support only; preserve the parent's weights.
abilities = {a['ability_id']: a for a in read(teach[0] / 'static.json')['game_data']['abilities']}
macro_ids = {i for i, a in abilities.items() if any(k in a.get('friendly_name', '').upper() for k in ('BUILD ', 'TRAIN ', 'RESEARCH '))}
assert sum(command.ability in macro_ids for _, _, command, _ in games['774']) == 91
contract = dict(bindings=bindings, sources=sources, vocabulary=configuration['vocabulary'],
                dimensions=list(policy.dimensions), hidden=64, model_seed=8140, shuffle_seed=8143,
                epochs_max=50, optimizer_seconds_max=1200, batch_size=16, rate=.0003,
                runtime=dict(executable=sys.executable, torch=torch.__version__, numpy=np.__version__,
                             device='cpu', cpu_threads=2, cuda_initialized=False),
                support_counts={k:int(v.sum()) for k,v in support.items()},
                support_neutralized_again=False, parent_checkpoint_sha256=previous_verified['checkpoint_sha256'],
                history_schedule=dict(refresh_every_epochs=5, human_probability_first20=.5, human_probability_after20=0, seed_base=8150, seed_epoch_multiplier=100),
                baseline_teaching=baseline['teaching']['predicted'], baseline_diagnostic=baseline['validation']['predicted'],
                baseline_per_game=control['initial_per_game'],
                input_history='Teaching uses at most32causal mixed human/predicted commands according to history_schedule. Human-history evaluation uses retained human commands; own-history evaluation regenerates final-policy predictions from empty per-game history.',
                baseline_retained=parent_report['per_game'],
                baseline_own_history={k:v['predicted'] for k,v in parent_report['own_history'].items()},
                gates=dict(teaching_actors=2546, teaching_complete=1277, teaching_games=7,
                           diagnostic_actors=73, diagnostic_complete=24, diagnostic_target=62,
                           diagnostic_ability=170, diagnostic_macro_ability=20,
                           own_teaching_complete=1000, own_diagnostic_ability=170, own_diagnostic_actors=73,
                           own_diagnostic_target=62, own_diagnostic_complete=24, own_diagnostic_macro_ability=20),
                scope='Human replay supervised imitation initialized from the verified retained-history checkpoint with one fresh Adam optimizer. Mixed history refreshed from the current policy every5epochs; human next-command labels and world states unchanged. Reused774 diagnostic evaluated after fitting; reserved games untouched. No native games or RL.')
source_rows = {p.name:list(teacher_states(p)) for p in teach}
products_by_game = {p.name:construction_products(read(p / 'static.json')['game_data']) for p in teach}
training_refreshes = []
history_cache = None


def history_digest(examples):
    digest = hashlib.sha256()
    for inputs, label in examples:
        for array in (*inputs['encoder'], inputs['actor_mask'], inputs['target_mask'], inputs['point_features']):
            array = np.asarray(array)
            digest.update(str((array.dtype.str, array.shape)).encode())
            digest.update(array.tobytes())
        digest.update(repr(label).encode())
    return digest.hexdigest()


def refresh_examples(current_policy, epoch, deadline):
    global history_cache
    if time.monotonic() >= deadline:
        raise TimeoutError('History refresh deadline')
    if epoch % 5 == 0:
        assert not current_policy.training and not torch.is_grad_enabled()
        refresh_started = time.monotonic()
        probability = .5 if epoch < 20 else 0
        snapshot = output / f'refresh-{epoch + 1}.npz'
        if output.exists():
            current_policy.save(snapshot, dict(epoch=epoch + 1, contract_sha256=sha(output / 'contract.json')))
        refreshed = []
        for game_index, directory in enumerate(teach):
            rebuilt = mixed_history_examples(current_policy, games[directory.name], source_rows[directory.name],
                configuration['vocabulary'], products_by_game[directory.name],
                human_probability=probability, seed=8150 + epoch * 100 + game_index, deadline=deadline)
            refreshed.extend((x, y) for x, y, _, _ in rebuilt if y is not None)
        assert len(refreshed) == 4510
        if time.monotonic() >= deadline:
            raise TimeoutError('History refresh deadline')
        history_cache = refreshed
        record = dict(epoch=epoch + 1, human_probability=probability, samples=len(refreshed),
            seconds=time.monotonic()-refresh_started, examples_sha256=history_digest(refreshed),
            snapshot_sha256=sha(snapshot) if snapshot.exists() else None)
        training_refreshes.append(record)
        print(json.dumps(dict(stage='history_refreshed', **record)), flush=True)
    return history_cache


if os.environ.get('SC2_IMITATION_PREFLIGHT_ONLY') == '1':
    policy.eval()
    with torch.no_grad():
        preview = refresh_examples(policy, 0, time.monotonic()+120)
    assert len(preview) == 4510 and not output.exists()
    assert sha(previous_root / 'policy.npz') == previous_verified['checkpoint_sha256']
    assert not torch.cuda.is_initialized()
    for path, digest in bindings.items():
        assert sha(path) == digest
    receipt = root / 'professional-mixed-history-01.preflight.json'
    assert not receipt.exists()
    write(receipt, dict(status='preflight_passed_no_fit', bindings=bindings, sources=sources,
        parent_checkpoint_sha256=previous_verified['checkpoint_sha256'], training_refresh=training_refreshes,
        teaching_commands=4513, fitting_samples=4510, diagnostic_commands=292, schedule=contract['history_schedule'],
        optimizer_updates=0, native_games=0, rl_updates=0))
    print(json.dumps(dict(status='preflight_passed_no_fit', receipt=str(receipt), sha256=sha(receipt))), flush=True)
    sys.exit(0)

output.mkdir()
np.savez_compressed(output / 'teaching-support.npz', **support)
contract['support_archive_sha256'] = sha(output / 'teaching-support.npz')
write(output / 'contract.json', contract)
policy.save(output / 'initial.npz', dict(contract_sha256=sha(output / 'contract.json'), stage='initial'))
print(json.dumps(dict(stage='preflight_passed', parameters=sum(p.numel() for p in policy.parameters()), contract_sha256=sha(output / 'contract.json'))), flush=True)
report = fit_goal_first(policy, fitting, epochs=50, batch_size=16, rate=.0003, seconds=1200, seed=8143, refresh_examples=refresh_examples)
report['training_refreshes'] = training_refreshes
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
