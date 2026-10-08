"""Independent terminal artifact and replay prediction check; never fits."""
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from src.learning.actor_selection import construction_products
from src.learning.entity_audit import audit_commands
from src.learning.entity_train import collect, validate_datasets
from src.learning.goal_first_policy import GoalFirstPolicy
from src.learning.goal_first_train import mixed_history_examples, prediction_history_examples, retained_history_examples, teaching_support
from src.learning.teacher_states import teacher_states


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def json_value(value):
    return json.loads(json.dumps(value))


torch.set_num_threads(2)
torch.set_num_interop_threads(2)
output = Path('logs/roadmap/professional-mixed-history-01')
telemetry_path = output.parent / 'professional-mixed-history-01.telemetry.json'
telemetry = read(telemetry_path)
assert telemetry['status'] == 'completed' and telemetry['returncode'] == 0 and telemetry['stop_reason'] is None
contract, comparison, report, fit = [read(output / name) for name in ('contract.json', 'comparison.json', 'report.json', 'fit.json')]
assert comparison['status'] == 'completed' and comparison['bindings_unchanged'] and report['reloaded_predictions_match']
for path, digest in contract['bindings'].items():
    assert sha(path) == digest
for name, key in (('contract.json', 'contract_sha256'), ('report.json', 'report_sha256'),
                  ('policy.npz', 'checkpoint_sha256'), ('fit.json', 'fit_sha256'), ('teaching-support.npz', 'support_archive_sha256')):
    assert sha(output / name) == comparison[key]
assert comparison['support_archive_sha256'] == contract['support_archive_sha256']
for name in ('script', 'watchdog'):
    matches = [path for path, digest in contract['bindings'].items() if digest == telemetry[name + '_sha256']]
    assert len(matches) == 1
assert fit['epochs_completed'] <= 50 and fit['status'] in ('completed', 'wall_bound')
assert fit['optimizer_seconds'] <= 1210  # cooperative bound plus final finite checks
assert fit['presentations'] <= 4510 * 50 and fit['updates'] <= 282 * 50
for key, value in fit.items():
    assert report[key] == value
policy, metadata = GoalFirstPolicy.load(output / 'policy.npz')
assert metadata['contract_sha256'] == comparison['contract_sha256']
assert all(p.device.type == 'cpu' for p in policy.parameters()) and not torch.cuda.is_initialized()
with np.load(output / 'teaching-support.npz', allow_pickle=False) as archive:
    support = {k: archive[k].copy() for k in archive.files}
assert {k: int(v.sum()) for k, v in support.items()} == contract['support_counts']
reconstructed_support = {k: np.zeros_like(v) for k, v in support.items()}
teach = [Path(s['dataset']) for s in contract['sources'] if s['role'] == 'teaching']
diagnostic = [Path(s['dataset']) for s in contract['sources'] if s['role'] == 'diagnostic']
assert len(teach) == 9 and [p.name for p in diagnostic] == ['774']
assert not any(p.name in ('848', '51483', '51886') for p in teach + diagnostic)
assert validate_datasets(teach, diagnostic, missing_fields=True) == contract['sources']
assert contract['epochs_max'] == 50 and contract['optimizer_seconds_max'] == 1200
assert contract['batch_size'] == 16 and contract['rate'] == .0003 and contract['shuffle_seed'] == 8143
assert contract['history_schedule'] == dict(refresh_every_epochs=5, human_probability_first20=.5,
    human_probability_after20=0, seed_base=8150, seed_epoch_multiplier=100)
assert contract['support_neutralized_again'] is False
parent = output.parent / 'professional-retained-history-01'
parent_verified = read(parent / 'verification.json')
assert sha(parent / 'policy.npz') == contract['parent_checkpoint_sha256'] == parent_verified['checkpoint_sha256']
initial, initial_meta = GoalFirstPolicy.load(output / 'initial.npz')
parent_policy, _ = GoalFirstPolicy.load(parent / 'policy.npz')
assert initial_meta['contract_sha256'] == comparison['contract_sha256']
for key, value in initial.state_dict().items():
    np.testing.assert_array_equal(value.numpy(), parent_policy.state_dict()[key].numpy())
del initial, parent_policy
refreshes = report['training_refreshes']
assert [r['epoch'] for r in refreshes] == list(range(1, 1 + 5*len(refreshes), 5))
assert len(refreshes) <= 10 and all(r['epoch'] <= min(50, fit['epochs_completed'] + 1) for r in refreshes)
verified_refreshes = []
for refresh in refreshes:
    epoch = refresh['epoch'] - 1
    assert refresh['samples'] == 4510 and refresh['human_probability'] == (.5 if epoch < 20 else 0)
    snapshot_path = output / f"refresh-{epoch + 1}.npz"
    assert sha(snapshot_path) == refresh['snapshot_sha256']
    snapshot, snapshot_meta = GoalFirstPolicy.load(snapshot_path)
    assert snapshot_meta == dict(epoch=epoch + 1, contract_sha256=comparison['contract_sha256'])
    if epoch == 0:
        first, _ = GoalFirstPolicy.load(output / 'initial.npz')
        for key, value in snapshot.state_dict().items():
            np.testing.assert_array_equal(value.numpy(), first.state_dict()[key].numpy())
        del first
    digest = hashlib.sha256()
    samples = 0
    for game_index, directory in enumerate(teach):
        original = collect([directory], contract['vocabulary'], spatial=True, missing_fields=True)[0]
        rebuilt = mixed_history_examples(snapshot, original, teacher_states(directory), contract['vocabulary'],
            construction_products(read(directory / 'static.json')['game_data']),
            human_probability=refresh['human_probability'], seed=8150+epoch*100+game_index)
        for inputs, label, _, _ in rebuilt:
            if label is None:
                continue
            for array in (*inputs['encoder'], inputs['actor_mask'], inputs['target_mask'], inputs['point_features']):
                array = np.asarray(array)
                digest.update(str((array.dtype.str, array.shape)).encode())
                digest.update(array.tobytes())
            digest.update(repr(label).encode())
            samples += 1
        del original, rebuilt
    assert samples == 4510 and digest.hexdigest() == refresh['examples_sha256']
    verified_refreshes.append(dict(epoch=epoch+1, samples=samples, examples_sha256=digest.hexdigest(), snapshot_sha256=sha(snapshot_path)))
    del snapshot
    print(json.dumps(dict(stage='independent_refresh_verified', epoch=epoch+1, samples=samples)), flush=True)
totals = {name: Counter() for name in ('predicted', 'ability_oracle', 'ability_actor_oracle')}
point_counts = Counter()
point_sums = Counter()
commands = {(r['game'], r['row']): r for r in report['commands']}
assert len(commands) == len(report['commands']) == 4805
own_history_hashes = {}
macro_correct = macro_rows = 0
for directory in teach + diagnostic:
    game = directory.name
    examples = collect([directory], contract['vocabulary'], spatial=True, missing_fields=True)[0]
    products = construction_products(read(directory / 'static.json')['game_data'])
    examples = retained_history_examples(examples, teacher_states(directory), contract['vocabulary'], products)
    audit = audit_commands(policy, examples)
    assert audit['predicted'] == report['per_game'][game]
    if directory in teach:
        for name in totals:
            totals[name].update(audit[name])
            error = audit['point_errors'][name]
            point_counts[name] += error['count']
            point_sums[name] += error['count'] * (error['mean'] or 0)
        part = teaching_support(policy, [(x, y) for x, y, _, _ in examples if y is not None])
        for key in support:
            reconstructed_support[key] |= part[key]
    else:
        assert audit == report['diagnostic']
    static = read(directory / 'static.json')['game_data']
    abilities = {a['ability_id']: a for a in static['abilities']}
    families = {}
    for index, (inputs, _, command, exclusion) in enumerate(examples):
        stored = commands[(game, index)]
        assert stored['command'] == command.as_dict() and stored['exclusion'] == exclusion
        assert json_value(policy.predict(inputs)) == stored['prediction']
        name = abilities[command.ability].get('friendly_name', abilities[command.ability]['link_name'])
        families.setdefault(name, []).append(examples[index])
        if game == '774' and any(k in name.upper() for k in ('BUILD ', 'TRAIN ', 'RESEARCH ')):
            macro_rows += 1
            macro_correct += int(stored['prediction']['ability'] == command.ability)
    assert set(families) == set(report['families'][game])
    for name, rows in families.items():
        assert audit_commands(policy, rows) == report['families'][game][name]
    rebuilt, records = prediction_history_examples(policy, examples, teacher_states(directory), contract['vocabulary'], construction_products(static))
    own_path = output / f'{game}-own-history.json'
    assert json_value(records) == read(own_path)
    assert audit_commands(policy, rebuilt) == report['own_history'][game]
    own_history_hashes[game] = sha(own_path)
    del examples, rebuilt, records, families
    print(json.dumps(dict(stage='independently_verified', game=game, predicted=audit['predicted'])), flush=True)
for name, values in totals.items():
    assert dict(values) == report['teaching'][name]
    expected = report['teaching']['point_errors'][name]
    assert point_counts[name] == expected['count']
    if point_counts[name]:
        np.testing.assert_allclose(point_sums[name] / point_counts[name], expected['mean'], atol=1e-10, rtol=1e-12)
    else:
        assert expected['mean'] is None
for key in support:
    np.testing.assert_array_equal(reconstructed_support[key], support[key])
assert macro_rows == comparison['diagnostic_macro_rows'] == 91 and macro_correct == comparison['diagnostic_macro_ability']
t, d, g = report['teaching']['predicted'], report['diagnostic']['predicted'], contract['gates']
improved = sum(report['per_game'][p.name]['complete'] > contract['baseline_per_game'][p.name]['complete'] for p in teach)
gates = dict(teaching_actors=t['actors'] >= g['teaching_actors'], teaching_complete=t['complete'] >= g['teaching_complete'],
             teaching_games=improved >= g['teaching_games'], diagnostic_actors=d['actors'] >= g['diagnostic_actors'],
             diagnostic_complete=d['complete'] >= g['diagnostic_complete'], diagnostic_target=d['target'] >= g['diagnostic_target'],
             diagnostic_ability=d['ability'] >= g['diagnostic_ability'], diagnostic_macro_ability=macro_correct >= g['diagnostic_macro_ability'])
own_teaching_complete = sum(report['own_history'][p.name]['predicted']['complete'] for p in teach)
own_diagnostic = report['own_history']['774']['predicted']
own_records = read(output / '774-own-history.json')
diagnostic_commands = [r for r in report['commands'] if r['game'] == '774']
# The static vocabulary is identical across sources; verify macro membership
# independently from its retained human-command ability metadata.
macro_ids = {i for i, a in abilities.items() if any(k in a.get('friendly_name', '').upper() for k in ('BUILD ', 'TRAIN ', 'RESEARCH '))}
own_macro_correct = sum(r['command']['ability'] in macro_ids and o['prediction']['ability'] == r['command']['ability'] for r, o in zip(diagnostic_commands, own_records, strict=True))
assert own_teaching_complete == comparison['own_teaching_complete']
assert own_diagnostic == comparison['own_diagnostic'] and own_macro_correct == comparison['own_diagnostic_macro_ability']
gates.update(own_teaching_complete=own_teaching_complete >= g['own_teaching_complete'],
             own_diagnostic_ability=own_diagnostic['ability'] >= g['own_diagnostic_ability'],
             own_diagnostic_actors=own_diagnostic['actors'] >= g['own_diagnostic_actors'],
             own_diagnostic_target=own_diagnostic['target'] >= g['own_diagnostic_target'],
             own_diagnostic_complete=own_diagnostic['complete'] >= g['own_diagnostic_complete'],
             own_diagnostic_macro_ability=own_macro_correct >= g['own_diagnostic_macro_ability'])
assert gates == comparison['gates'] and all(gates.values()) == comparison['all_gates_passed']
assert report['native_games'] == report['rl_updates'] == comparison['native_games'] == comparison['rl_updates'] == 0
assert comparison['promoted'] is False
verification = dict(status='verified_imitation_gates_passed' if all(gates.values()) else 'verified_completed_failure',
                    verifier_sha256=sha(__file__), comparison_sha256=sha(output / 'comparison.json'),
                    final_telemetry_sha256=sha(telemetry_path), contract_sha256=comparison['contract_sha256'],
                    checkpoint_sha256=comparison['checkpoint_sha256'], report_sha256=comparison['report_sha256'],
                    own_history_sha256=own_history_hashes, independently_verified_training_refreshes=verified_refreshes, independent_prediction_rows=4805, gates=gates,
                    max_cpu=max(s['whole_cpu_percent'] for s in telemetry['samples']),
                    scope='Independent human replay reconstruction, including hypothetical prediction history. No native competence evidence.',
                    native_games=0, rl_updates=0, promoted=False)
(output / 'verification.json').write_text(json.dumps(verification, indent=2) + '\n')
print(json.dumps(verification), flush=True)
