"""Evaluate the saved utility fit after an evaluator variable collision; no refit."""
import hashlib,json,pickle
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.special import expit
from scipy.sparse import load_npz
ROOT=Path('logs/roadmap');DATA=ROOT/'human-production-goals-02';PAIRS=ROOT/'human-production-precedence-01';OUT=ROOT/'human-production-utility-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
telemetry=json.loads((ROOT/'human-production-utility-01.fit-telemetry.json').read_text())
assert telemetry['status']=='stopped' and telemetry['returncode']==1
fit_script=ROOT/'fit_human_production_utility_01.py';assert sha(fit_script)==telemetry['script_sha256']
audit=json.loads((PAIRS/'label-verification.json').read_text())
for p,h in audit['bindings'].items():assert sha(p)==h,p
model=pickle.loads((OUT/'model.pkl').read_bytes());names=model['names'];parameter_weights=model['weights'];status=model['status'];xs={};rows_by_role={}
assert np.isfinite(parameter_weights).all() and abs(parameter_weights[-1].mean())<1e-12
x=load_npz(DATA/'teaching-state.npz');columns=np.flatnonzero(np.asarray(x.power(2).sum(axis=0)).ravel());scale=np.maximum(np.sqrt(np.asarray(x[:,columns].power(2).mean(axis=0)).ravel()),.01)
assert np.array_equal(columns,model['columns']) and np.array_equal(scale,model['scale'])
bindings={str(p):sha(p) for p in [Path(__file__),fit_script,ROOT/'human-production-utility-01.fit-telemetry.json',OUT/'model.pkl',Path('src/learning/production_utility.py'),Path('docs/superpowers/plans/2026-10-06-human-precedence-utility.md'),PAIRS/'label-verification.json']}
for role in ('teaching','development'):
 assert sha(OUT/f'{role}-pairs.json')==sha(PAIRS/f'{role}-pairs.json')
 rows_by_role[role]=json.loads((OUT/f'{role}-pairs.json').read_text());xs[role]=load_npz(DATA/f'{role}-state.npz').astype(np.float64)[:,columns].multiply(1/scale).tocsr()
 for p in (DATA/f'{role}-state.npz',OUT/f'{role}-pairs.json'):bindings[str(p)]=sha(p)
assert sorted({r[k] for r in rows_by_role['teaching'] for k in ('left','right')})==model['supported']
marker=json.loads((OUT/'optimizer-start.json').read_text());elapsed_to_checkpoint=(OUT/'model.pkl').stat().st_mtime-marker['time'];assert 0<=elapsed_to_checkpoint<600
baseline=defaultdict(lambda:[0.,0.])
for row in rows_by_role['teaching']:baseline[(row['left'],row['right'])][row['target']]+=row['weight']
scores={}
for role,x in xs.items():
 rows=rows_by_role[role];scores_matrix=x@parameter_weights[:-1]+parameter_weights[-1]
 p=expit(np.array([scores_matrix[r['row'],r['left']]-scores_matrix[r['row'],r['right']] for r in rows]))
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
report=dict(rl=False,status=status,evaluator_repaired=True,refit=False,fit_seconds=None,iterations=None,objective_calls=None,checkpoint_written_seconds_after_optimizer_marker=elapsed_to_checkpoint,configuration=dict(max_iterations=200,l2=.01,rms_floor=.01,threads=2,maxcor=10),gates=gates,offline_pass=all(gates.values()) and status!='solver_failed',scores=scores,names=names,supported=model['supported'],baseline={f'{a},{b}':v for (a,b),v in baseline.items()},bindings=bindings)
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=status,gates=gates,checkpoint_written_seconds_after_optimizer_marker=elapsed_to_checkpoint,development={k:{n:v for n,v in m.items() if n!='families'} for k,m in scores['development'].items() if k in ('all','proposal_only','proposed_building')})),flush=True)
