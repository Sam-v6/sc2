"""Reload the fitted model; independently recompute outcome labels and metrics."""
from collections import Counter
import gzip,hashlib,json,pickle
from pathlib import Path
import numpy as np
import mpyq
from scipy.sparse import load_npz
from src.learning.production_outcomes import production_outcomes
from src.learning.replay_extract import replay_metadata,load_protocol
OUT=Path('logs/roadmap/human-production-goals-02')
prep=json.loads((OUT/'preparation.json').read_text()); report=json.loads((OUT/'fit-report.json').read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,digest in report['bindings'].items(): assert sha(p)==digest,p
assert prep['status']=='verified_preparation'
for p,digest in prep['bindings'].items():
    assert sha(p)==digest,p
names=prep['names']; index={n:i for i,n in enumerate(names)}; outcomes={}; source_rows={}
for coverage in prep['coverage']:
    g=coverage['game']; directory=next(Path(p).parent for p in prep['bindings'] if p.endswith(f'/{g}/dataset.json'))
    r=json.loads((directory/'dataset.json').read_text()); s=json.loads((directory/'static.json').read_text())['game_data']; a={x['ability_id']:x.get('friendly_name','') for x in s['abilities']}
    products={u['name'] for u in s['units'] if u.get('race')==1 and a.get(u.get('ability_id'),'').startswith(('Build ','Train ')) and u['name']!='AutoTurret'}
    upgrades={u['name'] for u in s['upgrades'] if a.get(u.get('ability_id'),'').startswith('Research ')}
    meta,_=replay_metadata(r['source_replay']); ar=mpyq.MPQArchive(r['source_replay']); events=list(load_protocol(int(meta['BaseBuild'][4:])).decode_replay_tracker_events(ar.read_file('replay.tracker.events')))
    outcomes[g]=production_outcomes(events,r['player']['player_info']['player_id'],products,{'OrbitalCommand','PlanetaryFortress'},upgrades)
    with gzip.open(directory/'examples.jsonl.gz','rt') as f: source_rows[g]=list(map(json.loads,f))
model=pickle.loads((OUT/'model.pkl').read_bytes()); checked=0
building={'CommandCenter','SupplyDepot','Refinery','Barracks','EngineeringBay','MissileTurret','Bunker','SensorTower','GhostAcademy','Factory','Starport','Armory','FusionCore','PlanetaryFortress','OrbitalCommand','BarracksTechLab','BarracksReactor','FactoryTechLab','FactoryReactor','StarportTechLab','StarportReactor'}
roles={n:'upgrade' if n.startswith('upgrade:') else 'economy' if n=='unit:SCV' else 'building' if n[5:] in building else 'military' for n in names}
ys={r:np.load(OUT/f'{r}-counts.npy') for r in ('teaching','development')}
for role,y in ys.items():
    rows=json.loads((OUT/f'{role}-rows.json').read_text()); reconstructed=np.zeros_like(y)
    for j,row in enumerate(rows):
        assert source_rows[row['game']][row['row']]['action_loop']==row['loop']
        for t,n in outcomes[row['game']]:
            if row['loop']<=t<row['loop']+1008: reconstructed[j,index[n]]+=1
    assert np.array_equal(y,reconstructed); checked+=len(y)
    x=load_npz(OUT/f'{role}-state.npz'); prediction=np.maximum(model['model'].predict(x[:,model['columns']])*model['scale'],0)
    for label,pred in [('model',prediction),('zero',np.zeros_like(y,dtype=float)),('mean',np.broadcast_to(ys['teaching'].mean(axis=0),y.shape))]:
        assert np.allclose(pred,np.load(OUT/f'{label}-{role}-predictions.npy'),rtol=0,atol=1e-12)
        for category,expected in report['scores'][label][role].items():
            selected=[i for i,n in enumerate(names) if category=='all' or roles[n]==category]
            tp=[]; fp=[]; fn=[]; mae=[]
            for i in selected:
                t=y[:,i]>0; p=np.rint(pred[:,i])>0
                tp.append(np.count_nonzero(t&p)); fp.append(np.count_nonzero(~t&p)); fn.append(np.count_nonzero(t&~p)); mae.append(np.abs(y[:,i]-pred[:,i]).mean())
                item=expected['per_family'][names[i]]
                assert item['positive']==int(t.sum())
                assert abs(item['precision']-tp[-1]/max(tp[-1]+fp[-1],1))<1e-12
                assert abs(item['recall']-tp[-1]/max(tp[-1]+fn[-1],1))<1e-12
                assert abs(item['mae']-mae[-1])<1e-12
            assert expected['tp']==sum(tp) and expected['fp']==sum(fp) and expected['fn']==sum(fn)
            assert abs(expected['precision']-sum(tp)/max(sum(tp)+sum(fp),1))<1e-12
            assert abs(expected['recall']-sum(tp)/max(sum(tp)+sum(fn),1))<1e-12
            assert abs(expected['mae']-np.mean(mae))<1e-12
            f1=np.mean([2*t/max(2*t+f+n,1) for t,f,n in zip(tp,fp,fn,strict=True)])
            assert abs(expected['macro_f1']-f1)<1e-12
d={n:s['development'] for n,s in report['scores'].items()}
gates=dict(baseline_f1=all(d['model']['all']['macro_f1']>d[b]['all']['macro_f1'] for b in ('zero','mean')),baseline_mae=all(d['model']['all']['mae']<d[b]['all']['mae'] for b in ('zero','mean')),building=all(d['model']['building'][k]>=.25 for k in ('precision','recall')),military=all(d['model']['military'][k]>=.25 for k in ('precision','recall')),no_unseen_development_family=not prep['unknown_development'])
assert gates==report['gates'] and all(gates.values())==report['offline_pass']
receipt=dict(status='verified',rows=checked,families=len(names),gates=gates,rl=False,bindings={str(p):sha(p) for p in [Path(__file__),OUT/'fit-report.json',OUT/'model.pkl',OUT/'preparation.json']})
(OUT/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n'); print(json.dumps(receipt),flush=True)
