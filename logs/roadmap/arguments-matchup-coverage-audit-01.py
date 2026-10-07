"""Bind current artifacts and reproduce the completed evaluation without fitting."""
import ast
import hashlib
import json
from pathlib import Path
import numpy as np
from src.learning.argument_train import collect
from src.learning.global_imitation import coordinate_signs, global_features
from src.learning.imitation import FactorPolicy
from src.learning.imitation_train import metrics
from src.learning.imitation_play import decode_commands, replace_arguments
from src.learning.teacher_states import teacher_states, own_actors

root = Path('logs/roadmap')
out = root / 'arguments-matchup-coverage-01'
report = json.loads((out / 'report.json').read_text())
macro_path = root / 'imitation-prefix-240-01/policy.npz'
baseline_path = root / 'arguments-full-human-01/arguments.npz'
coverage_path = out / 'arguments.npz'
assert hashlib.sha256(macro_path.read_bytes()).hexdigest() == report['macro_sha256']
assert hashlib.sha256(baseline_path.read_bytes()).hexdigest() == report['baseline_sha256']
assert hashlib.sha256(coverage_path.read_bytes()).hexdigest() == report['checkpoint_sha256']
macro = FactorPolicy.load(macro_path)
baseline = FactorPolicy.load(baseline_path)
coverage = FactorPolicy.load(coverage_path)
script = root / 'arguments-matchup-coverage-01.py'
node = next(n for n in ast.parse(script.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'decoded_audit')
exec(compile(ast.Module(body=[node], type_ignores=[]), str(script), 'exec'))
files = [script, macro_path, baseline_path, coverage_path, out / 'contract.json', out / 'report.json']
files += [Path('src/learning') / (name + '.py') for name in ('argument_train', 'global_imitation', 'imitation', 'imitation_train', 'imitation_play', 'teacher_states', 'actor_selection', 'gameplay')]
for directory in report['train'] + report['evaluation']:
    files += [Path(directory) / name for name in ('dataset.json', 'static.json', 'examples.jsonl.gz')]
def inventory():
    return {str(p): {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}
before = inventory()
train_hashes = {json.loads((Path(p) / 'dataset.json').read_text())['sha256'] for p in report['train']}
for result in report['evaluation_results']:
    directory = Path(result['dataset'])
    vx, vy, points, _, sources = collect([directory], macro, None)
    assert not train_hashes & {s['sha256'] for s in sources}
    assert metrics(baseline, vx, vy, points) == result['baseline']
    assert metrics(coverage, vx, vy, points) == result['coverage']
    assert decoded_audit(directory, {'baseline': baseline, 'coverage': coverage}) == result['decoded']
assert inventory() == before
receipt = {'status': 'evaluation_reproduced_exactly', 'files': before,
           'verification': 'hash-bound current data, checkpoints and source unchanged across complete evaluation rerun; no fitting',
           'limits': 'Post-run audit does not retrospectively supply missing before-fit hashes. Fixed epochs, not matched minibatch count or compute.'}
(out / 'integrity-audit.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(receipt['status'], len(files), 'bound files')
