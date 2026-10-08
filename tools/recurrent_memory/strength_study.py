"""Fixed 128-game training comparison, then 90 immutable development games."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
from uuid import uuid4
from recurrent_policy import RecurrentPolicy
from recurrent_worker import digest,episode,entrypoint_probe
from strength_cases import training_cases,evaluation_cases,gate
from strength_validate import validate
from native_smoke import ROOT,CPU,TORCH,budget,verify
from src.rl.actor_critic import ActorCritic
from src.rl.terran import FEATURES,ACTIONS
from src.runtime import supervise
from src.runner import validate_map
from src.path import SC2_GAME_PATH

ARM=ROOT/'logs/recurrent-memory/strength-study'
PLAN=ROOT/'docs/superpowers/plans/2026-10-05-recurrent-strength-study.md'


def write(path,value):
    path=Path(path);assert not path.exists()
    temporary=path.with_name(path.name+f'.{uuid4().hex}.tmp')
    with temporary.open('x') as file:
        json.dump(value,file,indent=2,allow_nan=False);file.write('\n')
    temporary.replace(path)


def merge(hashes,extra):
    verify({'hashes':hashes})
    result=dict(hashes)
    for path,expected in extra.items():
        assert digest(path)==expected,path
        if path in result:assert result[path]==expected,path
        result[path]=expected
    return result


def fresh(cases):
    roots=[ROOT/'logs',ROOT.parents[1]/'logs',ROOT.parents[1]/'.worktrees/terran-training-history/logs']
    seeds=[c['seed'] for c in cases]
    pattern=r'"(?:seed|game_seed|seed_start)"\s*:\s*(?:'+'|'.join(map(str,seeds))+r')\b'
    scan=subprocess.run(['rg','-l','-U','-g','*.json',pattern,*map(str,roots)],capture_output=True,text=True)
    assert scan.returncode==1,(scan.stdout,scan.stderr)
    names=re.compile(r'^(?:'+'|'.join(map(str,seeds))+r')(?:-|\.)')
    for root in roots:
        assert not any(p.is_file() and names.match(p.name) for p in root.rglob('*'))
    return {'roots':list(map(str,roots)),'seeds':seeds,'receipt_and_actual_artifacts_checked':True}


def prepare():
    assert not ARM.exists()
    prior_path=ROOT/'logs/audit/recurrent-native-smoke-independent-review.json'
    prior=json.loads(prior_path.read_text());assert prior['passed'] and prior['smoke_backend_verified']
    hashes=merge(prior['data_hashes'],prior.get('source_hashes',{}))
    review_path=ROOT/'logs/audit/recurrent-strength-implementation-review.json'
    review=json.loads(review_path.read_text());assert review['passed'] and review['training_ready']
    hashes=merge(hashes,{**review['source_hashes'],str(review_path):digest(review_path),str(prior_path):digest(prior_path),str(PLAN):digest(PLAN)})
    hashes=merge(hashes,{str(validate_map(name).path):digest(validate_map(name).path) for name in ['Simple64','TritonLE']})
    cases=training_cases()+evaluation_cases();scan=fresh(cases)
    parent_path=ROOT/'logs/ppo-combat-kills/frozen-easy40.npz'
    assert hashes[str(parent_path)]=='0f3e05d9efd5eba4fd238a6282e462599ffc675f008b98fd42925e99f6bb16c6'
    parent=ActorCritic.load(parent_path,FEATURES,ACTIONS)
    probe=supervise(entrypoint_probe,(),10)
    assert probe['file']==str(ROOT/'tools/recurrent_memory/recurrent_worker.py') and probe['games_launched']==0
    ARM.mkdir();models={}
    for role,reset in [('recurrent',False),('reset',True)]:
        path=ARM/f'{role}-000.npz';RecurrentPolicy(parent,331,reset).save(path);models[role]=str(path)
    hashes=merge(hashes,{path:digest(path) for path in models.values()})
    inputs={'training_cases':training_cases(),'evaluation_cases':evaluation_cases(),'initial_models':models,'hashes':hashes,
            'workers':4,'cpu_ceiling_percent':80,'cpu_baseline_percent':50,'wall_seconds':180,'game_limit':1200,
            'gamma':parent.gamma,'reward_scale':parent.reward_scale,'reward_version':parent.reward_version,'macro_seconds':1,
            'seed_scan':scan,'spawn_probe':probe}
    verify(inputs);write(ARM/'inputs.json',inputs)
    print(json.dumps({'prepared':True,'inputs_sha256':digest(ARM/'inputs.json'),'training_games':128,'evaluation_games':90,'games_launched':0}),flush=True)


def collect(jobs,stop):
    assert len(jobs)<=8
    pool=ThreadPoolExecutor(max_workers=4);futures=[];audited={}
    try:
        for job in jobs:futures.append(pool.submit(supervise,episode,(job,),180,stop_event=stop))
        for future in as_completed(futures):
            result=future.result()
            if result['status'] in ['completed','truncated']:
                try:validate(jobs[futures.index(future)],{**jobs[futures.index(future)],**result})
                except Exception as failure:
                    result={**result,'episode_status':result['status'],'status':'audit_failed','audit_error':repr(failure)}
            audited[future]=result
            if result['status'] not in ['completed','truncated']:stop.set()
    except (KeyboardInterrupt,Exception):stop.set()
    finally:pool.shutdown(wait=True)
    results=[]
    for i in range(len(jobs)):
        try:result=audited.get(futures[i],futures[i].result()) if i<len(futures) else {'status':'not_started'}
        except KeyboardInterrupt:result={'status':'interrupted'}
        except Exception as failure:result={'status':'error','error':repr(failure)}
        results.append(result)
    return results


def job(case,role,model,inputs):
    base=ARM/case['phase']/f'{case["seed"]}-{role}';base.parent.mkdir(exist_ok=True)
    policy=RecurrentPolicy.load(model,FEATURES,ACTIONS)
    return {**case,'role':role,'purpose':'controlled-strength-study','memory_reset':policy.memory_reset,'model_updates':policy.updates,
            **{key:inputs[key] for key in ['game_limit','macro_seconds','gamma','reward_scale','reward_version']},
            'behavior_checkpoint':str(model),'behavior_checkpoint_sha256':digest(model),
            'actions':str(base.with_suffix('.actions.jsonl')),'journal':str(base.with_suffix('.journal.jsonl')),
            'replay':str(base.with_suffix('.SC2Replay')),'trajectory':str(base.with_suffix('.trajectory.npz')),
            'receipt':str(base.with_suffix('.json'))}


def fit_command(task_path):
    result=subprocess.run([str(TORCH),'-B',str(ROOT/'tools/recurrent_memory/fit_batch.py'),str(task_path)],capture_output=True,text=True,timeout=175)
    assert result.returncode==0,(result.stdout,result.stderr)
    return {'status':'completed','stdout':result.stdout}


def persist(jobs,results):
    rows=[]
    for j,result in zip(jobs,results):
        path=Path(j['receipt'])
        if path.exists():row=json.loads(path.read_text())
        else:
            row={**j,**result}
            try:
                row['episode_audit']=validate(j,row);row['discounted_return']=row['episode_audit']['discounted_return']
            except Exception as failure:row.update(episode_status=row['status'],status='audit_failed',audit_error=repr(failure))
            write(path,row)
        rows.append(row)
    return rows


def run(phase):
    inputs=json.loads((ARM/'inputs.json').read_text());inputs['hashes']=merge(inputs['hashes'],{str(ARM/'inputs.json'):digest(ARM/'inputs.json')})
    assert inputs['training_cases']==training_cases() and inputs['evaluation_cases']==evaluation_cases() and inputs['workers']==4
    summary_path=ARM/f'{phase}-summary.json';assert not summary_path.exists()
    write(ARM/f'{phase}-started.json',{'phase':phase,'inputs_sha256':digest(ARM/'inputs.json')})
    if phase=='train':models=dict(inputs['initial_models'])
    else:
        training=json.loads((ARM/'train-summary.json').read_text());assert training['completed']
        for role,path in training['final_models'].items():
            fit_path=ARM/f'{role}-016.fit.json'
            assert digest(fit_path)==training['final_fit_receipt_hashes'][role]
            fit=json.loads(fit_path.read_text())
            assert path==fit['checkpoint'] and digest(path)==training['final_model_hashes'][role]==fit['sha256']
            assert fit['optimizer_clock']==256 and fit['episodes']==64
        models={**training['final_models'],'reference':inputs['initial_models']['reset']}
        inputs['hashes']=merge(inputs['hashes'],{str(ARM/'train-summary.json'):digest(ARM/'train-summary.json'),**{path:digest(path) for path in models.values()}})
    stop,done,windows=threading.Event(),threading.Event(),[]
    monitor=threading.Thread(target=budget.monitor,args=(stop,done,windows),daemon=True);monitor.start()
    ledger=[];active_jobs=[];active_results=[];active_fit=None;error=None
    try:
        rounds=[inputs['training_cases'][start:start+4] for start in range(0,64,4)] if phase=='train' else [inputs['evaluation_cases'][start:start+1] for start in range(30)]
        for number,cases in enumerate(rounds,1):
            verify(inputs)
            while budget.baseline()>budget.BASELINE:assert not stop.is_set()
            assert not stop.is_set()
            roles=['recurrent','reset'] if phase=='train' else ['recurrent','reset','reference']
            active_jobs=[job(c,role,models[role],inputs) for c in cases for role in roles];active_results=[]
            active_results=collect(active_jobs,stop);rows=persist(active_jobs,active_results);ledger.extend(rows)
            assert len(rows)==len(active_jobs) and all(r['status'] in ['completed','truncated'] for r in rows) and not stop.is_set()
            if phase=='train':
                for role in roles:
                    own=[j for j in active_jobs if j['role']==role]
                    task_path=ARM/f'{role}-{number:03d}.task.json';target=str(ARM/f'{role}-{number:03d}.npz')
                    hashes=merge(inputs['hashes'],{str(p):digest(p) for j in own for p in [j['receipt'],j['trajectory'],j['actions'],j['journal'],j['replay']]})
                    task={'purpose':'controlled-strength-study','role':role,'jobs':own,'behavior_checkpoint':models[role],
                          'behavior_sha256':digest(models[role]),'target':target,'hashes':hashes,'task_path':str(task_path),
                          'fit_receipt':str(ARM/f'{role}-{number:03d}.fit.json')}
                    write(task_path,task);active_fit=ARM/f'{role}-{number:03d}.supervision.json'
                    result=supervise(fit_command,(str(task_path),),180,stop_event=stop);write(active_fit,result);active_fit=None
                    assert result['status']=='completed' and not stop.is_set(),result
                    fit=json.loads(Path(task['fit_receipt']).read_text());assert fit['sha256']==digest(target) and fit['optimizer_clock']==number*16 and fit['episodes']==number*4
                    inputs['hashes']=merge(inputs['hashes'],{target:fit['sha256'],str(task_path):digest(task_path),task['fit_receipt']:digest(task['fit_receipt'])})
                    models[role]=target
            write(ARM/f'{phase}-{number:03d}.ledger.json',ledger)
            print(json.dumps({'phase':phase,'round':number,'games':len(ledger),'updates':number*16 if phase=='train' else None}),flush=True)
        verify(inputs)
    except (KeyboardInterrupt,Exception) as failure:
        stop.set();error=repr(failure)
        if active_fit and not active_fit.exists():write(active_fit,{'status':'interrupted' if isinstance(failure,KeyboardInterrupt) else 'error','error':error})
    finally:
        recorded={(r['seed'],r['role']) for r in ledger}
        ledger.extend(r for r in persist(active_jobs,active_results) if (r['seed'],r['role']) not in recorded)
        done.set();monitor.join();write(ARM/f'{phase}-cpu-windows.json',windows)
        if stop.is_set() and error is None:error='CPU guard stopped run'
        write(ARM/f'{phase}-ledger.json',ledger)
        completed=error is None and len(ledger)==(128 if phase=='train' else 90)
        write(summary_path,{'completed':completed,'error':error,'recorded_games':len(ledger),'final_models':models,
                            'final_model_hashes':{role:digest(path) for role,path in models.items()} if completed else {},
                            'final_fit_receipt_hashes':{role:digest(ARM/f'{role}-016.fit.json') for role in models} if completed and phase=='train' else {},
                            'gate':gate(ledger) if completed and phase=='evaluate' else None,'strength_claim':False})
    print(summary_path.read_text(),flush=True)


if __name__=='__main__':
    command=sys.argv[1]
    if command=='prepare':prepare()
    else:
        assert command in ['train','evaluate'];run(command)
