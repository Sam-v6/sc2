"""Launch the single predeclared ability-importance human experiment."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root=Path('logs/roadmap')
baseline=root/'joint-professional-fit-05'
configuration=json.loads((baseline/'configuration.json').read_text())
output=root/'joint-professional-fit-07'
assert not output.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
teaching=[s['dataset'] for s in configuration['sources'] if s['role']=='teaching']
diagnostic=[s['dataset'] for s in configuration['sources'] if s['role']=='diagnostic']
assert len(teaching)==9 and len(diagnostic)==1 and Path(diagnostic[0]).name=='774'
assert not any(Path(p).name in {'848','51483','51886'} for p in teaching+diagnostic)
for source in configuration['sources']:
    for filename,expected in source['bindings'].items():assert sha(Path(filename))==expected
    catalog=json.loads((Path(source['dataset'])/'static.json').read_text())['game_data']
    assert next(a for a in catalog['abilities'] if a['ability_id']==1)['friendly_name']=='Smart'
audit_path=root/'professional-command-failures-01.json'
audit=json.loads(audit_path.read_text())
macros={int(k.split(':')[2]):v['counts']['commands'] for k,v in audit['groups'].items()
        if k.startswith('diagnostic:') and k.split(':',3)[3].startswith(('Build ','Train ','Research '))}
assert sum(macros.values())==91
argv=[sys.executable,'-m','src.learning.entity_train','--train',*teaching,
      '--validation',*diagnostic,'--output',str(output),'--epochs','50',
      '--batch-size','16','--hidden','32','--rate','.001','--seed','8100',
      '--wall-seconds','600','--refinement','--actor-cutoff','--spatial',
      '--missing-fields','--role-pooling','--actor-relative-points','--ability-importance']
contract=dict(argv=argv,baseline_sha256=sha(baseline/'policy.npz'),
              baseline_configuration_sha256=sha(baseline/'configuration.json'),
              diagnostic_audit_sha256=sha(audit_path),macro_ability_counts=macros,
              helper_sha256=sha(Path(__file__)),
              trainer_sha256=sha(Path('src/learning/entity_train.py')),
              expected_updates=14100,
              gates=dict(complete_min=24,macro_ability_min=35,macro_total=91,
                         required_abilities=[319,321,560],ability_min=139,
                         smart_attack_ability_min=119,smart_attack_total=198,
                         teaching_complete_min=825),
              scope='One human supervised weighted experiment, same fit05 architecture/data/order/budget. Context normalization false. No reserved predictions, native games or RL.')
path=root/'joint-professional-importance-contract-01.json'
assert not path.exists();path.write_text(json.dumps(contract,indent=2)+'\n')
print(json.dumps(dict(contract=str(path),output=str(output))),flush=True)
result=subprocess.run(argv,check=False)
print(json.dumps(dict(training_exit_code=result.returncode)),flush=True)
raise SystemExit(result.returncode)
