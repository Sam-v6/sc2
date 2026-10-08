"""Validate source bindings, split identities and exact raw-label representation."""
import hashlib,json
from pathlib import Path
from src.learning.entity_train import collect,validate_datasets
P=Path(__file__).parent
new=[Path('logs/roadmap/pro-demonstrations-09')/g for g in ('1038','163','1085','1032','130')]
old=[Path('logs/roadmap/pro-demonstrations-production-08')/g for g in ('294','870','955','839','991','523')]
held=[Path('logs/roadmap/pro-demonstrations-07')/g for g in ('887','920','851')]
counts=json.loads(Path('logs/roadmap/joint-professional-fit-05/configuration.json').read_text())['vocabulary']
validated=validate_datasets(old+new,held,missing_fields=True)
reserved=[Path('logs/roadmap/pro-demonstrations-07/848/dataset.json')]
seen={json.loads((d/'dataset.json').read_text())['sha256'] for d in old+new+held}
assert all(json.loads(p.read_text())['sha256'] not in seen for p in reserved)
results=[]
for d in new:
    examples,reports=collect([d],counts,spatial=True,missing_fields=True)
    row=dict(game=d.name,rows=len(examples),representable=sum(e[1] is not None for e in examples),reports=reports)
    results.append(row);print(json.dumps(row),flush=True)
report=dict(status='verified',rl=False,validated=validated,games=results,rows=sum(r['rows'] for r in results),representable=sum(r['representable'] for r in results),bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for d in new for p in (d/'dataset.json',d/'static.json',d/'examples.jsonl.gz')},verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(P/'encoding-verification.json').write_text(json.dumps(report,indent=2)+'\n')
