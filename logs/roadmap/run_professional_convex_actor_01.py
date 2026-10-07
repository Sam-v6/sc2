"""Frozen-feature actor optimizer comparison on human teaching rows."""
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np
import scipy
from scipy.optimize import minimize

from src.learning.entity_audit import audit_commands
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect, validate_datasets

read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=Path('logs/roadmap')
experiment=root/'professional-small-set-nonlinear-01'
output=root/'professional-convex-actor-01'
assert not output.exists()
assert os.environ.get('OPENBLAS_NUM_THREADS')==os.environ.get('OMP_NUM_THREADS')=='2'
contract=read(experiment/'contract.json')
comparison=read(experiment/'comparison.json')
assert sha(experiment/'contract.json')==comparison['contract_sha256']
checkpoint=experiment/'baseline/policy.npz'
assert sha(checkpoint)==comparison['checkpoint_sha256']['baseline']
policy,_=JointEntityPolicy.load(checkpoint)
assert policy.actor_geometry and policy.actor_cutoff and not policy.actor_nonlinear
configuration_path=root/'joint-professional-fit-05/configuration.json'
configuration_sha256=sha(configuration_path)
assert configuration_sha256==read(root/'professional-small-set-01/contract.json')['parent_configuration_sha256']
configuration=read(configuration_path)
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
            rows[(selected['game'],selected['row'])]=(x,y,command,None)

examples=[rows[(r['game'],r['row'])] for r in contract['selected']]
initial=np.concatenate((policy.heads['actor'],policy.heads['actor_geometry'],policy.heads['actor_cutoff'][:,None]),axis=1).astype(np.float64).ravel()
blocks=[];labels=[];slices=[];expected_loss=0.;expected_gradient=[];offset=0;logit_error=0.
for x,y,_,_ in examples:
    scores,c=policy._forward(x,ability=y['ability'],actors=tuple(y['actors']))
    eligible=np.flatnonzero(x['actor_mask'])
    f=np.column_stack((c['entities'][eligible],c['actor_geometry'][eligible],np.ones(len(eligible)))).astype(np.float64)
    z=np.einsum('h,nf->nhf',c['conditioned'].astype(np.float64),f).reshape(len(f),-1)
    blocks.append(z);gold=np.isin(eligible,y['actors']).astype(float);labels.append(gold)
    slices.append(slice(offset,offset+len(gold)));offset+=len(gold)
    logits=scores['actor'][eligible]
    np.testing.assert_allclose(z@initial,logits,atol=2e-5,rtol=2e-5)
    logit_error=max(logit_error,float(np.abs(z@initial-logits).max()))
    expected_loss+=float(np.mean(np.logaddexp(0,logits)-gold*logits)+np.log(np.exp(logits-logits.max()).sum())+logits.max()-logits[gold.astype(bool)].mean()-np.log(gold.sum()))/62
    _,g=policy.loss_and_gradients(x,y)
    expected_gradient.append(np.concatenate((g['actor'],g['actor_geometry'],g['actor_cutoff'][:,None]),axis=1).ravel())
z=np.concatenate(blocks);gold=np.concatenate(labels)
def objective(weights):
    assert np.isfinite(weights).all()
    logits=z@weights;delta=np.empty_like(logits);loss=0.
    for section in slices:
        a=logits[section];g=gold[section];shifted=np.exp(a-a.max());prob=shifted/shifted.sum()
        loss+=np.mean(np.logaddexp(0,a)-g*a)+np.log(shifted.sum())+a.max()-a[g.astype(bool)].mean()-np.log(g.sum())
        delta[section]=(np.exp(-np.logaddexp(0,-a))-g)/len(g)+prob-g/g.sum()
    gradient=z.T@delta/62
    assert np.isfinite(loss) and np.isfinite(gradient).all()
    return float(loss/62),gradient
initial_loss,gradient=objective(initial)
assert abs(initial_loss-expected_loss)<1e-5
np.testing.assert_allclose(gradient,np.mean(expected_gradient,axis=0),atol=2e-5,rtol=2e-5)
rng=np.random.default_rng(8103);fd=[]
for index in rng.choice(len(initial),8,replace=False):
    high=initial.copy();low=initial.copy();high[index]+=.001;low[index]-=.001
    numerical=(objective(high)[0]-objective(low)[0])/.002
    error=abs(numerical-gradient[index]);assert error<1e-7;fd.append(error)
original=audit_commands(policy,examples)
assert original['predicted']==comparison['predicted']['baseline']
probe_contract=dict(parent_contract_sha256=sha(experiment/'contract.json'),parent_checkpoint_sha256=sha(checkpoint),
                    sources=contract['sources'],selected=contract['selected'],code_sha256=contract['code_sha256'],helper_sha256=sha(Path(__file__)),
                    collection_configuration=str(configuration_path.absolute()),collection_configuration_sha256=configuration_sha256,original_logit_max_error=logit_error,
                    runtime=dict(numpy=np.__version__,scipy=scipy.__version__,blas_threads=2,device='cpu'),
                    cache_sha256=hashlib.sha256(z.tobytes()+gold.tobytes()).hexdigest(),initial_objective=initial_loss,
                    original_gradient_max_error=float(np.max(np.abs(gradient-np.mean(expected_gradient,axis=0)))),finite_difference_max_error=max(fd),
                    iterations_max=250,optimizer_seconds_max=120,adam_rate=.001,scope='Frozen features and other heads, same existing actor loss; teaching62only. No native, other replay predictions, GPU, LP initialization or RL.')
output.mkdir();(output/'contract.json').write_text(json.dumps(probe_contract,indent=2)+'\n')
reports={}
class WallBound(Exception):pass
for name in ('adam','lbfgs'):
    start=time.monotonic();weights=initial.copy();evaluations=0;iterations=0;history=[];best=initial.copy();best_loss=initial_loss
    def evaluate(w):
        global evaluations,best,best_loss
        if time.monotonic()-start>=120:raise WallBound
        value,g=objective(w);evaluations+=1
        if value<best_loss:best=w.copy();best_loss=value
        return value,g
    status='completed';solver_status=None;message=None
    try:
        if name=='adam':
            m=np.zeros_like(weights);v=np.zeros_like(weights)
            for step in range(1,251):
                value,g=evaluate(weights);g*=min(1.,5/max(np.linalg.norm(g),1e-8))
                m=.9*m+.1*g;v=.999*v+.001*g*g
                weights-=.001*(m/(1-.9**step))/(np.sqrt(v/(1-.999**step))+1e-8)
                iterations=step
                if step%25==0:history.append(dict(iteration=step,objective=objective(weights)[0]))
        else:
            def callback(w):
                global iterations
                iterations+=1
                if time.monotonic()-start>=120:raise WallBound
                if iterations%25==0:history.append(dict(iteration=iterations,objective=objective(w)[0]))
            result=minimize(evaluate,initial.copy(),jac=True,method='L-BFGS-B',callback=callback,
                            options=dict(maxiter=250,maxls=20,gtol=1e-8,ftol=1e-12))
            weights=result.x;solver_status=int(result.status);message=str(result.message)
            iterations=int(result.nit)
            if not result.success:status='iteration_bound' if result.status==1 else 'solver_stopped'
    except WallBound:
        status='wall_bound';weights=best.copy()
    seconds=time.monotonic()-start
    assert np.isfinite(weights).all()
    candidate,_=JointEntityPolicy.load(checkpoint);before={k:v.copy() for k,v in candidate.parameters.items()}
    h=candidate.heads['actor'].shape[0];matrix=weights.reshape(h,h+5)
    candidate.heads['actor'][:]=matrix[:,:h];candidate.heads['actor_geometry'][:]=matrix[:,h:h+4];candidate.heads['actor_cutoff'][:]=matrix[:,-1]
    for k,v in before.items():
        if k not in ('actor','actor_geometry','actor_cutoff'):np.testing.assert_array_equal(v,candidate.parameters[k])
    assert all(np.isfinite(v).all() for v in candidate.parameters.values())
    run=output/name;run.mkdir();candidate.save(run/'policy.npz',dict(contract=probe_contract,optimizer=name,status=status))
    loaded,_=JointEntityPolicy.load(run/'policy.npz')
    final=audit_commands(candidate,examples);assert final==audit_commands(loaded,examples)
    command_rows=[];resolved=[];newly_wrong=[]
    for selected,(x,y,_,_) in zip(contract['selected'],examples):
        prediction=candidate.predict(x);assert prediction==loaded.predict(x)
        previous=policy.predict(x)
        gold_set=set(y['actors']);before_exact=set(previous['actors'])==gold_set;after_exact=set(prediction['actors'])==gold_set
        if not before_exact and after_exact:resolved.append(selected)
        if before_exact and not after_exact:newly_wrong.append(selected)
        scores=candidate.scores(x,ability=prediction['ability'])['actor'];eligible=np.flatnonzero(x['actor_mask']);negative=[i for i in eligible if int(i) not in gold_set]
        margin=float(min(scores[list(gold_set)])-max(scores[negative])) if negative else None
        signed=min(float(min(scores[list(gold_set)])),float(-max(scores[negative]))) if negative else float(min(scores[list(gold_set)]))
        command_rows.append(dict(**selected,prediction=prediction,original_prediction=previous,gold_actors=sorted(gold_set),actor_margin=margin,minimum_signed_actor_score=signed))
    actual=np.concatenate((loaded.heads['actor'],loaded.heads['actor_geometry'],loaded.heads['actor_cutoff'][:,None]),axis=1).astype(np.float64).ravel()
    report=dict(status=status,solver_status=solver_status,message=message,iterations=iterations,evaluations=evaluations,optimizer_seconds=seconds,
                initial_objective=initial_loss,final_objective=objective(actual)[0],parameter_norm=float(np.linalg.norm(actual)),parameter_max=float(np.abs(actual).max()),
                initial_parameter_norm=float(np.linalg.norm(initial)),initial_parameter_max=float(np.abs(initial).max()),
                checkpoint_sha256=sha(run/'policy.npz'),history=history,final=final,command_rows=command_rows,resolved=resolved,newly_wrong=newly_wrong,frozen_parameters_unchanged=True,reloaded_predictions_match=True)
    (run/'report.json').write_text(json.dumps(report,indent=2)+'\n');reports[name]=report
    print(json.dumps(dict(optimizer=name,status=status,iterations=iterations,evaluations=evaluations,seconds=seconds,objective=report['final_objective'],predicted=final['predicted'])),flush=True)
for path,h in contract['code_sha256'].items():assert sha(Path(path))==h
assert validate_datasets(paths,[],missing_fields=True)==contract['sources']
assert sha(checkpoint)==probe_contract['parent_checkpoint_sha256']
assert sha(configuration_path)==configuration_sha256
summary=dict(status='completed',contract_sha256=sha(output/'contract.json'),bindings_unchanged=True,
             gates={name:dict(actors=r['final']['predicted']['actors']>=56,complete=r['final']['predicted']['complete']>=56,ability=r['final']['predicted']['ability']==62,target=r['final']['predicted']['target']>=59) for name,r in reports.items()},
             promoted=False,native_games=0,rl_updates=0)
(output/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
