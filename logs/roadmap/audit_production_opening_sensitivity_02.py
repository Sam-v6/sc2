"""Descriptive frozen-model input intervention; no fit or native causality claim."""
import copy,gzip,hashlib,json,pickle
from pathlib import Path
from src.learning.production_goal_policy import current_features,predict_goals
from src.learning.actor_selection import construction_products
root=Path('logs/roadmap'); out=root/'human-goal-native-03'; game=out/'canary'
with gzip.open(game/'trace.jsonl.gz','rt') as f: opening=json.loads(next(f))['observation']
static=json.loads((game/'static.json').read_text()); products=construction_products(static)
episode=json.loads((game/'episode.json').read_text()); job=episode['job']; model=pickle.loads(Path(job['model']).read_bytes()); profile=json.loads(Path(job['profile']).read_text())
rows=[]
for loop in (0,240,480,912,1200,2400,3408):
 for minerals in (50,100,150):
  state=copy.deepcopy(opening);state['game_loop']=loop
  if 'decision_loop' in state: state['decision_loop']=loop
  state['player']['minerals']=minerals
  goals,counts=predict_goals(model,current_features(state,job['vocabulary'],products,profile))
  rows.append(dict(loop=loop,minerals=minerals,goals=goals,counts={n:float(v) for n,v in zip(model['names'],counts) if n in ('unit:SupplyDepot','unit:Barracks','unit:Refinery','unit:SCV')}))
paths=[Path(__file__),Path(job['model']),Path(job['profile']),game/'trace.jsonl.gz',game/'static.json',Path('src/learning/production_goal_policy.py'),Path('src/learning/intention_probe.py')]
r=dict(status='verified_descriptive_intervention',rl=False,meaning='Only time and mineral inputs vary; remaining opening state is held fixed. These states need not be physically reachable.',rows=rows,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
(out/'opening-sensitivity.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(rows),flush=True)
