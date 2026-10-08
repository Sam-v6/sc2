import json
from pathlib import Path
import time
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect, digest, validate_datasets
from src.learning.entity_audit import audit_commands

root=Path.cwd(); old=root/'logs/roadmap/joint-entity-fit-01'
configuration=json.loads((old/'configuration.json').read_text())
original=json.loads((old/'report.json').read_text())
checkpoint=old/'policy.npz'
before=digest(checkpoint)
assert before==original['checkpoint_sha256']
policy,metadata=JointEntityPolicy.load(checkpoint)
assert not policy.refinement
paths={role:[Path(s['dataset']) for s in configuration['sources'] if s['role']==role] for role in ('teaching','diagnostic')}
assert validate_datasets(paths['teaching'],paths['diagnostic'])==configuration['sources']
start=time.monotonic(); results={}
for role,directories in paths.items():
    examples,_=collect(directories,configuration['vocabulary'])
    results[role]=audit_commands(policy,examples)
    assert results[role]==original['teaching' if role=='teaching' else 'validation']
assert digest(checkpoint)==before
assert validate_datasets(paths['teaching'],paths['diagnostic'])==configuration['sources']
report=dict(status='passed',baseline_checkpoint_sha256=before,results=results,seconds=time.monotonic()-start,scope='Entire teaching/reused-diagnostic baseline results exactly regenerated with compatibility branch; historical original code bindings are not claimed unchanged',reserved_replays_opened=False)
(root/'logs/roadmap/refinement-baseline-compatibility-01.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status='passed',seconds=report['seconds'])),flush=True)
