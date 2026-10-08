"""Read-only oracle: exact past retained human commands, not model predictions."""
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from src.learning.actor_selection import construction_products
from src.learning.entity_audit import audit_commands
from src.learning.entity_examples import state_inputs
from src.learning.entity_train import collect
from src.learning.goal_first_policy import GoalFirstPolicy
from src.learning.teacher_states import remember_command, teacher_states


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


root = Path('logs/roadmap/professional-goal-first-01')
output = root / 'retained-history-oracle.json'
assert not output.exists()
contract = json.loads((root / 'contract.json').read_text())
report = json.loads((root / 'report.json').read_text())
verified = json.loads((root / 'verification.json').read_text())
assert sha(root / 'report.json') == verified['report_sha256']
assert sha(root / 'policy.npz') == verified['checkpoint_sha256']
torch.set_num_threads(2)
torch.set_num_interop_threads(2)
policy, _ = GoalFirstPolicy.load(root / 'policy.npz')
result = dict(helper_sha256=sha(__file__), checkpoint_sha256=verified['checkpoint_sha256'],
              report_sha256=verified['report_sha256'], games={},
              scope='Human-state/schedule oracle using exact prior retained human commands. Current/future command never supplied to prediction. Original full event-slot history, which includes unresolved events, is replaced. Not ordinary deployed inference, fitting or native competence.')
for source in contract['sources']:
    directory = Path(source['dataset'])
    game = directory.name
    examples = collect([directory], contract['vocabulary'], spatial=True, missing_fields=True)[0]
    static = json.loads((directory / 'static.json').read_text())['game_data']
    products = construction_products(static)
    history, rebuilt, records = [], [], []
    previous_loop = None
    for index, ((old, label, command, exclusion), (row, observed)) in enumerate(zip(examples, teacher_states(directory), strict=True)):
        assert row['commands'] == [command.as_dict()] and observed['game_loop'] == row['action_loop']
        assert previous_loop is None or row['action_loop'] >= previous_loop
        previous_loop = row['action_loop']
        state = dict(observed, decision_loop=row['action_loop'], recent_commands=list(history), history_quality='event_slots')
        inputs = state_inputs(state, *contract['vocabulary'], products=products, missing_fields=True)
        assert inputs['tags'] == old['tags']
        for component in (1, 2, 3):
            np.testing.assert_array_equal(inputs['encoder'][component], old['encoder'][component])
        for begin, end in ((0, 30), (94, 124)):
            np.testing.assert_array_equal(inputs['encoder'][0][:, begin:end], old['encoder'][0][:, begin:end])
        for name in ('actor_mask', 'target_mask', 'entity_positions', 'points', 'world_points', 'point_radii'):
            np.testing.assert_array_equal(inputs[name], old[name])
        inputs['point_features'] = old['point_features']
        prediction = policy.predict(inputs)
        records.append(dict(row=index, prediction=prediction,
                            original_prior_events=len(observed['recent_commands']),
                            original_unknown_events=sum(bool(c.get('unknown')) for c in observed['recent_commands']),
                            retained_prior_events=len(history)))
        rebuilt.append((inputs, label, command, exclusion))
        # Append only AFTER predicting the current command.
        remembered = dict(remember_command(command.as_dict(), observed, row['action_loop']), verified=True)
        history = [*history, remembered][-32:]
    audit = audit_commands(policy, rebuilt)
    result['games'][game] = dict(audit=audit, original_human_history=report['per_game'][game],
                                 prediction_history=report['own_history'][game]['predicted'], records=records)
    print(json.dumps(dict(game=game, retained_gold_history=audit['predicted'],
                          original_human_history=report['per_game'][game], prediction_history=report['own_history'][game]['predicted'])), flush=True)
    del examples, rebuilt, records
for path, digest in contract['bindings'].items():
    assert sha(path) == digest
assert not torch.cuda.is_initialized()
output.write_text(json.dumps(result, indent=2) + '\n')
