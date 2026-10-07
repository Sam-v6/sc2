"""Frozen teacher-only nearest-example diagnostic; no fitting or native tuning."""
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from src.learning.production_inventory import observation_stock

ROOT = Path('logs/roadmap')
SOURCE = ROOT / 'human-inventory-targets-03'
OUT = ROOT / 'human-goal-retrieval-01'
OUT.mkdir(exist_ok=False)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep = json.loads((SOURCE/'preparation.json').read_text())
verification = json.loads((SOURCE/'verification-observations.json').read_text())
assert verification['status'] == 'verified_inventory_labels'
for p,h in verification['bindings'].items(): assert sha(p) == h, p
names = prep['names']; ix = {n:i for i,n in enumerate(names)}
races = {g['game']:g['opponent_selected_race'] for g in json.loads((SOURCE/'opponent-race-audit.json').read_text())['games']}
roles = {}
for role in ['teaching','development']:
    refs = json.loads((SOURCE/f'{role}-rows.json').read_text())
    stock = np.load(SOURCE/f'{role}-current.npy')
    targets = np.load(SOURCE/f'{role}-inventory.npy')
    descriptor = np.array([[r['loop']/22.4, stock[i,ix['unit:SCV']], stock[i,ix['unit:CommandCenter']]] for i,r in enumerate(refs)])
    roles[role] = dict(refs=refs, stock=stock, targets=targets, descriptor=descriptor)
t = roles['teaching']; scale = np.maximum(t['descriptor'].std(axis=0),1)
z = t['descriptor']/scale
cohorts = {race:np.array([i for i,r in enumerate(t['refs']) if races[r['game']] == race]) for race in sorted(set(races.values()))}
cohorts['unknown'] = np.arange(len(z))
thresholds = {}
for race,indices in cohorts.items():
    distances = []
    for i in indices:
        other = indices[[t['refs'][j]['game'] != t['refs'][i]['game'] for j in indices]]
        assert len(other)
        distances.append(float(np.sqrt(((z[other]-z[i])**2).sum(axis=1).min())))
    thresholds[race] = float(np.percentile(distances,95))
def retrieve(descriptor,race):
    indices = cohorts.get(race,cohorts['unknown'])
    d2 = ((z[indices]-np.array(descriptor)/scale)**2).sum(axis=1)
    at = int(np.argmin(d2)); i = int(indices[at]); distance = float(np.sqrt(d2[at]))
    return i,distance,distance<=thresholds.get(race,thresholds['unknown'])
reports=[]; predictions=[]
d = roles['development']
for i,r in enumerate(d['refs']):
    j,distance,supported = retrieve(d['descriptor'][i],races[r['game']])
    predictions.append(t['targets'][j])
    reports.append(dict(query=r, source=t['refs'][j], future_loop=t['refs'][j]['loop']+1008, selected_race=races[r['game']], distance=distance,supported=supported))
predictions=np.array(predictions)
np.save(OUT/'development-predictions.npy',predictions)
(OUT/'development-retrievals.json').write_text(json.dumps(reports)+'\n')
production=[ix['unit:'+n] for n in ['Barracks','Factory','Starport']]
game_reports=[]
for game in dict.fromkeys(r['game'] for r in d['refs']):
    mask=np.array([r['game']==game for r in d['refs']])
    game_reports.append(dict(game=game, rows=int(mask.sum()), supported_fraction=float(np.mean([reports[i]['supported'] for i in np.flatnonzero(mask)])), mean_absolute_error=float(np.abs(predictions[mask]-d['targets'][mask]).mean()), production_error=float(np.abs(predictions[mask][:,production]-d['targets'][mask][:,production]).mean())))
# Audit saved native states without reading hidden opponent race: the protocol is
# known Zerg, but prove the opponent requested it from public replay metadata.
from src.learning.replay_extract import replay_metadata
native=ROOT/'human-production-cadence-native-01/D'
meta,_=replay_metadata(native/'game.SC2Replay')
with gzip.open(native/'trace.jsonl.gz','rt') as stream: rows=list(map(json.loads,stream))
player=rows[0]['observation']['player']['player_id']
opponent=next(p for p in meta['Players'] if p['PlayerID']!=player)
race=opponent['SelectedRace']
static=json.loads((native/'static.json').read_text())
held=None; expires=-1; native_reports=[]
for row in rows:
    if row['phase']!='forecast':continue
    state=row['observation']; stock=observation_stock(state,static); loop=state['game_loop']
    if held is None or loop>=expires:
        held,distance,supported=retrieve([loop/22.4,stock['unit:SCV'],stock['unit:CommandCenter']],race)
        expires=loop+1008
    target=t['targets'][held]; ref=t['refs'][held]
    native_reports.append(dict(loop=loop, source=ref, future_loop=ref['loop']+1008, source_sha256=sha(SOURCE/'teaching-inventory.npy'), supported=supported,distance=distance,goal_expires=expires,current_production={names[i]:stock[names[i]] for i in production},target_production={names[i]:int(target[i]) for i in production},target={n:int(target[i]) for i,n in enumerate(names) if target[i]>0}))
late=[r for r in native_reports if r['loop']>=300*22.4]
late_capacity=bool(late and all(sum(r['target_production'].values())>sum(r['current_production'].values()) for r in late))
(OUT/'native-retrievals.json').write_text(json.dumps(native_reports)+'\n')
np.savez_compressed(OUT/'library.npz',descriptor=t['descriptor'],targets=t['targets'],scale=scale)
(OUT/'library-rows.json').write_text(json.dumps(t['refs'])+'\n')
report=dict(status='audited_human_goal_retrieval', training=False,rl=False,rows=len(t['refs']),scales=scale.tolist(),thresholds=thresholds,development=game_reports,native_public_selected_race=race,native_late_more_capacity_every_forecast=late_capacity,native_late_supported_fraction=float(np.mean([r['supported'] for r in late])),native_final=native_reports[-1],bindings={str(p):sha(p) for p in [Path(__file__),SOURCE/'preparation.json',SOURCE/'verification-observations.json',SOURCE/'opponent-race-audit.json',SOURCE/'teaching-inventory.npy',SOURCE/'teaching-current.npy',SOURCE/'teaching-rows.json',SOURCE/'development-inventory.npy',SOURCE/'development-current.npy',SOURCE/'development-rows.json',native/'trace.jsonl.gz',native/'static.json',native/'game.SC2Replay']})
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
