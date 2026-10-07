"""One bounded full-corpus frozen-feature human actor optimization comparison."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import scipy

from src.learning.entity_actor_fit import actor_cache, actor_objective, actor_weights, fit_actor_heads
from src.learning.entity_audit import audit_commands
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect, validate_datasets

root=Path('logs/roadmap');output=root/'professional-wider-actor-01'
assert not output.exists()
watchdog_path=Path(os.environ['SC2_ACTOR_WATCHDOG'])
watchdog_hash=hashlib.sha256(watchdog_path.read_bytes()).hexdigest()
assert os.environ.get('OPENBLAS_NUM_THREADS')==os.environ.get('OMP_NUM_THREADS')=='2'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
configuration_path=root/'joint-professional-fit-05/configuration.json'
configuration_hash=sha(configuration_path);configuration=read(configuration_path)
parent_path=root/'joint-professional-fit-05/policy.npz';parent_report=read(parent_path.parent/'report.json')
parent_hash=sha(parent_path);assert parent_hash==parent_report['checkpoint_sha256']
assert parent_report['status']=='completed'
parent,_=JointEntityPolicy.load(parent_path)
assert parent.actor_cutoff and parent.refinement and not parent.actor_geometry and not parent.actor_nonlinear and not parent.actor_count
teach=[Path(s['dataset']) for s in configuration['sources'] if s['role']=='teaching']
diagnostic=[Path(s['dataset']) for s in configuration['sources'] if s['role']=='diagnostic']
assert len(teach)==9 and [p.name for p in diagnostic]==['774']
assert not any(p.name in ('848','51483','51886') for p in teach+diagnostic)
for source in configuration['sources']:
    for path,h in source['bindings'].items():assert sha(Path(path))==h
sources=validate_datasets(teach,diagnostic,missing_fields=True)
code={p:sha(Path(p)) for p in configuration['code_before']}
extra=Path('src/learning/entity_actor_fit.py').absolute();code[str(extra)]=sha(extra)
started=time.monotonic();games={}
for directory in teach+diagnostic:
    games[directory.name]=collect([directory],configuration['vocabulary'],spatial=True,missing_fields=True)[0]
    print(json.dumps(dict(stage='loaded',game=directory.name,commands=len(games[directory.name]))),flush=True)
all_teaching=[e for p in teach for e in games[p.name]];fitting=[(x,y) for x,y,_,_ in all_teaching if y is not None]
assert len(all_teaching)==4513 and len(fitting)==4510 and len(games['774'])==292

def derivative():
    policy,_=JointEntityPolicy.load(parent_path)
    policy.actor_geometry=True
    policy.heads['actor_geometry']=np.zeros((policy.heads['actor'].shape[0],4),np.float32)
    return policy
baseline=derivative();original_predictions={}
for game,examples in games.items():
    original_predictions[game]=[parent.predict(x) for x,_,_,_ in examples]
    assert original_predictions[game]==[baseline.predict(x) for x,_,_,_ in examples]
initial_teaching=audit_commands(baseline,all_teaching)
initial_diagnostic=audit_commands(baseline,games['774'])
assert initial_teaching['predicted']==parent_report['teaching']['predicted']
assert initial_diagnostic['predicted']==parent_report['validation']['predicted']
initial_per_game={p.name:audit_commands(baseline,games[p.name])['predicted'] for p in teach}
cache=actor_cache(baseline,fitting)
assert len(cache['contexts'])==4510
initial_weights=actor_weights(baseline);initial_loss=actor_objective(initial_weights,cache)[0]
cache_hash=hashlib.sha256()
for key,value in cache.items():cache_hash.update(key.encode());cache_hash.update(value.tobytes())
contract=dict(sources=sources,code_sha256=code,helper_sha256=sha(Path(__file__)),parent_checkpoint_sha256=parent_hash,
              collection_configuration=str(configuration_path.absolute()),collection_configuration_sha256=configuration_hash,
              initial_teaching=initial_teaching,initial_diagnostic=initial_diagnostic,initial_per_game=initial_per_game,
              initial_prediction_parity=True,initial_actor_objective=initial_loss,
              cache_sha256=cache_hash.hexdigest(),cache_shapes={k:list(v.shape) for k,v in cache.items()},
              cache_bytes=sum(v.nbytes for v in cache.values()),dense_outer_product_bytes=int(len(cache['gold'])*initial_weights.size*8),
              watchdog=dict(path=str(watchdog_path),sha256=watchdog_hash,telemetry='logs/roadmap/professional-wider-actor-01.telemetry.json'),
              runtime=dict(executable=sys.executable,numpy=np.__version__,scipy=scipy.__version__,device='cpu',blas_threads=2),
              iterations_max=250,optimizer_seconds_max=300,adam_rate=.001,
              gates=dict(teaching_actors_min=2546,teaching_complete_min=1277,teaching_games_improved_min=7,
                         diagnostic_actors_min=73,diagnostic_complete_min=24,diagnostic_targets_min=62),
              scope='Nine human teaching games, reused774diagnostic only after each frozen fit; no reserved predictions, native games, GPU or RL.')
assert sha(configuration_path)==configuration_hash
for path,h in code.items():assert sha(Path(path))==h
output.mkdir();(output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
np.savez_compressed(output/'cache.npz',**cache)
print(json.dumps(dict(stage='preflight_passed',cache_bytes=contract['cache_bytes'],dense_bytes=contract['dense_outer_product_bytes'],initial_actor_objective=initial_loss)),flush=True)
reports={}
for optimizer in ('adam','lbfgs'):
    policy=derivative();before={k:v.copy() for k,v in policy.parameters.items()}
    np.testing.assert_array_equal(actor_weights(policy),initial_weights)
    report=fit_actor_heads(policy,cache,optimizer=optimizer,iterations=250,seconds=300)
    for key,value in before.items():
        if key not in ('actor','actor_geometry','actor_cutoff'):np.testing.assert_array_equal(value,policy.parameters[key])
    run=output/optimizer;run.mkdir();policy.save(run/'policy.npz',dict(contract=contract,optimizer=optimizer,status=report['status']))
    loaded,_=JointEntityPolicy.load(run/'policy.npz')
    report.update(checkpoint_sha256=sha(run/'policy.npz'),frozen_parameters_unchanged=True,
                  teaching=audit_commands(policy,all_teaching),diagnostic=audit_commands(policy,games['774']),
                  per_game={p.name:audit_commands(policy,games[p.name])['predicted'] for p in teach})
    commands=[];resolved=[];newly_wrong=[]
    for game,examples in games.items():
        for index,(x,y,command,reason) in enumerate(examples):
            prediction=policy.predict(x);assert prediction==loaded.predict(x)
            previous=original_predictions[game][index];assert prediction['ability']==previous['ability']
            gold_indices=[x['tags'].index(tag) for tag in command.units]
            gold_set=set(gold_indices);was_correct=set(previous['actors'])==gold_set;now_correct=set(prediction['actors'])==gold_set
            identity=dict(game=game,row=index,ability=command.ability)
            if not was_correct and now_correct:resolved.append(identity)
            if was_correct and not now_correct:newly_wrong.append(identity)
            scores=policy.scores(x,ability=prediction['ability'])['actor'];eligible=np.flatnonzero(x['actor_mask']);negative=[i for i in eligible if int(i) not in gold_set]
            margin=float(min(scores[gold_indices])-max(scores[negative])) if negative else None
            commands.append(dict(**identity,prediction=prediction,original_prediction=previous,gold_actors=gold_indices,actor_margin=margin,exclusion=reason))
    report.update(commands=commands,resolved=resolved,newly_wrong=newly_wrong,reloaded_predictions_match=True,ability_predictions_unchanged=True)
    assert report['teaching']['commands']==4513 and report['diagnostic']['commands']==292
    (run/'report.json').write_text(json.dumps(report,indent=2)+'\n');reports[optimizer]=report
    print(json.dumps(dict(optimizer=optimizer,status=report['status'],iterations=report['iterations'],evaluations=report['evaluations'],seconds=report['optimizer_seconds'],objective=report['final_objective'],teaching=report['teaching']['predicted'],diagnostic=report['diagnostic']['predicted'],norm=report['parameter_norm'])),flush=True)
    for path,h in code.items():assert sha(Path(path))==h
    assert validate_datasets(teach,diagnostic,missing_fields=True)==sources
    assert sha(watchdog_path)==watchdog_hash
    assert sha(parent_path)==parent_hash and sha(configuration_path)==configuration_hash
c=reports['lbfgs'];g=contract['gates'];improved=sum(c['per_game'][game]['complete']>initial_per_game[game]['complete'] for game in initial_per_game)
gates=dict(teaching_actors=c['teaching']['predicted']['actors']>=g['teaching_actors_min'],teaching_complete=c['teaching']['predicted']['complete']>=g['teaching_complete_min'],teaching_games=improved>=g['teaching_games_improved_min'],diagnostic_actors=c['diagnostic']['predicted']['actors']>=g['diagnostic_actors_min'],diagnostic_complete=c['diagnostic']['predicted']['complete']>=g['diagnostic_complete_min'],diagnostic_targets=c['diagnostic']['predicted']['target']>=g['diagnostic_targets_min'],ability_unchanged=c['ability_predictions_unchanged'])
comparison=dict(status='completed',contract_sha256=sha(output/'contract.json'),cache_archive_sha256=sha(output/'cache.npz'),bindings_unchanged=True,gates=gates,all_gates_passed=all(gates.values()),teaching_games_improved=improved,elapsed_seconds=time.monotonic()-started,promoted=False,native_games=0,rl_updates=0)
(output/'comparison.json').write_text(json.dumps(comparison,indent=2)+'\n');print(json.dumps(comparison,indent=2))
