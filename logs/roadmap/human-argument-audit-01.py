"""Read-only held-game argument audit; human abilities and groups supplied."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
from src.learning.argument_train import collect
from src.learning.imitation import FactorPolicy
from src.learning.imitation_train import metrics
from src.learning.teacher_states import teacher_states

root = Path('logs/roadmap')
macro_path = root / 'imitation-prefix-240-01/policy.npz'
argument_path = root / 'arguments-prefix-240-01/arguments.npz'
macro = FactorPolicy.load(macro_path)
policy = FactorPolicy.load(argument_path)
train_ids = [51574, 51573, 51958, 51890, 51891]
coverage = []
for replay_id in [*train_ids, 50925]:
    directory = root / f'issued-{replay_id}'
    static = json.loads((directory / 'static.json').read_text())
    names = {a['ability_id']: a.get('friendly_name', a.get('link_name', ''))
             for a in static['game_data']['abilities']}
    for seconds in [240, 600, None]:
        commands = Counter()
        attacks = Counter()
        for row, state in teacher_states(directory, seconds):
            known = {u['tag']: u for u in state['units'] + state['owned_memory']}
            for command in row['commands']:
                ability = command['ability']
                commands[ability] += 1
                if 'attack' in names.get(ability, '').lower():
                    target = known.get(command['target_unit'], {})
                    attacks[str(target.get('alliance', 'point'))] += 1
        coverage.append({'replay': replay_id, 'seconds': seconds,
                         'commands': sum(commands.values()),
                         'attack_target_alliances': dict(attacks),
                         'attack_abilities': {str(a): {'name': names.get(a), 'count': n}
                                              for a,n in commands.items()
                                              if 'attack' in names.get(a, '').lower()}})
held = []
for seconds in [240, 600, None]:
    x, labels, points, _, _ = collect([root / 'issued-50925'], macro, seconds)
    report = metrics(policy, x, labels, points)
    predicted = policy.predict(x)
    valid = labels['point_valid'].astype(bool)
    errors = np.linalg.norm(predicted['point'][:, :2] - points, axis=1) * 128
    report['point_error_percentiles_tiles'] = np.percentile(errors[valid], [50,90,99]).tolist()
    report['seconds'] = seconds
    held.append(report)
report = {'status': 'completed',
          'scope': 'teacher-forced held-human-game arguments; no live skill claim',
          'macro_sha256': hashlib.sha256(macro_path.read_bytes()).hexdigest(),
          'arguments_sha256': hashlib.sha256(argument_path.read_bytes()).hexdigest(),
          'coverage': coverage, 'held_game': held}
output = root / 'human-argument-audit-01.json'
with output.open('x') as stream:
    json.dump(report, stream, indent=2)
print(json.dumps(report))
