"""One fixed nonlinear human forecast diagnostic and independent refit."""
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import sklearn
from scipy.sparse import load_npz
from sklearn.ensemble import ExtraTreesClassifier, ExtraTreesRegressor
source=Path('logs/roadmap/production-forecast-probe-01')
out=Path('logs/roadmap/production-threshold-probe-01')
assert not out.exists()
report=json.loads((source/'report.json').read_text())
verification=json.loads((source/'verification.json').read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert verification['report_sha256']==sha(source/'report.json')
paths=[source/'report.json',source/'verification.json',Path(__file__),Path('docs/superpowers/plans/2026-10-06-production-threshold-probe.md')]
paths += [source/f'{r}-{f}' for r in ('teaching','development') for f in ('state.npz','labels.npy','rows.json')]
bindings={str(p):sha(p) for p in paths}
xs={r:load_npz(source/f'{r}-state.npz') for r in ('teaching','development')}
ys={r:np.load(source/f'{r}-labels.npy',allow_pickle=False) for r in xs}
config=dict(n_estimators=128,max_features=1.0,min_samples_leaf=4,random_state=8158,n_jobs=2)
started=time.monotonic()
a=ExtraTreesClassifier(**config,class_weight='balanced').fit(xs['teaching'],ys['teaching'][:,0].astype(int))
t=ExtraTreesRegressor(**config).fit(xs['teaching'],np.log1p(ys['teaching'][:,1]))
assert a.classes_.tolist()==np.unique(ys['teaching'][:,0]).tolist()
def metrics(y,p):
    result={}
    for name,mask in [('all',np.ones(len(y),dtype=bool)),('positive_delay',y[:,1]>0),('nonworker',y[:,0]!=524)]:
        truth=y[mask]; pred=p[mask]
        classes={str(int(c)):dict(rows=int((truth[:,0]==c).sum()),correct=int(((truth[:,0]==c)&(pred[:,0]==c)).sum())) for c in np.unique(truth[:,0])}
        result[name]=dict(rows=len(truth),accuracy=float((truth[:,0]==pred[:,0]).mean()),macro_recall=float(np.mean([v['correct']/v['rows'] for v in classes.values()])),delay_mae=float(np.abs(truth[:,1]-pred[:,1]).mean()),classes=classes)
    return result
out.mkdir()
results={}
predictions={}
for role,y in ys.items():
    pred=np.column_stack([a.predict(xs[role]),np.maximum(0,np.expm1(t.predict(xs[role])))])
    predictions[role]=pred
    np.save(out/f'{role}-predictions.npy',pred)
    results[role]=metrics(y,pred)
# Fresh estimators deterministically refit the bound teaching data.
a2=ExtraTreesClassifier(**config,class_weight='balanced').fit(xs['teaching'],ys['teaching'][:,0].astype(int))
t2=ExtraTreesRegressor(**config).fit(xs['teaching'],np.log1p(ys['teaching'][:,1]))
for role,x in xs.items():
    p=np.column_stack([a2.predict(x),np.maximum(0,np.expm1(t2.predict(x)))])
    np.testing.assert_array_equal(p[:,0],predictions[role][:,0])
    np.testing.assert_allclose(p[:,1],predictions[role][:,1],atol=1e-12,rtol=1e-12)
    # Independent aggregate metric reconstruction from saved predictions.
    saved=np.load(out/f'{role}-predictions.npy',allow_pickle=False)
    for subset,m in results[role].items():
        indexes=[i for i,row in enumerate(ys[role]) if subset=='all' or (subset=='positive_delay' and row[1]>0) or (subset=='nonworker' and row[0]!=524)]
        hits=sum(saved[i,0]==ys[role][i,0] for i in indexes)
        error=sum(abs(saved[i,1]-ys[role][i,1]) for i in indexes)
        np.testing.assert_allclose([m['accuracy'],m['delay_mae']],[hits/len(indexes),error/len(indexes)],atol=1e-12,rtol=1e-12)
        for c,v in m['classes'].items():
            eligible=[i for i in indexes if ys[role][i,0]==int(c)]
            assert v['rows']==len(eligible) and v['correct']==sum(saved[i,0]==int(c) for i in eligible)
assert all(sha(Path(p))==d for p,d in bindings.items())
receipt=dict(rl=False,controller=False,bindings=bindings,sklearn_version=sklearn.__version__,configuration=config,class_weight='balanced',seconds=time.monotonic()-started,refit_predictions_verified=True,metrics=results)
(out/'report.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({r:{s:{k:v for k,v in m.items() if k!='classes'} for s,m in ms.items()} for r,ms in results.items()}),flush=True)
