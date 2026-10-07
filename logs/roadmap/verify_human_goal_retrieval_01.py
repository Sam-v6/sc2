"""Independent distance, source, hold and target checks for retrieval audit."""
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from src.learning.replay_extract import replay_metadata
ROOT=Path('logs/roadmap');OUT=ROOT/'human-goal-retrieval-01';SOURCE=ROOT/'human-inventory-targets-03'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
audit=json.loads((OUT/'audit.json').read_text())
for p,h in audit['bindings'].items():assert sha(p)==h,p
names=json.loads((SOURCE/'preparation.json').read_text())['names'];ix={n:i for i,n in enumerate(names)}
teacher_refs=json.loads((SOURCE/'teaching-rows.json').read_text());current=np.load(SOURCE/'teaching-current.npy');targets=np.load(SOURCE/'teaching-inventory.npy')
race_audit=json.loads((SOURCE/'opponent-race-audit.json').read_text());races={}
for g in race_audit['games']:
    assert sha(g['source_replay'])==g['source_sha256']
    metadata,_=replay_metadata(g['source_replay'])
    # Teacher is Terran, and audit already ties its player to imported data. The
    # public race list must agree without using AssignedRace for selection.
    expected=sorted([g['teacher_selected_race'],g['opponent_selected_race']])
    assert sorted(p['SelectedRace'] for p in metadata['Players'])==expected
    races[g['game']]=g['opponent_selected_race']
x=np.column_stack([np.array([r['loop'] for r in teacher_refs])/22.4,current[:,ix['unit:SCV']],current[:,ix['unit:CommandCenter']]])
scale=np.maximum(np.std(x,axis=0),1);assert np.array_equal(scale,audit['scales'])
indices={race:np.array([i for i,r in enumerate(teacher_refs) if races[r['game']]==race]) for race in ['Prot','Terr','Zerg']};indices['unknown']=np.arange(len(x))
def distances(query,ids):return np.sqrt(sum(((x[ids,k]-query[k])/scale[k])**2 for k in range(3)))
for race,ids in indices.items():
    nearest=[float(distances(x[i],ids[[teacher_refs[j]['game']!=teacher_refs[i]['game'] for j in ids]]).min()) for i in ids]
    assert abs(float(np.percentile(nearest,95))-audit['thresholds'][race])<1e-12
refs=json.loads((SOURCE/'development-rows.json').read_text());dc=np.load(SOURCE/'development-current.npy');dy=np.load(SOURCE/'development-inventory.npy');pred=np.load(OUT/'development-predictions.npy');report=json.loads((OUT/'development-retrievals.json').read_text())
for i,(ref,r) in enumerate(zip(refs,report,strict=True)):
    ids=indices[races[ref['game']]];d=distances([ref['loop']/22.4,dc[i,ix['unit:SCV']],dc[i,ix['unit:CommandCenter']]],ids);j=int(ids[np.argmin(d)])
    assert r['query']==ref, (i,ref,r)
    source_index=teacher_refs.index(r['source'])
    assert source_index in ids and abs(float(distances([ref['loop']/22.4,dc[i,ix['unit:SCV']],dc[i,ix['unit:CommandCenter']]],np.array([source_index]))[0])-float(d.min()))<1e-12, (i,ref,r)
    # Equivalent arithmetic can choose either row at a numerical distance tie.
    # Verify the implementation's deterministic first-index rule separately.
    normalized=x[ids]/scale-np.array([ref['loop']/22.4,dc[i,ix['unit:SCV']],dc[i,ix['unit:CommandCenter']]])/scale
    j=int(ids[np.argmin(np.sum(normalized*normalized,axis=1))])
    assert source_index==j and r['future_loop']==teacher_refs[j]['loop']+1008
    assert abs(r['distance']-float(d.min()))<1e-12 and r['supported']==(d.min()<=audit['thresholds'][races[ref['game']]])
    assert np.array_equal(pred[i],targets[j])
for r in audit['development']:
    mask=np.array([ref['game']==r['game'] for ref in refs]);assert abs(np.abs(pred[mask]-dy[mask]).mean()-r['mean_absolute_error'])<1e-12
native=ROOT/'human-production-cadence-native-01/D';static=json.loads((native/'static.json').read_text());unitnames={u['unit_id']:u['name'] for u in static['units']}
with gzip.open(native/'trace.jsonl.gz','rt') as f:rows=[r for r in map(json.loads,f) if r['phase']=='forecast']
retrievals=json.loads((OUT/'native-retrievals.json').read_text());held=None;expires=-1
for row,r in zip(rows,retrievals,strict=True):
    state=row['observation'];loop=state['game_loop'];own={u['tag']:u for u in state.get('owned_memory',[])};own.update({u['tag']:u for u in state['units'] if u['alliance']==1})
    workers=sum(unitnames[u['unit_type']]=='SCV' for u in own.values());bases=sum(unitnames[u['unit_type']] in ('CommandCenter','CommandCenterFlying','OrbitalCommand','OrbitalCommandFlying','PlanetaryFortress') for u in own.values())
    if held is None or loop>=expires:
        ids=indices[audit['native_public_selected_race']];d=distances([loop/22.4,workers,bases],ids)
        normalized=x[ids]/scale-np.array([loop/22.4,workers,bases])/scale
        held=int(ids[np.argmin(np.sum(normalized*normalized,axis=1))])
        assert abs(float(distances([loop/22.4,workers,bases],np.array([held]))[0])-float(d.min()))<1e-12
        expires=loop+1008
    assert r['source']==teacher_refs[held] and r['goal_expires']==expires and r['loop']==loop, (loop,workers,bases,r['source'],teacher_refs[held],r['goal_expires'],expires)
    assert r['target']=={n:int(targets[held,i]) for i,n in enumerate(names) if targets[held,i]>0}
receipt=dict(status='verified_human_goal_retrieval',teaching_rows=len(x),development_rows=len(refs),native_forecasts=len(rows),rl=False,training=False,bindings={str(p):sha(p) for p in [Path(__file__),OUT/'audit.json',OUT/'development-predictions.npy',OUT/'development-retrievals.json',OUT/'native-retrievals.json',OUT/'library.npz',OUT/'library-rows.json']})
(OUT/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
