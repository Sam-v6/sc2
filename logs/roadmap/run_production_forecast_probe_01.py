"""Fixed human-label forecast diagnostic, no controller or RL."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from scipy.sparse import csr_matrix, hstack, vstack, save_npz
from src.learning.entity_train import collect, validate_datasets
from src.learning.entity_type_status import unit_type_status
from src.learning.intention_probe import probe_features
from src.learning.production_targets import production_targets
from src.learning.production_probe import fit_forecast, predict_forecast

ROOT = Path('logs/roadmap')
OUT = ROOT / 'production-forecast-probe-01'
TRAIN = ('294','870','955','839','991','523')
HELD = ('887','920','851')
config = json.loads((ROOT/'joint-professional-fit-05/configuration.json').read_text())
counts = config['vocabulary']
paths = {g:ROOT/('pro-demonstrations-production-08' if g in TRAIN else 'pro-demonstrations-07')/g for g in TRAIN+HELD}
assert not (OUT/'report.json').exists()
validated = validate_datasets([paths[g] for g in TRAIN], [paths[g] for g in HELD], missing_fields=True)
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):
    p.write_text(json.dumps(x,indent=2)+'\n')
bindings = {str(p):sha(p) for p in [Path(__file__),Path('src/learning/production_probe.py'),Path('src/learning/production_targets.py'),Path('src/learning/intention_probe.py'),Path('src/learning/entity_type_status.py'),Path('docs/superpowers/plans/2026-10-06-production-forecast-probe.md')]}
bindings.update({str(p):sha(p) for d in paths.values() for p in [d/'dataset.json',d/'static.json',d/'examples.jsonl.gz']})
parts = {'teaching': [], 'development': []}
coverage = []
names = {}
for g,d in paths.items():
    static=json.loads((d/'static.json').read_text())['game_data']
    names.update({a['ability_id']:a.get('friendly_name','') for a in static['abilities']})
    production={a for a,n in names.items() if n.startswith(('Build ','Train ','Research '))}
    production.update(u['ability_id'] for u in static['units'] if 8 in u.get('attributes',[]) and names.get(u.get('ability_id'),'').startswith('Morph'))
    receipt=json.loads((d/'dataset.json').read_text())
    unknowns={(r['event']['_gameloop'],r['event']['m_sequence']) for r in receipt['issued_command_audit']['unresolved_events']}
    with gzip.open(d/'examples.jsonl.gz','rt') as stream:
        rows=list(map(json.loads,stream))
    targets=production_targets(rows,production,unknowns)
    for i,(r,target) in enumerate(zip(rows,targets,strict=True)):
        k=(r['action_loop'],r['source_sequence'])
        future=next((s for s in rows[i:] if s['commands'][0]['ability'] in production),None)
        expected=None
        if future:
            fk=(future['action_loop'],future['source_sequence'])
            if not any(k<u<fk for u in unknowns):
                expected=dict(ability=future['commands'][0]['ability'],delay_loops=fk[0]-k[0],target_key=list(fk))
        assert expected==target
    examples=collect([d],counts,spatial=True,missing_fields=True)[0]
    assert len(examples)==len(rows)
    valid=[]
    for i,((inputs,_,_,_),target) in enumerate(zip(examples,targets,strict=True)):
        if target is None:
            continue
        state,history=probe_features(inputs,*counts[:2])
        state=hstack([state,csr_matrix(unit_type_status(inputs,counts[0]).reshape(1,-1))]).tocsr()
        valid.append((state,history,target['ability'],target['delay_loops']/22.4,g,i,tuple(target['target_key'])))
    role='teaching' if g in TRAIN else 'development'
    parts[role].extend(valid)
    coverage.append(dict(game=g,role=role,rows=len(rows),valid=len(valid),unique_targets=len({v[-1] for v in valid})))
    print(json.dumps(coverage[-1]),flush=True)
labels={}
matrices={}
for role,items in parts.items():
    labels[role]=np.array([[v[2],v[3]] for v in items])
    matrices[role]={'state':vstack([v[0] for v in items]).tocsr(),'history':vstack([v[1] for v in items]).tocsr()}
    np.save(OUT/f'{role}-labels.npy',labels[role])
    write(OUT/f'{role}-rows.json',[dict(game=v[4],row=v[5],target_key=v[6]) for v in items])
    for feature,matrix in matrices[role].items():
        save_npz(OUT/f'{role}-{feature}.npz',matrix)
majority=Counter(labels['teaching'][:,0]).most_common(1)[0][0]
mean=labels['teaching'][:,1].mean()
def metrics(truth,pred):
    result={}
    for subset,mask in [('all',np.ones(len(truth),dtype=bool)),('positive_delay',truth[:,1]>0),('nonworker',truth[:,0]!=524)]:
        actual=truth[mask]; estimate=pred[mask]
        classes=np.unique(actual[:,0])
        byclass={str(int(c)):dict(name=names[int(c)],rows=int((actual[:,0]==c).sum()),correct=int(((actual[:,0]==c)&(estimate[:,0]==c)).sum())) for c in classes}
        result[subset]=dict(rows=len(actual),accuracy=float((actual[:,0]==estimate[:,0]).mean()),macro_recall=float(np.mean([x['correct']/x['rows'] for x in byclass.values()])),delay_mae=float(np.abs(actual[:,1]-estimate[:,1]).mean()),classes=byclass)
    return result
report=dict(rl=False,controller=False,regularization=.1,bindings=bindings,validated=validated,coverage=coverage,baseline={},models={})
for role,truth in labels.items():
    pred=np.column_stack([np.full(len(truth),majority),np.full(len(truth),mean)])
    report['baseline'][role]=metrics(truth,pred)
for feature in ('state','state_history'):
    xs={r:(m['state'] if feature=='state' else hstack([m['state'],m['history']]).tocsr()) for r,m in matrices.items()}
    started=time.monotonic()
    model=fit_forecast(xs['teaching'],labels['teaching'][:,0].astype(int),labels['teaching'][:,1],regularization=.1)
    assert model['relative_residual']<1e-8
    save_npz(OUT/f'{feature}-training-values.npz',model['values'])
    np.savez(OUT/f'{feature}-model.npz',**{k:v for k,v in model.items() if k!='values'})
    scores={}
    for role,truth in labels.items():
        a,t=predict_forecast(model,xs[role]); pred=np.column_stack([a,t])
        np.save(OUT/f'{feature}-{role}-predictions.npy',pred)
        scores[role]=metrics(truth,pred)
    report['models'][feature]=dict(seconds=time.monotonic()-started,relative_residual=model['relative_residual'],active_features=len(model['columns']),metrics=scores)
    print(json.dumps(dict(model=feature,development={k:{a:b for a,b in v.items() if a!='classes'} for k,v in scores['development'].items()})),flush=True)
assert all(sha(p)==digest for p,digest in bindings.items())
write(OUT/'report.json',report)
