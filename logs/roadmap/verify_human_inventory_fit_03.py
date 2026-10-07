"""Recompute stock predictions, equal-game metrics and frozen promotion gates."""
import hashlib,json,pickle
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
OUT=Path('logs/roadmap/human-inventory-targets-03')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
report=json.loads((OUT/'fit-report.json').read_text());prep=json.loads((OUT/'preparation.json').read_text());verify=json.loads((OUT/'verification-observations.json').read_text())
for receipt in (report,prep,verify):
    for path,checksum in receipt['bindings'].items():assert sha(path)==checksum,path
failure=json.loads((OUT/'fit-wrapper-error.json').read_text())
assert failure['status']=='wrapper_error_after_checkpoint' and not failure['refit']
for path,checksum in failure['bindings'].items():assert sha(path)==checksum,path
model=pickle.loads((OUT/'model.pkl').read_bytes());names=model['names']
truth={r:np.load(OUT/f'{r}-inventory.npy') for r in ('teaching','development')};current={r:np.load(OUT/f'{r}-current.npy') for r in truth}
refs={r:json.loads((OUT/f'{r}-rows.json').read_text()) for r in truth}
xs={r:load_npz(Path(prep['feature_source'])/f'{r}-state.npz').astype(np.float32) for r in truth}
assert model['target_kind']=='future_inventory' and names==prep['names']
assert np.array_equal(model['columns'],np.flatnonzero(np.asarray(xs['teaching'].power(2).sum(axis=0)).ravel()))
assert np.allclose(model['scale'],np.maximum(truth['teaching'].std(axis=0),.1),rtol=0,atol=1e-12)
games=sorted({r['game'] for r in refs['teaching']});mean=sum(np.mean(truth['teaching'][[r['game']==g for r in refs['teaching']]],axis=0) for g in games)/len(games)
production={'Barracks','Factory','Starport','BarracksReactor','BarracksTechLab','FactoryReactor','FactoryTechLab','StarportReactor','StarportTechLab'}
other_buildings={'CommandCenter','SupplyDepot','Refinery','EngineeringBay','MissileTurret','Bunker','SensorTower','GhostAcademy','Armory','PlanetaryFortress','OrbitalCommand'}
category={n:'upgrade' if n.startswith('upgrade:') else 'workers' if n=='unit:SCV' else 'production' if n[5:] in production else 'buildings' if n[5:] in other_buildings else 'military' for n in names}
metrics={}
for label in ('persistence','mean','model'):
    metrics[label]={}
    for role in truth:
        expected=current[role].astype(float) if label=='persistence' else np.broadcast_to(mean,truth[role].shape) if label=='mean' else np.maximum(model['model'].predict(xs[role][:,model['columns']])*model['scale'],0)
        stored=np.load(OUT/f'{label}-{role}-predictions.npy');assert np.allclose(expected,stored,atol=1e-12,rtol=0)
        metrics[label][role]={}
        for group in ('all','workers','production','buildings','military','upgrade'):
            cols=[i for i,n in enumerate(names) if group=='all' or category[n]==group];scores={}
            for game in sorted({r['game'] for r in refs[role]}):
                rows=[i for i,r in enumerate(refs[role]) if r['game']==game]
                scores[game]=float(np.abs(truth[role][rows][:,cols]-stored[rows][:,cols]).mean())
                assert abs(scores[game]-report['scores'][label][role][group]['per_game'][game])<1e-12
            value=float(np.mean(list(scores.values())))
            assert abs(value-report['scores'][label][role][group]['mae'])<1e-12
            metrics[label][role][group]=value
supported=(truth['teaching']>0).any(axis=0)
gates=dict(overall_beats_persistence=metrics['model']['development']['all']<metrics['persistence']['development']['all'],overall_beats_mean=metrics['model']['development']['all']<metrics['mean']['development']['all'],production_beats_persistence=metrics['model']['development']['production']<metrics['persistence']['development']['production'],teaching_support=bool(supported.all()))
assert gates==report['gates'] and all(gates.values())==report['offline_pass']
assert dict(zip(names,map(bool,supported)))==report['supported']
receipt=dict(status='verified_inventory_fit',gates=gates,offline_pass=all(gates.values()),metrics=metrics,rows={r:len(v) for r,v in truth.items()},rl=False,bindings={str(p):sha(p) for p in [Path(__file__),OUT/'fit-report.json',OUT/'model.pkl',OUT/'fit-wrapper-error.json']+list(OUT.glob('*-predictions.npy'))})
(OUT/'fit-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(status=receipt['status'],gates=gates,offline_pass=receipt['offline_pass'],development={label:r['development'] for label,r in metrics.items()})),flush=True)
