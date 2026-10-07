"""Bounded frozen feature/context separability probes, never deployed."""
import hashlib
import json
import os
from pathlib import Path
import time
import warnings

import numpy as np
import scipy
from scipy.optimize import linprog, OptimizeWarning

from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect, validate_datasets

read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=Path('logs/roadmap')
experiment=root/'professional-small-set-nonlinear-01'
output=root/'professional-actor-separability-01'
assert not output.exists()
assert os.environ.get('OPENBLAS_NUM_THREADS')==os.environ.get('OMP_NUM_THREADS')=='2'
contract=read(experiment/'contract.json')
comparison=read(experiment/'comparison.json')
assert sha(experiment/'contract.json')==comparison['contract_sha256']
checkpoint=experiment/'baseline/policy.npz'
assert sha(checkpoint)==comparison['checkpoint_sha256']['baseline']
policy,_=JointEntityPolicy.load(checkpoint)
assert policy.actor_geometry and policy.actor_cutoff and not policy.actor_nonlinear
configuration=read(root/'joint-professional-fit-05/configuration.json')
paths=[Path(s['dataset']) for s in contract['sources']]
assert validate_datasets(paths,[],missing_fields=True)==contract['sources']
for path,h in contract['code_sha256'].items():assert sha(Path(path))==h
rows={}
for directory in paths:
    examples,_=collect([directory],configuration['vocabulary'],spatial=True,missing_fields=True)
    for selected in contract['selected']:
        if selected['game']==directory.name:
            x,y,command,_=examples[selected['row']]
            assert y is not None and command.ability==selected['ability']
            rows[(selected['game'],selected['row'])]=(x,y)
probe_contract=dict(parent_contract_sha256=sha(experiment/'contract.json'),checkpoint_sha256=sha(checkpoint),
                    sources=contract['sources'],selected=contract['selected'],code_sha256=contract['code_sha256'],
                    helper_sha256=sha(Path(__file__)),runtime=dict(numpy=np.__version__,scipy=scipy.__version__,solver_threads=1,blas_threads=2,device='cpu'),
                    coefficient_bound=1,per_row_seconds=2,per_row_total_seconds=90,shared_seconds=45,
                    scope='Frozen teaching-row diagnostic oracles only. No deployment, native games, other replay predictions or RL.')
output.mkdir()
(output/'contract.json').write_text(json.dumps(probe_contract,indent=2)+'\n')
def solve(features,sign,seconds):
    # -sign*score + margin <=0; maximize margin with bounded score coefficients.
    matrix=np.column_stack((-sign[:,None]*features,np.ones(len(sign))))
    objective=np.zeros(features.shape[1]+1);objective[-1]=-1
    start=time.monotonic()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore',category=OptimizeWarning,message='Unrecognized options detected.*')
        result=linprog(objective,A_ub=matrix,b_ub=np.zeros(len(sign)),
                       bounds=[(-1,1)]*features.shape[1]+[(0,None)],method='highs',
                       options=dict(threads=1,time_limit=seconds,primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9))
    receipt=dict(status=int(result.status),message=result.message,seconds=time.monotonic()-start)
    if result.x is not None:
        achieved=float(np.min(sign*(features@result.x[:-1])))
        receipt.update(solver_margin=float(result.x[-1]),achieved_margin=achieved,
                       positive_margin_verified=achieved>1e-7,
                       coefficients_sha256=hashlib.sha256(result.x[:-1].tobytes()).hexdigest())
        assert achieved>=result.x[-1]-1e-7
    return receipt
records=[];shared=[];signs=[];original_exact=0;start=time.monotonic()
weights=np.concatenate((policy.heads['actor'],policy.heads['actor_geometry'],policy.heads['actor_cutoff'][:,None]),axis=1).ravel()
for selected in contract['selected']:
    x,y=rows[(selected['game'],selected['row'])]
    scores,cache=policy._forward(x,ability=y['ability'],actors=tuple(y['actors']))
    eligible=np.flatnonzero(x['actor_mask'])
    feature=np.column_stack((cache['entities'][eligible],cache['actor_geometry'][eligible],np.ones(len(eligible)))).astype(np.float64)
    sign=np.where(np.isin(eligible,y['actors']),1.,-1.)
    joint=np.einsum('h,nf->nhf',cache['conditioned'].astype(np.float64),feature).reshape(len(feature),-1)
    np.testing.assert_allclose(joint@weights,scores['actor'][eligible],atol=2e-5,rtol=2e-5)
    shared.append(joint);signs.append(sign)
    collision=any(np.array_equal(a,b) for a in feature[sign>0] for b in feature[sign<0])
    exact=set(policy.predict(x)['actors'])==set(y['actors']);original_exact+=exact
    remaining=90-(time.monotonic()-start)
    probe=solve(feature,sign,min(2,remaining)) if remaining>0 else dict(status='total_wall_bound')
    records.append(dict(**selected,eligible=len(eligible),gold_count=int((sign>0).sum()),
                        original_exact=exact,opposite_label_feature_collision=collision,probe=probe))
assert original_exact==comparison['predicted']['baseline']['actors']
shared_probe=solve(np.concatenate(shared),np.concatenate(signs),45)
for path,h in contract['code_sha256'].items():assert sha(Path(path))==h
assert validate_datasets(paths,[],missing_fields=True)==contract['sources']
assert sha(checkpoint)==probe_contract['checkpoint_sha256']
receipt=dict(status='completed',contract_sha256=sha(output/'contract.json'),rows=records,shared_probe=shared_probe,
             original_exact=original_exact,independent_positive_margin_rows=sum(r['probe'].get('positive_margin_verified',False) for r in records),
             opposite_label_collision_rows=sum(r['opposite_label_feature_collision'] for r in records),
             bindings_unchanged=True,deployed_policy_updates=0,native_games=0,rl_updates=0)
(output/'report.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='rows'},indent=2))
