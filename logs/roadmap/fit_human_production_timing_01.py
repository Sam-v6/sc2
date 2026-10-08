"""One frozen supervised timing fit; no controller change or RL."""
import hashlib,json,pickle,time
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
from sklearn.ensemble import ExtraTreesRegressor
from src.learning.production_timing import first_delays,conditional_times
ROOT=Path('logs/roadmap');DATA=ROOT/'human-production-goals-01';OUT=ROOT/'human-production-timing-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((DATA/'preparation.json').read_text());names=prep['names'];ys={};xs={};bindings={str(p):sha(p) for p in [Path(__file__),Path('src/learning/production_timing.py'),Path('docs/superpowers/plans/2026-10-06-human-production-timing.md'),ROOT/'production-timing-audit-01/report.json']}
audit=json.loads((ROOT/'production-timing-audit-01/report.json').read_text())
for p,h in audit['bindings'].items():assert sha(p)==h,p
for role in ('teaching','development'):
    rows=json.loads((DATA/f'{role}-rows.json').read_text());outcomes={g:json.loads((DATA/f'{g}-outcomes.json').read_text()) for g in {r['game'] for r in rows}}
    count=np.load(DATA/f'{role}-counts.npy');delay=np.zeros_like(count,dtype=float)
    for i,row in enumerate(rows):
        first=first_delays(outcomes[row['game']],row['loop'],1008)
        for j,n in enumerate(names):
            independent=[t-row['loop'] for t,name in outcomes[row['game']] if name==n and row['loop']<=t<row['loop']+1008]
            assert (n in first)==(count[i,j]>0)==bool(independent)
            if independent:
                assert first[n]==min(independent)
                delay[i,j]=first[n]/1008
    presence=(count>0).astype(float);ys[role]=dict(presence=presence,delay=delay,moments=np.concatenate((presence,delay),axis=1))
    xs[role]=load_npz(DATA/f'{role}-state.npz').astype(np.float32)
    np.savez(OUT/f'{role}-targets.npz',presence=presence,delay=delay)
    for p in [DATA/f'{role}-counts.npy',DATA/f'{role}-state.npz',DATA/f'{role}-rows.json']+ [DATA/f'{g}-outcomes.json' for g in outcomes]:bindings[str(p)]=sha(p)
scale=np.maximum(ys['teaching']['moments'].std(axis=0),.1);columns=np.flatnonzero(np.asarray(xs['teaching'].power(2).sum(axis=0)).ravel())
model=ExtraTreesRegressor(n_estimators=128,min_samples_leaf=4,max_features=1.,random_state=8161,n_jobs=2)
start=time.monotonic();model.fit(xs['teaching'][:,columns],ys['teaching']['moments']/scale);seconds=time.monotonic()-start;assert seconds<600
(OUT/'model.pkl').write_bytes(pickle.dumps(dict(model=model,scale=scale,columns=columns,names=names)))
median=np.array([np.median(ys['teaching']['delay'][ys['teaching']['presence'][:,j]>0,j]) for j in range(len(names))])*45
# Explicit schema groups match the existing outcome trial.
building={'CommandCenter','SupplyDepot','Refinery','Barracks','EngineeringBay','MissileTurret','Bunker','SensorTower','GhostAcademy','Factory','Starport','Armory','FusionCore','PlanetaryFortress','OrbitalCommand','BarracksTechLab','BarracksReactor','FactoryTechLab','FactoryReactor','StarportTechLab','StarportReactor'}
groups={n:'upgrade' if n.startswith('upgrade:') else 'economy' if n=='unit:SCV' else 'building' if n[5:] in building else 'military' for n in names}
report=dict(rl=False,fit_seconds=seconds,names=names,scores={},bindings=bindings)
for role,x in xs.items():
    moments=model.predict(x[:,columns])*scale;prediction,known=conditional_times(moments[:,:len(names)],moments[:,len(names):],45)
    np.savez(OUT/f'{role}-predictions.npz',moments=moments,seconds=prediction,known=known)
    truth=ys[role]['delay']*45;positive=ys[role]['presence']>0
    count_positive=np.rint(np.load(DATA/f'model-{role}-predictions.npy'))>0
    result=dict(actual_positive_coverage=float(known[positive].mean()),count_prediction_coverage=float(known[count_positive].mean()),families={})
    for j,n in enumerate(names):
        mask=positive[:,j]
        if not mask.any():continue
        # Unknown actual-positive predictions are charged a horizon error, not dropped.
        errors=np.where(known[mask,j],abs(prediction[mask,j]-truth[mask,j]),45)
        result['families'][n]=dict(rows=int(mask.sum()),model=float(errors.mean()),median=float(abs(median[j]-truth[mask,j]).mean()),half_horizon=float(abs(22.5-truth[mask,j]).mean()))
    result['groups']={g:{label:float(np.mean([v[label] for n,v in result['families'].items() if g=='all' or groups[n]==g])) for label in ('model','median','half_horizon')} for g in ('all','economy','building','military','upgrade')}
    report['scores'][role]=result
d=report['scores']['development'];gates=dict(baselines=all(d['groups']['all']['model']<d['groups']['all'][b] for b in ('median','half_horizon')),coverage=d['count_prediction_coverage']>=.95 and d['actual_positive_coverage']>=.95,groups=all(v['model']<=v['median']+2 for k,v in d['groups'].items() if k!='all'))
report.update(gates=gates,offline_pass=all(gates.values()),teaching_medians=median.tolist())
for p,h in bindings.items():assert sha(p)==h,p
report['bindings'].update({str(OUT/'model.pkl'):sha(OUT/'model.pkl')})
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(fit_seconds=seconds,gates=gates,development={k:v for k,v in d.items() if k!='families'})),flush=True)
