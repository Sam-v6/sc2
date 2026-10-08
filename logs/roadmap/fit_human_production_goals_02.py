"""One CPU-only simultaneous human production outcome fit; RL is off."""
import hashlib, json, pickle, time
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
from sklearn.ensemble import ExtraTreesRegressor

OUT=Path('logs/roadmap/human-production-goals-02')
prep=json.loads((OUT/'preparation.json').read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert prep['status']=='verified_preparation'
for path,digest in prep['bindings'].items():assert sha(path)==digest,path
assert not (OUT/'fit-report.json').exists()
xs={r:load_npz(OUT/f'{r}-state.npz').astype(np.float32) for r in ('teaching','development')}
ys={r:np.load(OUT/f'{r}-counts.npy') for r in xs}
names=prep['names']; scale=np.maximum(ys['teaching'].std(axis=0),.1)
columns=np.flatnonzero(np.asarray(xs['teaching'].power(2).sum(axis=0)).ravel())
model=ExtraTreesRegressor(n_estimators=128,min_samples_leaf=4,max_features=1.,random_state=8160,n_jobs=2)
started=time.monotonic(); model.fit(xs['teaching'][:,columns],ys['teaching']/scale)
fit_seconds=time.monotonic()-started
assert fit_seconds<600
(OUT/'model.pkl').write_bytes(pickle.dumps(dict(model=model,scale=scale,columns=columns,names=names)))
mean=ys['teaching'].mean(axis=0)
def metrics(truth,prediction):
    positive=np.rint(np.maximum(prediction,0))>0; actual=truth>0
    def group(mask):
        t=actual[:,mask]; p=positive[:,mask]; tp=(t&p).sum(axis=0); fp=(~t&p).sum(axis=0); fn=(t&~p).sum(axis=0)
        precision=tp/np.maximum(tp+fp,1); recall=tp/np.maximum(tp+fn,1)
        return dict(tp=int(tp.sum()),fp=int(fp.sum()),fn=int(fn.sum()),precision=float(tp.sum()/max((tp+fp).sum(),1)),recall=float(tp.sum()/max((tp+fn).sum(),1)),macro_f1=float(np.mean(2*tp/np.maximum(2*tp+fp+fn,1))),mae=float(np.abs(truth[:,mask]-prediction[:,mask]).mean()),per_family={names[i]:dict(positive=int(actual[:,i].sum()),precision=float(precision[j]),recall=float(recall[j]),mae=float(np.abs(truth[:,i]-prediction[:,i]).mean())) for j,i in enumerate(np.flatnonzero(mask))})
    building_names={'CommandCenter','SupplyDepot','Refinery','Barracks','EngineeringBay','MissileTurret','Bunker','SensorTower','GhostAcademy','Factory','Starport','Armory','FusionCore','PlanetaryFortress','OrbitalCommand','BarracksTechLab','BarracksReactor','FactoryTechLab','FactoryReactor','StarportTechLab','StarportReactor'}
    categories={n:'upgrade' if n.startswith('upgrade:') else 'economy' if n=='unit:SCV' else 'building' if n[5:] in building_names else 'military' for n in names}
    return {category:group(np.array([category=='all' or categories[n]==category for n in names])) for category in ('all','economy','building','military','upgrade')}
report=dict(rl=False,fit_seconds=fit_seconds,configuration=dict(trees=128,leaf=4,features=1.,seed=8160,threads=2,target_scaling='teaching_std_floor_0.1',history=False),scores={})
for label in ('zero','mean','model'):
    report['scores'][label]={}
    for role,x in xs.items():
        pred=np.zeros_like(ys[role],dtype=float) if label=='zero' else np.broadcast_to(mean,ys[role].shape) if label=='mean' else np.maximum(model.predict(x[:,columns])*scale,0)
        np.save(OUT/f'{label}-{role}-predictions.npy',pred)
        report['scores'][label][role]=metrics(ys[role],pred)
development={label:s['development'] for label,s in report['scores'].items()}
gates=dict(baseline_f1=all(development['model']['all']['macro_f1']>development[b]['all']['macro_f1'] for b in ('zero','mean')),baseline_mae=all(development['model']['all']['mae']<development[b]['all']['mae'] for b in ('zero','mean')),building=all(development['model']['building'][k]>=.25 for k in ('precision','recall')),military=all(development['model']['military'][k]>=.25 for k in ('precision','recall')),no_unseen_development_family=not prep['unknown_development'])
report['gates']=gates; report['offline_pass']=all(gates.values())
report['bindings']={str(p):sha(p) for p in [Path(__file__),OUT/'preparation.json',OUT/'model.pkl',Path('docs/superpowers/plans/2026-10-06-human-primitives-imitation.md')]+list(OUT.glob('*-state.npz'))+list(OUT.glob('*-counts.npy'))}
(OUT/'fit-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(fit_seconds=fit_seconds,gates=gates,development={n:{c:{k:v for k,v in m.items() if k!='per_family'} for c,m in s.items()} for n,s in development.items()})),flush=True)
