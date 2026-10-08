"""Frozen-model history ablation on human states; never fits or plays games."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import torch

from src.learning.actor_selection import construction_products
from src.learning.entity_audit import audit_commands
from src.learning.entity_train import collect
from src.learning.goal_first_policy import GoalFirstPolicy
from src.learning.goal_first_train import _history_inputs, _history_rows
from src.learning.teacher_states import remember_command, teacher_states


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


started = time.monotonic()
torch.set_num_threads(2)
torch.set_num_interop_threads(2)
root = Path('logs/roadmap/professional-retained-history-01')
output = root / 'history-ablation.json'
assert not output.exists()
verification = json.loads((root / 'verification.json').read_text())
assert verification['status'] == 'verified_completed_failure'
for name, key in (('contract.json', 'contract_sha256'), ('report.json', 'report_sha256'), ('policy.npz', 'checkpoint_sha256')):
    assert sha(root / name) == verification[key]
contract = json.loads((root / 'contract.json').read_text())
report = json.loads((root / 'report.json').read_text())
policy, _ = GoalFirstPolicy.load(root / 'policy.npz')
result = dict(helper_sha256=sha(__file__), checkpoint_sha256=verification['checkpoint_sha256'],
              report_sha256=verification['report_sha256'], games={},
              scope='Frozen model on unchanged human states/times. Empty, one-command and eight-command exact past human histories. Read-only input ablation; no training, native games or RL. Diagnostic774 remains reused, not held out.')
for game in ('294', '774'):
    source = next(s for s in contract['sources'] if Path(s['dataset']).name == game)
    directory = Path(source['dataset'])
    examples = collect([directory], contract['vocabulary'], spatial=True, missing_fields=True)[0]
    products = construction_products(json.loads((directory / 'static.json').read_text())['game_data'])
    rows = list(teacher_states(directory))
    result['games'][game] = dict(retained32=report['per_game'][game], own32=report['own_history'][game]['predicted'], ablations={})
    for window in (0, 1, 8):
        history, rebuilt = [], []
        for _, (original, label, command, exclusion), row, observed in _history_rows(examples, rows):
            assert time.monotonic() - started < 300
            inputs = _history_inputs(original, row, observed, history[-window:] if window else [], contract['vocabulary'], products)
            rebuilt.append((inputs, label, command, exclusion))
            history = [*history, dict(remember_command(command.as_dict(), observed, row['action_loop']), verified=True)][-32:]
        audit = audit_commands(policy, rebuilt)
        result['games'][game]['ablations'][str(window)] = audit
        print(json.dumps(dict(game=game, human_history_window=window, predicted=audit['predicted'])), flush=True)
    del examples, rows, rebuilt
for path, digest in contract['bindings'].items():
    assert sha(path) == digest
assert not torch.cuda.is_initialized()
assert sha(root / 'policy.npz') == verification['checkpoint_sha256']
result['elapsed_seconds'] = time.monotonic() - started
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(dict(status='completed_read_only_ablation', output=str(output), sha256=sha(output), elapsed_seconds=result['elapsed_seconds'])), flush=True)
