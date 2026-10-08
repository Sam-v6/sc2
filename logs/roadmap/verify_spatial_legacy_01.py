import json
from pathlib import Path
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_audit import audit_commands
from src.learning.entity_train import collect, digest, validate_datasets
root=Path.cwd();directory=root/'logs/roadmap/joint-entity-fit-04';r=json.loads((directory/'report.json').read_text());c=json.loads((directory/'configuration.json').read_text());policy,_=JointEntityPolicy.load(directory/'policy.npz');assert policy.spatial_features==2
paths={role:[Path(s['dataset']) for s in c['sources'] if s['role']==role] for role in ('teaching','diagnostic')}
assert validate_datasets(paths['teaching'],paths['diagnostic'])==c['sources']
bound=[directory/'policy.npz',directory/'report.json',Path(__file__),*[Path(p) for p in c['code_before']],root/'src/learning/entity_spatial.py',root/'src/learning/spatial_construction.py']
before={str(p):digest(p) for p in bound};results={}
for role,datasets in paths.items():
 examples,_=collect(datasets,c['vocabulary']);result=audit_commands(policy,examples);assert result==r['teaching' if role=='teaching' else 'validation'];results[role]=result
assert before=={p:digest(Path(p)) for p in before}
assert validate_datasets(paths['teaching'],paths['diagnostic'])==c['sources']
receipt=dict(status='verified',results=results,current_code_and_checkpoint_bindings=before,scope='Exact complete legacy fit04 reports regenerated under opt-in spatial integration. Current audit bindings stable; historical fit code hashes are not claimed current. No spatial fit, native/RL or reserved evaluation.')
(root/'logs/roadmap/spatial-legacy-compatibility-01.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
