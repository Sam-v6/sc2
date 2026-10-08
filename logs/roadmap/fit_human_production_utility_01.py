"""One bounded sparse family-utility fit on verified human commitment pairs."""
import hashlib,json,pickle,time
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from scipy.sparse import load_npz
from src.learning.production_utility import utility_objective
ROOT=Path('logs/roadmap');DATA=ROOT/'human-production-goals-02';PAIRS=ROOT/'human-production-precedence-01';OUT=ROOT/'human-production-utility-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
audit=json.loads((PAIRS/'label-verification.json').read_text());assert audit['status']=='verified_original_command_labels_weights'
for p,h in audit['bindings'].items():assert sha(p)==h,p
prep=json.loads((DATA/'preparation.json').read_text())
for p,h in prep['bindings'].items():assert sha(p)==h,p
OUT.mkdir(exist_ok=False);names=prep['names'];xs={};rows_by_role={}
bindings={str(p):sha(p) for p in [Path(__file__),PAIRS/'label-verification.json',Path('src/learning/production_utility.py'),Path('docs/superpowers/plans/2026-10-06-human-precedence-utility.md')]}
for role in ('teaching','development'):
 xs[role]=load_npz(DATA/f'{role}-state.npz').astype(np.float64)
 pairfile=PAIRS/f'{role}-pairs.json';rows_by_role[role]=json.loads(pairfile.read_text());(OUT/f'{role}-pairs.json').write_bytes(pairfile.read_bytes())
 for p in (DATA/f'{role}-state.npz',pairfile):bindings[str(p)]=sha(p)
columns=np.flatnonzero(np.asarray(xs['teaching'].power(2).sum(axis=0)).ravel());scale=np.maximum(np.sqrt(np.asarray(xs['teaching'][:,columns].power(2).mean(axis=0)).ravel()),.01)
xs={role:x[:,columns].multiply(1/scale).tocsr() for role,x in xs.items()}
parameters=np.zeros((len(columns)+1,len(names)));latest=parameters.ravel().copy();pairs=rows_by_role['teaching'];rows=np.array([r['row'] for r in pairs]);left=np.array([r['left'] for r in pairs]);right=np.array([r['right'] for r in pairs]);truth=np.array([r['target'] for r in pairs]);sample=np.array([r['weight'] for r in pairs]);sample/=sample.sum();calls=0
memory=dict(parameters=latest.nbytes,estimated_lbfgs_history=latest.nbytes*22,score_matrix=xs['teaching'].shape[0]*len(names)*8)
# Estimate shape only; do not densify state in the optimizer.
memory['score_matrix']=xs['teaching'].shape[0]*len(names)*8
print(json.dumps(dict(stage='prepared',active_columns=len(columns),teaching_pairs=len(pairs),memory_bytes=memory)),flush=True)
(OUT/'optimizer-start.json').write_text(json.dumps(dict(monotonic=time.monotonic(),time=time.time()))+'\n');started=time.monotonic()
def objective(p):
 global latest,calls
 if time.monotonic()-started>=600:raise TimeoutError('Optimizer reached600seconds')
 loss,gradient=utility_objective(p,xs['teaching'],rows,left,right,truth,sample,.01,len(names))
 if not np.isfinite(loss) or not np.isfinite(gradient).all():raise ValueError('Nonfinite utility objective')
 latest=p.copy();calls+=1
 return loss,gradient
iterations=0
try:
 result=minimize(objective,latest,jac=True,method='L-BFGS-B',options=dict(maxiter=200,maxcor=10,ftol=1e-9,gtol=1e-5))
 latest=result.x;iterations=int(result.nit);status='converged' if result.success else 'iteration_bound' if result.status==1 else 'solver_failed'
except TimeoutError:status='wall_bound'
fit_seconds=time.monotonic()-started;weights=latest.reshape(parameters.shape);weights[-1]-=weights[-1].mean();assert np.isfinite(weights).all()
supported=sorted({r[k] for r in pairs for k in ('left','right')})
(OUT/'model.pkl').write_bytes(pickle.dumps(dict(kind='sparse_family_utility',weights=weights,columns=columns,scale=scale,names=names,supported=supported,status=status)))
baseline=defaultdict(lambda:[0.,0.])
for row in rows_by_role['teaching']:baseline[(row['left'],row['right'])][row['target']]+=row['weight']
scores={}
for role,x in xs.items():
 rows=rows_by_role[role];scores_matrix=x@weights[:-1]+weights[-1]
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
bindings[str(OUT/'model.pkl')]=sha(OUT/'model.pkl')
report=dict(rl=False,status=status,fit_seconds=fit_seconds,iterations=iterations,objective_calls=calls,memory_bytes=memory,configuration=dict(max_iterations=200,l2=.01,rms_floor=.01,threads=2,maxcor=10),gates=gates,offline_pass=all(gates.values()) and status!='solver_failed',scores=scores,names=names,supported=supported,baseline={f'{a},{b}':v for (a,b),v in baseline.items()},bindings=bindings)
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=status,fit_seconds=fit_seconds,gates=gates,development={k:{n:v for n,v in m.items() if n!='families'} for k,m in scores['development'].items() if k in ('all','proposal_only','proposed_building')})),flush=True)
