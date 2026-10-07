"""Frozen human-label and actor-score audit; no fitting or native games."""
import gzip
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np

from src.learning.actor_selection import actor_features, select_actors
from src.learning.global_imitation import global_features
from src.learning.imitation import FactorPolicy, unit_features
from src.learning.teacher_states import own_actors, teacher_states

root = Path('logs/roadmap')
out = root / 'worker-harvest-diagnosis-01'
out.mkdir(exist_ok=False)
datasets = [root / 'issued-timing-masked-01' / f'issued-{i}' for i in (51574, 51573, 51958, 51890, 51891, 50925)]
datasets += [root / 'issued-timing-masked-01/issued-51960-p1', root / 'issued-51482-rom-masked-01']
paths = [root / 'consistent-fullgame-02/macro/policy.npz', root / 'consistent-fullgame-02/actors/actors.npz']
trace = root / 'consistent-fullgame-live-zerg-02/trace.jsonl.gz'
files = [Path(__file__), *paths, trace, *sorted(Path('src/learning').glob('*.py')), *[d / n for d in datasets for n in ('dataset.json', 'static.json', 'examples.jsonl.gz')]]
def hashes():
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before = hashes()
contract = {'scope': 'Teacher-conditioned harvest actor selection with all known own actors synthetically eligible; not native legality or autonomous generalization. Mineral targets only. Builder means SCV first order is a catalogue Build ability, not proof construction will finish.', 'datasets': list(map(str, datasets)), 'models': list(map(str, paths)), 'no_fit_no_rl': True, 'reserved_51886_unused': True, 'files_before': before}
(out / 'contract.json').write_text(json.dumps(contract, indent=2) + '\n')
macro, actor = [FactorPolicy.load(p) for p in paths]
start = time.monotonic()
records = []

def scores(state, ability):
    own = own_actors(state)
    x, origin = global_features(state, macro.unit_types, macro.sizes['ability'], canonical=True, summarize=True, semantics=macro.evidence.get('action_history_encoder') == 'roles_targets_age', upgrade_count=macro.evidence.get('upgrade_count', 0))
    context = macro.command_context(x, ability)
    features = np.stack([actor_features(state, u, i, macro.unit_types, macro.sizes['ability'], origin, context) for i, u in enumerate(own)])
    logits = actor.predict(features)['ability']
    available = {u['tag']: {ability} for u in own}
    selected = {u['tag'] for u in select_actors(own, logits, available, ability)}
    return own, features, logits[:, 1] - logits[:, 0], selected

for d in datasets:
    static = json.loads((d / 'static.json').read_text())
    builds = {a['ability_id'] for a in static['game_data']['abilities'] if a.get('friendly_name', '').startswith('Build ')}
    for row, state in teacher_states(d):
        known = {u['tag']: u for u in state['units']}
        for command in row['commands']:
            target = known.get(command['target_unit'], {})
            if command['ability'] not in (1, 295) or target.get('mineral_contents', 0) <= 0:
                continue
            own, features, margins, selected = scores(state, command['ability'])
            workers = [(i, u) for i, u in enumerate(own) if u['unit_type'] == 45]
            if not any(u['tag'] in command['units'] for _, u in workers):
                continue
            builders = [{'tag': u['tag'], 'order': u['orders'][0], 'teacher_selected': u['tag'] in command['units'], 'model_selected': u['tag'] in selected, 'margin': float(margins[i])} for i, u in workers if u.get('orders') and u['orders'][0]['ability_id'] in builds]
            records.append({'dataset': str(d), 'loop': row['action_loop'], 'teacher': command, 'teacher_actor_set_hit': selected == set(command['units']), 'builders': builders, 'worker_count': len(workers), 'predicted': sorted(selected)})

with gzip.open(trace, 'rt') as stream:
    frame = next(r for r in map(json.loads, stream) if r['observation']['game_loop'] == 1448)
state = dict(frame['observation'], recent_commands=frame['model_recent_commands'])
assert 'map_size' in state
own, features, margins, selected = scores(state, 1)
live = []
for i, u in enumerate(own):
    if u['unit_type'] == 45:
        order = u.get('orders', [])
        offset = len(unit_features(state, u, macro.unit_types))
        live.append({'tag': u['tag'], 'orders': order, 'margin': float(margins[i]), 'oracle_selected': u['tag'] in selected, 'build321_onehot': float(features[i, offset + 321]), 'build321_training_mean': float(actor.feature_mean[offset + 321]), 'build321_training_scale': float(actor.feature_scale[offset + 321])})
assert next(u for u in live if u['tag'] == 4350803969)['build321_onehot'] == 1
def summarize(rows):
    builders = [b for r in rows for b in r['builders']]
    return {'harvest_commands': len(rows), 'actor_set_hits': sum(r['teacher_actor_set_hit'] for r in rows), 'commands_with_builders': sum(bool(r['builders']) for r in rows), 'builder_candidates': len(builders), 'teacher_selected_builders': sum(b['teacher_selected'] for b in builders), 'teacher_selected_builders_nonqueued': sum(b['teacher_selected'] and not r['teacher']['queue'] for r in rows for b in r['builders']), 'model_selected_builders': sum(b['model_selected'] for b in builders), 'builder_false_positives': sum(b['model_selected'] and not b['teacher_selected'] for b in builders), 'builder_order_counts': dict(Counter(b['order']['ability_id'] for b in builders))}
assert hashes() == before
report = dict(contract, status='completed', by_dataset={str(d): summarize([r for r in records if r['dataset'] == str(d)]) for d in datasets}, aggregate=summarize(records), records=records, live={'loop': 1448, 'workers': live, 'issued': frame['issued_model_commands'], 'scope': 'Unfiltered actor margins reproduced from traced live state/history; synthetic eligibility differs from native mask'}, files_after=hashes(), wall_seconds=time.monotonic() - start)
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': 'completed', 'by_dataset': report['by_dataset'], 'live_workers': live, 'wall_seconds': report['wall_seconds']}, indent=2))
