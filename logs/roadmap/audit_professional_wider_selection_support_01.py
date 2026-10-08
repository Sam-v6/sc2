"""Bounded, independent frozen-teaching feature probes; never deployed."""
import hashlib
import json
import os
from pathlib import Path
import time
import warnings

import numpy as np
import scipy
from scipy.optimize import linprog,OptimizeWarning

root=Path('logs/roadmap/professional-wider-actor-01');output=Path('logs/roadmap/professional-wider-selection-support-01')
assert not output.exists()
assert os.environ.get('OPENBLAS_NUM_THREADS')==os.environ.get('OMP_NUM_THREADS')=='2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
comparison=read(root/'comparison.json');parent=read(root/'contract.json');report=read(root/'lbfgs/report.json')
assert sha(root/'contract.json')==comparison['contract_sha256']
assert sha(root/'cache.npz')==comparison['cache_archive_sha256']
assert sha(root/'lbfgs/policy.npz')==report['checkpoint_sha256']
meta=[x for x in report['commands'] if x['game']!='774' and x['exclusion'] is None]
with np.load(root/'cache.npz',allow_pickle=False) as archive:cache={k:archive[k] for k in archive.files}
assert len(meta)==len(cache['starts'])==4510
assert len({(x['game'],x['row']) for x in meta})==4510
assert not any(x['game'] in ('774','848','51483','51886') for x in meta)
contract=dict(parent_contract_sha256=sha(root/'contract.json'),cache_sha256=sha(root/'cache.npz'),checkpoint_sha256=report['checkpoint_sha256'],parent_report_sha256=sha(root/'lbfgs/report.json'),helper_sha256=sha(Path(__file__)),selected=[dict(game=x['game'],row=x['row'],ability=x['ability']) for x in meta],runtime=dict(numpy=np.__version__,scipy=scipy.__version__,solver_threads=1,blas_threads=2,device='cpu'),coefficient_bound=1,per_row_seconds=2,total_seconds=90,positive_margin_threshold=1e-7,scope='Independent frozen teaching-row queries only, no shared policy or extra predictions/native/RL.')
output.mkdir();(output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
coefficients=np.full((4510,cache['features'].shape[1]),np.nan)
records=[];start=time.monotonic()
for i,(begin,end) in enumerate(zip(cache['starts'],[*cache['starts'][1:],len(cache['gold'])])):
    f=cache['features'][begin:end];gold=cache['gold'][begin:end];sign=2*gold-1
    assert gold.sum()==len(meta[i]['gold_actors'])
    remaining=90-(time.monotonic()-start)
    record=dict(**contract['selected'][i],eligible=len(gold),gold_count=int(gold.sum()),actual_actor_exact=set(meta[i]['prediction']['actors'])==set(meta[i]['gold_actors']))
    if remaining<=0:record['status']='total_wall_bound'
    else:
        a=np.column_stack((-sign[:,None]*f,np.ones(len(sign))));objective=np.zeros(f.shape[1]+1);objective[-1]=-1
        tick=time.monotonic()
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',category=OptimizeWarning,message='Unrecognized options detected.*')
            result=linprog(objective,A_ub=a,b_ub=np.zeros(len(sign)),bounds=[(-1,1)]*f.shape[1]+[(0,None)],method='highs',options=dict(threads=1,time_limit=min(2,remaining),primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9))
        record.update(status=int(result.status),message=result.message,seconds=time.monotonic()-tick)
        if result.x is not None:
            weights=result.x[:-1];assert np.isfinite(weights).all() and np.max(np.abs(weights))<=1+1e-8
            achieved=float(min(sign*(f@weights)));assert achieved>=result.x[-1]-1e-7
            coefficients[i]=weights
            record.update(solver_margin=float(result.x[-1]),achieved_margin=achieved,positive_margin_verified=achieved>1e-7)
    records.append(record)
    if (i+1)%1000==0:print(json.dumps(dict(rows=i+1,elapsed=time.monotonic()-start,positive=sum(r.get('positive_margin_verified',False) for r in records))),flush=True)
np.savez_compressed(output/'coefficients.npz',weights=coefficients)
summary={name:dict(rows=0,positive=0,optimal_near_zero=0,nonterminal=0,actual_exact=0) for name in ('singleton','group')}
for r in records:
    s=summary['singleton' if r['gold_count']==1 else 'group'];s['rows']+=1;s['actual_exact']+=r['actual_actor_exact']
    if r.get('positive_margin_verified'):s['positive']+=1
    elif r['status']==0:s['optimal_near_zero']+=1
    else:s['nonterminal']+=1
assert sha(root/'cache.npz')==contract['cache_sha256'] and sha(root/'lbfgs/report.json')==contract['parent_report_sha256']
receipt=dict(status='completed',contract_sha256=sha(output/'contract.json'),coefficients_sha256=sha(output/'coefficients.npz'),elapsed_seconds=time.monotonic()-start,summary=summary,rows=records,policy_updates=0,native_games=0,rl_updates=0)
(output/'report.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='rows'},indent=2))
