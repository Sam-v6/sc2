"""Independent original-command pair labels and reloaded classifier metrics."""
import gzip,hashlib,json,pickle
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
from scipy.special import expit
ROOT=Path('logs/roadmap');DATA=ROOT/'human-production-goals-02';OUT=ROOT/'human-production-utility-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads((OUT/'report.json').read_text());prep=json.loads((DATA/'preparation.json').read_text())
for p,h in r['bindings'].items():assert sha(p)==h,p
names=r['names'];events={}
for item in prep['coverage']:
 g=item['game'];d=next(Path(p).parent for p in prep['bindings'] if p.endswith(f'/{g}/dataset.json'));s=json.loads((d/'static.json').read_text())['game_data']
 abilities={a['ability_id']:a for a in s['abilities']};types={u['unit_id']:u['name'] for u in s['units']};products={u['name']:u for u in s['units']};upgrades={u['name']:u for u in s['upgrades']}
 def canonical(a):return abilities.get(a,{}).get('remaps_to_ability_id') or a
 mapping=defaultdict(list)
 for name in names:
  kind,n=name.split(':',1);native=(products if kind=='unit' else upgrades)[n];mapping[canonical(native['ability_id'])].append(name)
 events[g]=[]
 with gzip.open(d/'examples.jsonl.gz','rt') as f:
  for line in f:
   row=json.loads(line);c=row['original_command'];matches=mapping[canonical(c['ability'])]
   if len(matches)>1:
    own={u['tag']:types[u['unit_type']] for u in row['observation']['units'] if u['alliance']==1}
    parents={own[t] for t in c['units'] if t in own}
    matches=[n for n in matches if any(abilities[products[n[5:]]['ability_id']].get('friendly_name','').endswith(' '+p) for p in parents)]
   if len(matches)==1:events[g].append((row['action_loop'],row['source_sequence'],matches[0]))
model=pickle.loads((OUT/'model.pkl').read_bytes());baseline=defaultdict(lambda:[0.,0.]);checked=0
for role in ('teaching','development'):
 rows=json.loads((OUT/f'{role}-pairs.json').read_text());anchors=json.loads((DATA/f'{role}-rows.json').read_text());x=load_npz(DATA/f'{role}-state.npz').astype(np.float32);count_predictions=np.load(DATA/f'model-{role}-predictions.npy')
 frequencies=Counter((v['game'],tuple(v['source_pair'][0] or (-1,-1)),tuple(v['source_pair'][1] or (-1,-1)),v['left'],v['right']) for v in rows);totals=Counter()
 for v in rows:
  key=(v['game'],tuple(v['source_pair'][0] or (-1,-1)),tuple(v['source_pair'][1] or (-1,-1)),v['left'],v['right']);totals[v['game']]+=1/frequencies[key]
 for v in rows:
  anchor=anchors[v['row']];assert anchor['game']==v['game'] and anchor['loop']==v['loop'];first={}
  for t,seq,n in events[v['game']]:
   if v['loop']<=t<v['loop']+1008:first[n]=min(first.get(n,(t,seq)),(t,seq))
  a=first.get(names[v['left']]);b=first.get(names[v['right']]);assert [list(a) if a else None,list(b) if b else None]==v['source_pair']
  ta=a[0] if a else v['loop']+1008;tb=b[0] if b else v['loop']+1008;assert ta!=tb and int(ta<tb)==v['target']
  assert v['proposal_only']==bool(np.rint(count_predictions[v['row'],v['left']])>0 and np.rint(count_predictions[v['row'],v['right']])>0)
  key=(v['game'],tuple(v['source_pair'][0] or (-1,-1)),tuple(v['source_pair'][1] or (-1,-1)),v['left'],v['right']);assert abs(v['weight']-1/frequencies[key]/totals[v['game']])<1e-12
  if role=='teaching':baseline[(v['left'],v['right'])][v['target']]+=v['weight']
 n=len(rows);state=x[:,model['columns']].multiply(1/model['scale']).tocsr();utilities=state@model['weights'][:-1]+model['weights'][-1]
 p=expit(np.array([utilities[v['row'],v['left']]-utilities[v['row'],v['right']] for v in rows]))
 assert np.allclose(p,np.load(OUT/f'{role}-probabilities.npy'),atol=1e-12,rtol=0)
 truth=np.array([v['target'] for v in rows]);w=np.array([v['weight'] for v in rows]);majority=np.array([baseline.get((v['left'],v['right']),[0.,0.])[1]>baseline.get((v['left'],v['right']),[0.,0.])[0] for v in rows]);proposed=np.array([v['proposal_only'] for v in rows])
 building_names={'CommandCenter','SupplyDepot','Refinery','Barracks','Factory','Starport','EngineeringBay','Armory','GhostAcademy','FusionCore','Bunker','MissileTurret','SensorTower','OrbitalCommand','PlanetaryFortress'}
 building_mask=np.array([any(names[v[k]].removeprefix('unit:') in building_names or names[v[k]].endswith(('TechLab','Reactor')) for k in ('left','right')) for v in rows])
 for label,mask in [('all',np.ones(n,bool)),('proposal_only',proposed),('proposed_building',proposed&building_mask)]:
  expected=r['scores'][role][label];assert expected['pairs']==int(mask.sum())
  for key,val in [('accuracy',np.average((p[mask]>=.5)==truth[mask],weights=w[mask])),('majority_accuracy',np.average(majority[mask]==truth[mask],weights=w[mask])),('brier',np.average((p[mask]-truth[mask])**2,weights=w[mask]))]:assert abs(expected[key]-val)<1e-12
  family_scores=[];majority_scores=[]
  for i,name in enumerate(names):
   selected=mask&np.array([v['left']==i or v['right']==i for v in rows])
   if not selected.any():continue
   f=r['scores'][role][label]['families'][name];assert f['pairs']==int(selected.sum())
   a=float(np.average((p[selected]>=.5)==truth[selected],weights=w[selected]));b=float(np.average(majority[selected]==truth[selected],weights=w[selected]));assert abs(f['model']-a)<1e-12 and abs(f['majority']-b)<1e-12
   family_scores.append(a);majority_scores.append(b)
  assert abs(expected['macro_family_accuracy']-np.mean(family_scores))<1e-12 and abs(expected['majority_macro_family_accuracy']-np.mean(majority_scores))<1e-12
 checked+=n
assert {f'{a},{b}':v for (a,b),v in baseline.items()}==r['baseline']
d=r['scores']['development']['proposal_only'];b=r['scores']['development']['proposed_building']
gates=dict(proposal_support=d['pairs']>=200,accuracy=d['accuracy']>max(.5,d['majority_accuracy']),macro_family=d['macro_family_accuracy']>d['majority_macro_family_accuracy'],building=b['accuracy']>=.65)
assert gates==r['gates'] and (all(gates.values()) and r['status']!='solver_failed')==r['offline_pass']
assert model['status']==r['status'] and np.isfinite(model['weights']).all()
assert sorted({v[k] for v in json.loads((OUT/'teaching-pairs.json').read_text()) for k in ('left','right')})==model['supported']
receipt=dict(status='verified_labels_predictions_metrics_gates',pairs=checked,rl=False,offline_pass=r['offline_pass'],gates=gates,limits=['Offline command precedence is not native production or game competence.'],bindings={str(p):sha(p) for p in [Path(__file__),OUT/'report.json',OUT/'model.pkl',OUT/'teaching-pairs.json',OUT/'development-pairs.json']})
(OUT/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
