"""Reconstruct frozen canary predictions, dispatch accounting and birth labels."""
import gzip,hashlib,json,pickle
from collections import Counter
from pathlib import Path
import numpy as np
from src.learning.production_goal_policy import current_features,predict_goals
from src.learning.actor_selection import construction_products
ROOT=Path('logs/roadmap');OUT=ROOT/'human-goal-native-01'
r=json.loads((OUT/'canary/episode.json').read_text());sup=json.loads((OUT/'canary.supervision.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,h in sup['bindings'].items():
    # The native plan was clarified before panel launch, with no controller change.
    if not p.endswith('human-production-goals-native.md'):assert sha(p)==h,p
model=pickle.loads(Path(r['job']['model']).read_bytes());profile=json.loads(Path(r['job']['profile']).read_text());static=json.loads((OUT/'canary/static.json').read_text());products=construction_products(static)
with gzip.open(OUT/'canary/trace.jsonl.gz','rt') as f:rows=list(map(json.loads,f))
ack=Counter();codes=Counter();births=[];seen={};units={u['unit_id']:u['name'] for u in static['units']}
for i,row in enumerate(rows):
    goals,counts=predict_goals(model,current_features(row['observation'],r['job']['vocabulary'],products,profile))
    assert goals==row['goals'] and np.allclose(counts,row['raw_counts'],atol=1e-12,rtol=0)
    assert len(row['results'])==len(row['execution'])+len(row['assistance'])
    for item,code in zip(row['execution'],row['results'],strict=False):
        if code==1:ack[item['goal']]+=1
    codes.update(map(str,row['results']))
    for unit in row['observation']['units']:
        if unit['alliance']!=1:continue
        name='unit:'+units[unit['unit_type']];old=seen.get(unit['tag'])
        if i and name in model['names'] and (old is None or (old!=unit['unit_type'] and name in ('unit:OrbitalCommand','unit:PlanetaryFortress'))):
            births.append(dict(loop=row['observation']['game_loop'],goal=name,tag=unit['tag']))
        seen[unit['tag']]=unit['unit_type']
assert dict(ack)==r['acknowledged'] and dict(codes)==r['results']
assert births==r['production']  # No upgrades completed in this engineering canary.
assert r['frames']==len(rows) and not r['rl'] and not r['training']
receipt=dict(status='verified_engineering',frames=len(rows),acknowledged=dict(ack),production=dict(Counter(x['goal'] for x in births)),competence=False,rl=False,bindings={str(p):sha(p) for p in [Path(__file__),OUT/'canary/episode.json',OUT/'canary/trace.jsonl.gz',OUT/'canary.supervision.json']})
(OUT/'canary-verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
