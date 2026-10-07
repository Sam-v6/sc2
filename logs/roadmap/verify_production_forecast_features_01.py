"""Reconstruct every stored causal feature row from the bound human corpus."""
import hashlib
import json
from pathlib import Path
from scipy.sparse import csr_matrix, hstack, load_npz, vstack
from src.learning.entity_train import collect
from src.learning.entity_type_status import unit_type_status
from src.learning.intention_probe import probe_features
out=Path('logs/roadmap/production-forecast-probe-01')
report=json.loads((out/'report.json').read_text())
for p,d in report['bindings'].items():
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==d,p
counts=json.loads(Path('logs/roadmap/joint-professional-fit-05/configuration.json').read_text())['vocabulary']
total=0
for role in ('teaching','development'):
    refs=json.loads((out/f'{role}-rows.json').read_text())
    games={}
    for g in sorted({r['game'] for r in refs}):
        root=Path('logs/roadmap')/('pro-demonstrations-production-08' if role=='teaching' else 'pro-demonstrations-07')/g
        examples=collect([root],counts,spatial=True,missing_fields=True)[0]
        games[g]=examples
        print('reconstructed',g,len(examples),flush=True)
    states=[]; histories=[]
    for r in refs:
        inputs=games[r['game']][r['row']][0]
        s,h=probe_features(inputs,*counts[:2])
        states.append(hstack([s,csr_matrix(unit_type_status(inputs,counts[0]).reshape(1,-1))]).tocsr())
        histories.append(h)
    for name,items in [('state',states),('history',histories)]:
        rebuilt=vstack(items).tocsr(); saved=load_npz(out/f'{role}-{name}.npz')
        assert saved.shape==rebuilt.shape and (saved-rebuilt).nnz==0,(role,name)
    total+=len(refs)
result=dict(status='verified',causal_feature_rows=total,report_sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest())
(out/'feature-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
