"""Reconstruct learned forecasts, primitive ownership and production accounting."""
import gzip, hashlib, json, pickle
from collections import Counter
from pathlib import Path
import numpy as np
from src.learning.production_goal_policy import current_features, predict_goals
from src.learning.actor_selection import construction_products
from src.learning.production_execution import goal_catalog
ROOT=Path('logs/roadmap'); OUT=ROOT/'human-goal-native-03'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads((OUT/'canary/episode.json').read_text()); sup=json.loads((OUT/'canary.supervision.json').read_text())
assert sup['result']['status'] in ('completed','truncated'),sup['result']['status']
for p,h in sup['bindings'].items(): assert sha(p)==h,p
assert sha(r['job']['model'])==r['model_sha256']
model=pickle.loads(Path(r['job']['model']).read_bytes()); profile=json.loads(Path(r['job']['profile']).read_text())
static=json.loads((OUT/'canary/static.json').read_text()); products=construction_products(static)
goals_catalog=goal_catalog(static,model['names']); units={u['unit_id']:u['name'] for u in static['units']}
with gzip.open(OUT/'canary/trace.jsonl.gz','rt') as f: rows=list(map(json.loads,f))
ack=Counter(); codes=Counter(); requests=Counter(); births=[]; seen={}; upgrades=set(); forecasts=0; micro=0
for row in rows:
    assert len(row['results'])==len(row['execution'])+len(row['assistance'])
    commands=[e['command'] for e in row['execution']]+row['assistance']
    actors=[tag for c in commands for tag in c['units']]
    assert len(actors)==len(set(actors)),('actor overwritten',row['observation']['game_loop'])
    protected={p['actor'] for p in row['pending'].values()}
    assert not protected.intersection(tag for c in row['assistance'] for tag in c['units'])
    codes.update(map(str,row['results']))
    if row['phase']=='micro':
        micro+=1
        assert row['goals'] is None and row['execution']==[]
        continue
    assert row['phase']=='forecast'
    goals,counts=predict_goals(model,current_features(row['observation'],r['job']['vocabulary'],products,profile))
    assert goals==row['goals'] and np.allclose(counts,row['raw_counts'],atol=1e-12,rtol=0)
    requests.update(goals)
    for item,code in zip(row['execution'],row['results'],strict=False):
        assert item['goal'] in goals
        assert item['command']['ability']==goals_catalog[item['goal']]['ability']
        if code==1: ack[item['goal']]+=1
    for unit in row['observation']['units']:
        if unit['alliance']!=1: continue
        name='unit:'+units[unit['unit_type']]; old=seen.get(unit['tag'])
        if forecasts and name in model['names'] and (old is None or (old!=unit['unit_type'] and name in ('unit:OrbitalCommand','unit:PlanetaryFortress'))):
            births.append(dict(loop=row['observation']['game_loop'],goal=name,tag=unit['tag']))
        seen[unit['tag']]=unit['unit_type']
    for goal,info in goals_catalog.items():
        u=info['upgrade']
        if u is not None and u in row['observation']['upgrades'] and u not in upgrades:
            births.append(dict(loop=row['observation']['game_loop'],goal=goal)); upgrades.add(u)
    forecasts+=1
assert dict(ack)==r['acknowledged'] and dict(codes)==r['results'] and dict(requests)==r['requested']
assert births==r['production']
assert r['frames']==forecasts and micro>0 and not r['rl'] and not r['training']
receipt=dict(status='verified_engineering',forecast_frames=forecasts,micro_frames=micro,acknowledged=dict(ack),production=dict(Counter(x['goal'] for x in births)),competence=False,rl=False,bindings={str(p):sha(p) for p in [Path(__file__),OUT/'canary/episode.json',OUT/'canary/trace.jsonl.gz',OUT/'canary.supervision.json']})
(OUT/'canary-verification.json').write_text(json.dumps(receipt,indent=2)+'\n'); print(json.dumps(receipt),flush=True)
