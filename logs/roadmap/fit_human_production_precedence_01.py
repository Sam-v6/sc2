"""One bounded original-command precedence fit; no native promotion or RL."""
import gzip,hashlib,json,pickle,time
from collections import Counter,defaultdict
from itertools import combinations
from pathlib import Path
import numpy as np
from scipy.sparse import hstack,load_npz,vstack,csr_matrix
from sklearn.ensemble import ExtraTreesClassifier
from src.learning.production_execution import goal_catalog,order_goals,canonical
from src.learning.production_precedence import next_commitments,precedence_target
ROOT=Path('logs/roadmap'); DATA=ROOT/'human-production-goals-02'; OUT=ROOT/'human-production-precedence-01'
OUT.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
verify=json.loads((DATA/'verification.json').read_text());assert verify['status']=='verified'
for p,h in verify['bindings'].items():assert sha(p)==h,p
prep=json.loads((DATA/'preparation.json').read_text())
for p,h in prep['bindings'].items():assert sha(p)==h,p
count_model=pickle.loads((DATA/'model.pkl').read_bytes())
names=prep['names'];index={n:i for i,n in enumerate(names)}
bindings={str(p):sha(p) for p in [Path(__file__),DATA/'verification.json',Path('src/learning/production_precedence.py'),Path('docs/superpowers/plans/2026-10-06-human-production-precedence.md')]}
events={};uncertain={}
for coverage in prep['coverage']:
 g=coverage['game'];d=next(Path(p).parent for p in prep['bindings'] if p.endswith(f'/{g}/dataset.json'))
 static=json.loads((d/'static.json').read_text())['game_data'];catalog={a['ability_id']:a for a in static['abilities']};unit_names={u['unit_id']:u['name'] for u in static['units']};goals=goal_catalog(static,names)
 relevant={canonical(info['ability'],catalog) for info in goals.values()};events[g]=[];uncertain[g]=[]
 with gzip.open(d/'examples.jsonl.gz','rt') as f:source=list(map(json.loads,f))
 for row in source:
  c=row['original_command'];a=c['ability']
  if a<=0:uncertain[g].append(row['action_loop']);continue
  if canonical(a,catalog) not in relevant:continue
  own={u['tag']:u for u in row['observation']['units'] if u['alliance']==1};resolved=set()
  for tag in c['units']:
   if tag in own:
    u=dict(own[tag],orders=[dict(ability_id=a)]);resolved.update(n for n,_ in order_goals(u,goals,catalog,unit_names))
  if len(resolved)==1:events[g].append((row['action_loop'],row['source_sequence'],next(iter(resolved))))
  else:uncertain[g].append(row['action_loop'])
 for p in (d/'static.json',d/'examples.jsonl.gz'):bindings[str(p)]=sha(p)
xs={};rows_by_role={};rng=np.random.default_rng(8162)
for role in ('teaching','development'):
 x=load_npz(DATA/f'{role}-state.npz').astype(np.float32);anchors=json.loads((DATA/f'{role}-rows.json').read_text());counts=np.load(DATA/f'model-{role}-predictions.npy')
 assert np.allclose(counts,np.maximum(count_model['model'].predict(x[:,count_model['columns']])*count_model['scale'],0),rtol=0,atol=1e-12)
 pairs_by_game=defaultdict(list);censored=0
 for row_i,row in enumerate(anchors):
  g=row['game'];loop=row['loop']
  if any(loop<=t<loop+1008 for t in uncertain[g]):censored+=1;continue
  first=next_commitments(events[g],loop,1008);proposed={names[i] for i in np.flatnonzero(np.rint(counts[row_i])>0)};support=sorted(proposed|set(first))
  for a,b in combinations(support,2):
   y=precedence_target(first,a,b)
   if y is None:continue
   # Independent scalar label reconstruction from original command timeline.
   ta=min((t for t,seq,n in events[g] if n==a and loop<=t<loop+1008),default=loop+1008)
   tb=min((t for t,seq,n in events[g] if n==b and loop<=t<loop+1008),default=loop+1008)
   assert ta!=tb and int(ta<tb)==y
   pairs_by_game[g].append(dict(row=row_i,game=g,loop=loop,left=index[a],right=index[b],target=y,proposal_only=a in proposed and b in proposed,source_pair=[first.get(a),first.get(b)]))
 selected=[]
 games=sorted(pairs_by_game);quota=50000//len(games)
 for g in games:
  values=pairs_by_game[g]
  if role=='teaching' and len(values)>quota:values=[values[i] for i in sorted(rng.choice(len(values),quota,replace=False))]
  frequency=Counter((tuple(v['source_pair'][0] or (-1,-1)),tuple(v['source_pair'][1] or (-1,-1)),v['left'],v['right']) for v in values)
  for v in values:
   key=(tuple(v['source_pair'][0] or (-1,-1)),tuple(v['source_pair'][1] or (-1,-1)),v['left'],v['right']);v['weight']=1/frequency[key]
  total=sum(v['weight'] for v in values)
  for v in values:v['weight']/=total
  selected.extend(values)
 rows_by_role[role]=selected;idx=np.array([v['row'] for v in selected]);left=np.array([v['left'] for v in selected]);right=np.array([v['right'] for v in selected]);n=len(selected)
 identities=csr_matrix((np.ones(2*n), (np.repeat(np.arange(n),2),np.column_stack((left,len(names)+right)).ravel())),shape=(n,2*len(names)))
 xs[role]=hstack([x[idx],identities]).tocsr()
 (OUT/f'{role}-pairs.json').write_text(json.dumps(selected)+'\n')
 for p in (DATA/f'{role}-state.npz',DATA/f'{role}-rows.json',DATA/f'model-{role}-predictions.npy'):bindings[str(p)]=sha(p)
 print(json.dumps(dict(stage='pairs',role=role,pairs=n,censored_anchors=censored)),flush=True)
width=xs['teaching'].shape[1]-2*len(names)
x=xs['teaching'];mirror=hstack([x[:,:width],x[:,width+len(names):],x[:,width:width+len(names)]]).tocsr()
y=np.array([r['target'] for r in rows_by_role['teaching']]);w=np.array([r['weight'] for r in rows_by_role['teaching']]);columns=np.flatnonzero(np.asarray(vstack([x,mirror]).power(2).sum(axis=0)).ravel())
model=ExtraTreesClassifier(n_estimators=128,min_samples_leaf=4,max_features=1.,random_state=8162,n_jobs=2)
start=time.monotonic();model.fit(vstack([x,mirror])[:,columns],np.r_[y,1-y],sample_weight=np.r_[w,w]);fit_seconds=time.monotonic()-start;assert fit_seconds<600
(OUT/'model.pkl').write_bytes(pickle.dumps(dict(model=model,columns=columns,names=names,state_width=width)))
baseline=defaultdict(lambda:[0.,0.])
for row in rows_by_role['teaching']:baseline[(row['left'],row['right'])][row['target']]+=row['weight']
scores={}
for role,x in xs.items():
 mirror=hstack([x[:,:width],x[:,width+len(names):],x[:,width:width+len(names)]]).tocsr()
 p=(model.predict_proba(x[:,columns])[:,1]+1-model.predict_proba(mirror[:,columns])[:,1])/2
 np.save(OUT/f'{role}-probabilities.npy',p)
 rows=rows_by_role[role];truth=np.array([r['target'] for r in rows]);pred=(p>=.5);bp=np.array([baseline.get((r['left'],r['right']),[0.,0.])[1]>baseline.get((r['left'],r['right']),[0.,0.])[0] for r in rows]);weights=np.array([r['weight'] for r in rows])
 def measures(mask):
  if not mask.any():return dict(pairs=0)
  accuracy=lambda v:float(np.average(v[mask]==truth[mask],weights=weights[mask]))
  family={}
  for i,name in enumerate(names):
   m=mask&np.array([r['left']==i or r['right']==i for r in rows])
   if m.any():family[name]=dict(pairs=int(m.sum()),model=float(np.average(pred[m]==truth[m],weights=weights[m])),majority=float(np.average(bp[m]==truth[m],weights=weights[m])))
  return dict(pairs=int(mask.sum()),accuracy=accuracy(pred),majority_accuracy=accuracy(bp),brier=float(np.average((p[mask]-truth[mask])**2,weights=weights[mask])),macro_family_accuracy=float(np.mean([v['model'] for v in family.values()])),majority_macro_family_accuracy=float(np.mean([v['majority'] for v in family.values()])),families=family)
 proposed=np.array([r['proposal_only'] for r in rows]);building={'CommandCenter','SupplyDepot','Refinery','Barracks','Factory','Starport','EngineeringBay','Armory','GhostAcademy','FusionCore','Bunker','MissileTurret','SensorTower','OrbitalCommand','PlanetaryFortress'}
 buildings=np.array([any(names[r[k]].removeprefix('unit:') in building or names[r[k]].endswith(('TechLab','Reactor')) for k in ('left','right')) for r in rows])
 game_scores={g:measures(proposed&np.array([r['game']==g for r in rows])) for g in sorted({r['game'] for r in rows})}
 scores[role]=dict(per_game=game_scores,all=measures(np.ones(len(rows),bool)),proposal_only=measures(proposed),proposed_building=measures(proposed&buildings),unknown_baseline_pairs=sum((r['left'],r['right']) not in baseline for r in rows))
d=scores['development']['proposal_only'];b=scores['development']['proposed_building'];gates=dict(proposal_support=d['pairs']>=200,accuracy=d['accuracy']>max(.5,d['majority_accuracy']),macro_family=d['macro_family_accuracy']>d['majority_macro_family_accuracy'],building=b.get('accuracy',0)>=.65)
for p,h in bindings.items():assert sha(p)==h,p
bindings[str(OUT/'model.pkl')]=sha(OUT/'model.pkl')
report=dict(rl=False,fit_seconds=fit_seconds,gates=gates,offline_pass=all(gates.values()),scores=scores,names=names,baseline={f'{a},{b}':v for (a,b),v in baseline.items()},bindings=bindings)
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(fit_seconds=fit_seconds,gates=gates,development={k:{n:v for n,v in m.items() if n!='families'} if isinstance(m,dict) else m for k,m in scores['development'].items()})),flush=True)
