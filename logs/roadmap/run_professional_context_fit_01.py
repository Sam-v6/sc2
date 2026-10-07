"""Launch exactly one predeclared normalization fit with existing human sources."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path('logs/roadmap')
baseline = root / 'joint-professional-fit-05'
configuration = json.loads((baseline / 'configuration.json').read_text())
output = root / 'joint-professional-fit-06'
assert not output.exists(), 'Do not overwrite/restart an experiment'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
teaching = [s['dataset'] for s in configuration['sources'] if s['role']=='teaching']
diagnostic = [s['dataset'] for s in configuration['sources'] if s['role']=='diagnostic']
assert len(teaching)==9 and len(diagnostic)==1 and Path(diagnostic[0]).name=='774'
assert not any(Path(p).name in {'848','51483','51886'} for p in teaching+diagnostic)
for source in configuration['sources']:
    for filename, expected in source['bindings'].items():
        assert sha(Path(filename)) == expected
argv = [sys.executable, '-m', 'src.learning.entity_train', '--train', *teaching,
        '--validation', *diagnostic, '--output', str(output),
        '--epochs','50','--batch-size','16','--hidden','32','--rate','.001',
        '--seed','8100','--wall-seconds','600','--refinement','--actor-cutoff',
        '--spatial','--missing-fields','--role-pooling','--actor-relative-points',
        '--context-layer-norm']
contract = dict(argv=argv, baseline_sha256=sha(baseline/'policy.npz'),
                baseline_configuration_sha256=sha(baseline/'configuration.json'),
                code_sha256={str(p):sha(p) for p in [Path('src/learning')/name for name in
                               ('entity_encoder.py','entity_policy.py','entity_train.py')]},
                helper_sha256=sha(Path(__file__)),
                scope='One matched human supervised normalization experiment. No reserved games, native games or RL.',
                expected_updates=14100,
                gates=dict(teaching_loss_ratio_max=.8, teaching_complete_min=1277,
                           teaching_games_improved_min=7, diagnostic_complete_min=24,
                           diagnostic_ability_min=135, diagnostic_actors_min=39))
path = root/'joint-professional-context-contract-01.json'
assert not path.exists()
path.write_text(json.dumps(contract,indent=2)+'\n')
print(json.dumps(dict(contract=str(path),output=str(output))),flush=True)
result = subprocess.run(argv,check=False)
print(json.dumps(dict(training_exit_code=result.returncode)),flush=True)
raise SystemExit(result.returncode)
