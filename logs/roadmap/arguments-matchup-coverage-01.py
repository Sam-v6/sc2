"""Fixed-model human-data coverage experiment; ability and actors are supplied."""
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from src.learning.argument_train import collect
from src.learning.global_imitation import coordinate_signs, global_features
from src.learning.imitation import FactorPolicy
from src.learning.imitation_train import equal_replay_weights, metrics
from src.learning.imitation_play import decode_commands, replace_arguments
from src.learning.teacher_states import teacher_states, own_actors

root = Path('logs/roadmap')
out = root / 'arguments-matchup-coverage-01'
out.mkdir(exist_ok=False)
macro_path = root / 'imitation-prefix-240-01/policy.npz'
baseline_path = root / 'arguments-full-human-01/arguments.npz'
macro = FactorPolicy.load(macro_path)
baseline = FactorPolicy.load(baseline_path)
train = [root / f'issued-{i}' for i in (51574, 51573, 51958, 51890, 51891)] + [root / 'issued-51957-p1']
held = [root / 'issued-50925', root / 'issued-51960-p1', root / 'issued-51959-held-01']
contract = {
    'scope': 'supervised matchup coverage only; human ability and actor group supplied, not complete command imitation',
    'change': 'add one same-player TvT training game; unchanged base-relative representation and 32-hidden architecture',
    'epochs': 600, 'seed': 5001,
    'train': [str(p) for p in train], 'evaluation': [str(p) for p in held],
    'fresh_held': str(held[-1]),
    'limits': 'Other-player TvP/Z coverage still missing; Lyra and Huski are reused diagnostics. No live promotion or RL readiness.',
    'gate': 'higher decoded argument fidelity on both TvT diagnostics, no lower on fresh TvZ, and no lower enemy-unit target fidelity',
    'point_tolerance_tiles': 2.0,
    'macro_sha256': hashlib.sha256(macro_path.read_bytes()).hexdigest(),
    'baseline_sha256': hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
}
(out / 'contract.json').write_text(json.dumps(contract, indent=2) + '\n')

def decoded_audit(directory, policies):
    static = json.loads((directory / 'static.json').read_text())
    catalog = {a['ability_id']: a for a in static['game_data']['abilities']}
    observations = {name: [] for name in policies}
    for row, state in teacher_states(directory):
        own = {u['tag']: u for u in own_actors(state)}
        units = {u['tag']: u for u in state['units']}
        x, origin = global_features(state, macro.unit_types, macro.sizes['ability'], canonical=True, summarize=True)
        for truth in row['commands']:
            group = [own[t] for t in truth['units']]
            from src.learning.actor_selection import group_features
            features = group_features(state, group, macro.unit_types, macro.sizes['ability'], origin, macro.command_context(x, truth['ability']))
            enemy = truth['target_unit'] is not None and units.get(truth['target_unit'], {}).get('alliance') == 4
            for name, model in policies.items():
                output = replace_arguments({}, model.predict(features[None, :]), coordinate_signs(state, origin))
                output['ability'] = np.zeros((1, macro.sizes['ability']))
                output['point'] = output['point'][:, :2]
                commands, _ = decode_commands(state, [dict(group[0], position=[*origin, 0])], output,
                    {group[0]['tag']: {truth['ability']}}, catalog, macro.unit_types, state['map_size'], chosen_abilities=[truth['ability']])
                exact = False
                if commands:
                    command = commands[0]
                    target = command.target_unit == truth['target_unit']
                    if truth['target_point'] is None:
                        target &= command.target_point is None
                    else:
                        target &= command.target_point is not None and np.linalg.norm(np.asarray(command.target_point) - truth['target_point']) <= 2.0
                    exact = bool(target and command.autocast == truth['autocast'] and command.queue == truth['queue'])
                observations[name].append({'correct': exact, 'enemy_unit': enemy, 'attack': truth['ability'] == 23})
    return {name: {stratum: {'commands': len(rows), 'argument_fidelity': float(np.mean([r['correct'] for r in rows])) if rows else None}
            for stratum, rows in [('all', values), ('enemy_unit', [r for r in values if r['enemy_unit']]), ('attack', [r for r in values if r['attack']])]}
            for name, values in observations.items()}

start = time.monotonic()
x, labels, points, ranges, sources = collect(train, macro, None)
policy = FactorPolicy(x.shape[1], 1, macro.unit_types, seed=5001)
policy.feature_mean = x.mean(axis=0)
policy.feature_scale = np.maximum(x.std(axis=0), .1)
weights = equal_replay_weights(np.ones(len(x)), ranges)
active = np.flatnonzero(np.any(x != policy.feature_mean, axis=0))
px = x[:, active]
rng = np.random.default_rng(5001)
for epoch in range(600):
    order = rng.permutation(len(x))
    for begin in range(0, len(x), 128):
        ix = order[begin:begin+128]
        policy.learn(px[ix], {k:v[ix] for k,v in labels.items()}, points[ix], weights=weights[ix], feature_indices=active)
    if epoch % 100 == 0:
        print(json.dumps({'epoch': epoch, 'wall_seconds': time.monotonic()-start}), flush=True)
results = []
for directory in held:
    vx, vy, vp, _, vs = collect([directory], macro, None)
    assert not {s['sha256'] for s in sources} & {s['sha256'] for s in vs}
    results.append({'dataset': str(directory), 'sources': vs, 'baseline': metrics(baseline, vx, vy, vp),
                    'coverage': metrics(policy, vx, vy, vp), 'decoded': decoded_audit(directory, {'baseline': baseline, 'coverage': policy})})
def fidelity(r, model, stratum='all'):
    return r['decoded'][model][stratum]['argument_fidelity']
gate = all(fidelity(r, 'coverage') > fidelity(r, 'baseline') for r in results[:2]) and fidelity(results[-1], 'coverage') >= fidelity(results[-1], 'baseline')
gate &= all(fidelity(r, 'coverage', 'enemy_unit') is None or fidelity(r, 'coverage', 'enemy_unit') >= fidelity(r, 'baseline', 'enemy_unit') for r in results)
report = dict(contract, status='completed', commands=len(x), sources=sources, training=metrics(policy, x, labels, points),
              evaluation_results=results, gate_passed=bool(gate), wall_seconds=time.monotonic()-start, point_origin='base')
policy.save(out / 'arguments.npz', report)
report['checkpoint_sha256'] = hashlib.sha256((out / 'arguments.npz').read_bytes()).hexdigest()
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': 'completed', 'gate_passed': bool(gate), 'wall_seconds': report['wall_seconds'], 'decoded': [r['decoded'] for r in results]}), flush=True)
