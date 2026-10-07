"""One frozen inventory fit; game-balanced errors against persistence/mean."""
import hashlib,json,pickle,threading,time
from pathlib import Path
import numpy as np
import psutil
from scipy.sparse import load_npz
from sklearn.ensemble import ExtraTreesRegressor

OUT=Path('logs/roadmap/human-inventory-targets-03')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    prep=json.loads((OUT/'preparation.json').read_text())
    verify=json.loads((OUT/'verification-observations.json').read_text())
    assert verify['status']=='verified_inventory_labels' and verify['label_rows']==6354
    for receipt in (prep,verify):
        for path,checksum in receipt['bindings'].items():assert sha(path)==checksum,path
    assert not (OUT/'model.pkl').exists()
    xs={r:load_npz(Path(prep['feature_source'])/f'{r}-state.npz').astype(np.float32) for r in ('teaching','development')}
    ys={r:np.load(OUT/f'{r}-inventory.npy') for r in xs}
    current={r:np.load(OUT/f'{r}-current.npy') for r in xs}
    refs={r:json.loads((OUT/f'{r}-rows.json').read_text()) for r in xs}
    names=prep['names']; scale=np.maximum(ys['teaching'].std(axis=0),.1)
    columns=np.flatnonzero(np.asarray(xs['teaching'].power(2).sum(axis=0)).ravel())
    model=ExtraTreesRegressor(n_estimators=128,min_samples_leaf=4,max_features=1.,random_state=8160,n_jobs=2)
    begun=time.monotonic();done=threading.Event();samples=[]
    def watch():
        while not done.is_set():
            samples.append(psutil.cpu_percent(interval=1));done.wait(4)
    watcher=threading.Thread(target=watch,daemon=True);watcher.start()
    model.fit(xs['teaching'][:,columns],ys['teaching']/scale)
    seconds=time.monotonic()-begun;assert seconds<600
    done.set();watcher.join(5)
    supported=(ys['teaching']>0).any(axis=0)
    checkpoint=dict(model=model,scale=scale,columns=columns,names=names,target_kind='future_inventory',horizon_loops=1008)
    (OUT/'model.pkl').write_bytes(pickle.dumps(checkpoint))
    teaching_games=sorted({r['game'] for r in refs['teaching']})
    mean=np.mean([ys['teaching'][[r['game']==g for r in refs['teaching']]].mean(axis=0) for g in teaching_games],axis=0)
    production={'Barracks','Factory','Starport','BarracksReactor','BarracksTechLab','FactoryReactor','FactoryTechLab','StarportReactor','StarportTechLab'}
    buildings={'CommandCenter','SupplyDepot','Refinery','EngineeringBay','MissileTurret','Bunker','SensorTower','GhostAcademy','Armory','PlanetaryFortress','OrbitalCommand'}|production
    categories={n:'upgrade' if n.startswith('upgrade:') else 'workers' if n=='unit:SCV' else 'production' if n[5:] in production else 'buildings' if n[5:] in buildings else 'military' for n in names}
    scores={}
    for label in ('persistence','mean','model'):
        scores[label]={}
        for role,x in xs.items():
            pred=current[role].astype(float) if label=='persistence' else np.broadcast_to(mean,ys[role].shape) if label=='mean' else np.maximum(model.predict(x[:,columns])*scale,0)
            np.save(OUT/f'{label}-{role}-predictions.npy',pred)
            groups={}
            for category in ('all','workers','production','buildings','military','upgrade'):
                mask=np.array([category=='all' or categories[n]==category for n in names]);per_game={}
                for game in sorted({r['game'] for r in refs[role]}):
                    rows=np.array([r['game']==game for r in refs[role]])
                    per_game[game]=float(np.abs(ys[role][rows][:,mask]-pred[rows][:,mask]).mean())
                groups[category]=dict(mae=float(np.mean(list(per_game.values()))),per_game=per_game)
            scores[label][role]=groups
    gates=dict(overall_beats_persistence=scores['model']['development']['all']['mae']<scores['persistence']['development']['all']['mae'],
               overall_beats_mean=scores['model']['development']['all']['mae']<scores['mean']['development']['all']['mae'],
               production_beats_persistence=scores['model']['development']['production']['mae']<scores['persistence']['development']['production']['mae'],
               teaching_support=bool(supported.all()))
    bindings={str(p):sha(p) for p in [Path(__file__),OUT/'preparation.json',OUT/'verification-observations.json',OUT/'model.pkl',Path('docs/superpowers/plans/2026-10-06-human-inventory-fit.md')]+list(OUT.glob('*-inventory.npy'))+list(OUT.glob('*-current.npy'))}
    report=dict(status='fitted_inventory',fit_seconds=seconds,peak_cpu=max(samples or [0]),scores=scores,gates=gates,offline_pass=all(gates.values()),supported=dict(zip(names,map(bool,supported))),bindings=bindings,rl=False,configuration=dict(trees=128,leaf=4,features=1.,seed=8160,threads=2,target_scaling='teaching_std_floor_0.1',history=False))
    (OUT/'fit-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(fit_seconds=seconds,peak_cpu=report['peak_cpu'],gates=gates,development={label:value['development'] for label,value in scores.items()})),flush=True)
if __name__=='__main__':main()
