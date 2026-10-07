import hashlib
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np

from src.learning.actor_selection import construction_products
from src.learning.entity_encoder import JointEntityEncoder
from src.learning.entity_examples import command_label, decode_command, state_inputs
from src.learning.entity_policy import JointEntityPolicy
from src.learning.gameplay import Command
from src.learning.teacher_states import teacher_states, remember_command

root = Path.cwd()
contract = root / 'logs/roadmap/expanded-human-macro-01/contract.json'
inventory = json.loads(contract.read_text())['train_inventory']
paths = [root / p for p in ('src/learning/entity_encoder.py', 'src/learning/entity_policy.py', 'src/learning/entity_examples.py', 'src/learning/teacher_states.py', 'src/learning/gameplay.py', 'src/learning/actor_selection.py')]
paths += [contract, Path(__file__)]
paths += [Path(item['dataset']) / name for item in inventory for name in ('static.json', 'examples.jsonl.gz')]
def bindings():
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before = bindings()
start = time.monotonic()
results = []
delays = (0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512)
for item in inventory:
    directory = Path(item['dataset'])
    static = json.loads((directory/'static.json').read_text())['game_data']
    counts = [max(x[k] for x in static[name])+1 for name,k in (('units','unit_id'),('abilities','ability_id'),('upgrades','upgrade_id'))]
    products = construction_products(static)
    report = dict(dataset=str(directory), commands=0, representable=0, errors=[], modes=Counter(), masked_delay=0, bursts=0, maximum_entities=0, numeric_bytes=0)
    policy = None
    for row, state in teacher_states(directory):
        state = dict(state, decision_loop=row['action_loop'], recent_commands=list(state['recent_commands']))
        report['bursts'] += int(len(row['commands']) > 1)
        for index, raw in enumerate(row['commands']):
            report['commands'] += 1
            inputs = state_inputs(state, *counts, products)
            report['maximum_entities'] = max(report['maximum_entities'], len(inputs['tags']))
            report['numeric_bytes'] += inputs['encoder'][0].nbytes
            command = Command(**dict(raw, units=tuple(raw['units']), target_point=tuple(raw['target_point']) if raw.get('target_point') is not None else None))
            delay = row['next_action_delay'] if index == len(row['commands'])-1 else 0
            try:
                label = command_label(command, inputs, delays, delay)
                decoded = decode_command(label, inputs)
                assert decoded.units == command.units
                assert decoded.ability == command.ability and decoded.queue == command.queue and decoded.autocast == command.autocast and decoded.target_unit == command.target_unit
                if command.target_point is not None:
                    np.testing.assert_allclose(decoded.target_point, command.target_point, atol=1e-5)
                assert Command.from_proto(decoded.to_proto()).units == command.units
                report['representable'] += 1
                report['modes'][label['mode']] += 1
                report['masked_delay'] += int(delay is None)
                if policy is None:
                    policy = JointEntityPolicy(JointEntityEncoder(94, len(inputs['encoder'][3]), 9, counts[0], counts[1], hidden=32, seed=7000), delays=delays, seed=7001)
                    loss, gradients = policy.loss_and_gradients(inputs, label)
                    assert np.isfinite(loss) and all(np.isfinite(g).all() for g in gradients.values())
                    report['initial_untrained_loss'] = loss
                    report['parameter_bytes'] = sum(p.nbytes for p in policy.parameters.values())
            except ValueError as error:
                report['errors'].append(dict(loop=row['action_loop'], command=raw, reason=str(error)))
            state['recent_commands'].append(remember_command(raw, state, row['action_loop']))
    assert report['commands'] == item['commands']
    results.append(report)
    print(json.dumps({k:v for k,v in report.items() if k!='errors'}), flush=True)
after = bindings()
assert before == after
report = dict(scope='Nine teaching games, causal conversion and label roundtrip; one untrained joint gradient per game; no optimizer, holdout, native play or RL', results=results, elapsed_seconds=time.monotonic()-start, sources_before=before, sources_after=after, source_bindings_unchanged=True)
(root/'logs/roadmap/entity-examples-real-audit-01.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(dict(commands=sum(r['commands'] for r in results), representable=sum(r['representable'] for r in results), seconds=report['elapsed_seconds'])), flush=True)
