"""Twelve fixed Hard games; no fitting or deployment teacher fallback."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from pathlib import Path
import sys
import threading
import selector
from teacher_worker import episode,entrypoint_probe
from teacher_validate import validate
from recurrent_worker import digest
from strength_study import write,merge,fresh
from native_smoke import ROOT,budget,verify
from src.runtime import supervise
from src.runner import validate_map
from src.rl.actor_critic import ActorCritic
from src.rl.terran import FEATURES,ACTIONS

ARM=ROOT/'logs/macro-teacher/preflight'
PLAN=ROOT/'docs/superpowers/plans/2026-10-05-macro-teacher-preflight.md'


def cases():
    return [{'seed':125000+i,'policy_seed':125000+i,'race':['Terran','Protoss','Zerg'][i%3],
             'build':['Rush','Timing','Power','Macro','Air'][i%5],'map':['Simple64','TritonLE'][(i//3)%2],
             'difficulty':'Hard','mode':'evaluate','purpose':'macro-teacher-preflight'} for i in range(12)]


def gate(rows):
    assert len(rows)==12 and {row['seed'] for row in rows}=={case['seed'] for case in cases()}
    for row in rows:assert all(row[key]==value for key,value in next(case for case in cases() if case['seed']==row['seed']).items())
    valid=all(row['status'] in ['completed','truncated'] and row['episode_audit']['passed'] for row in rows)
    wins={race:sum(row.get('result')=='Victory' for row in rows if row['race']==race) for race in ['Terran','Protoss','Zerg']}
    return {'competent':valid and sum(wins.values())>=8 and min(wins.values())>=2,
            'wins':sum(wins.values()),'wins_by_race':wins,'valid_all12':valid,'learned_strength_claim':False}


def prepare():
    assert not ARM.exists()
    previous_path=ROOT/'logs/audit/recurrent-strength-evaluation-independent-review.json'
    previous=json.loads(previous_path.read_text());assert previous['passed'] and previous['evaluation_complete']
    hashes=merge(previous['data_hashes'],previous['source_hashes'])
    review_path=ROOT/'logs/audit/macro-teacher-implementation-review.json'
    review=json.loads(review_path.read_text());assert review['passed'] and review['preflight_ready']
    hashes=merge(hashes,{**review['source_hashes'],str(previous_path):digest(previous_path),str(review_path):digest(review_path),str(PLAN):digest(PLAN)})
    hashes=merge(hashes,{str(validate_map(name).path):digest(validate_map(name).path) for name in ['Simple64','TritonLE']})
    scan=fresh(cases());model=ROOT/'logs/ppo-combat-kills/frozen-easy40.npz'
    assert hashes[str(model)]=='0f3e05d9efd5eba4fd238a6282e462599ffc675f008b98fd42925e99f6bb16c6'
    context=ActorCritic.load(model,FEATURES,ACTIONS)
    probe=supervise(entrypoint_probe,(),10)
    assert probe['file']==str(ROOT/'tools/macro_teacher/teacher_worker.py') and probe['games_launched']==0
    ARM.mkdir(parents=True);jobs=[]
    for case in cases():
        base=ARM/str(case['seed'])
        jobs.append({**case,'game_limit':1200,'macro_seconds':1,'gamma':context.gamma,'reward_scale':context.reward_scale,
                     'reward_version':context.reward_version,'behavior_checkpoint':str(model),'behavior_checkpoint_sha256':digest(model),
                     'checkpoint_role':'context_only_not_teacher_weights','teacher_source':str(Path(selector.__file__).resolve()),
                     'teacher_source_sha256':digest(selector.__file__),
                     **{key:str(base.with_suffix(suffix)) for key,suffix in [('actions','.actions.jsonl'),('journal','.journal.jsonl'),
                         ('replay','.SC2Replay'),('trajectory','.trajectory.npz'),('production','.production.jsonl'),('commands','.commands.jsonl'),('receipt','.json')]}})
    inputs={'jobs':jobs,'hashes':hashes,'workers':4,'cpu_ceiling_percent':80,'cpu_baseline_percent':50,'wall_seconds':180,
            'seed_scan':scan,'spawn_probe':probe}
    verify(inputs);write(ARM/'inputs.json',inputs);print(json.dumps({'prepared':True,'games_launched':0,'inputs_sha256':digest(ARM/'inputs.json')}),flush=True)


def collect(jobs,stop):
    assert len(jobs)<=4
    outcomes={};futures=[];pool=ThreadPoolExecutor(max_workers=4)
    try:
        for job in jobs:futures.append(pool.submit(supervise,episode,(job,),180,stop_event=stop))
        for future in as_completed(futures):
            job=jobs[futures.index(future)];result=future.result();row={**job,**result}
            try:row['episode_audit']=validate(job,row)
            except Exception as failure:row.update(episode_status=row['status'],status='audit_failed',audit_error=repr(failure))
            outcomes[future]=row
            if row['status'] not in ['completed','truncated']:stop.set()
    except (KeyboardInterrupt,Exception):stop.set()
    finally:pool.shutdown(wait=True)
    rows=[]
    for i,job in enumerate(jobs):
        if i<len(futures) and futures[i] in outcomes:row=outcomes[futures[i]]
        else:
            try:result=futures[i].result() if i<len(futures) else {'status':'not_started'}
            except KeyboardInterrupt:result={'status':'interrupted'}
            except Exception as failure:result={'status':'error','error':repr(failure)}
            row={**job,**result}
            if row['status'] in ['completed','truncated']:
                try:row['episode_audit']=validate(job,row)
                except Exception as failure:row.update(episode_status=row['status'],status='audit_failed',audit_error=repr(failure))
        rows.append(row)
    return rows


def persist(rows):
    for row in rows:
        if not Path(row['receipt']).exists():write(row['receipt'],row)


def run():
    inputs=json.loads((ARM/'inputs.json').read_text());assert inputs['workers']==4
    assert [{key:job[key] for key in cases()[0]} for job in inputs['jobs']]==cases()
    inputs['hashes']=merge(inputs['hashes'],{str(ARM/'inputs.json'):digest(ARM/'inputs.json')})
    write(ARM/'started.json',{'inputs_sha256':digest(ARM/'inputs.json')})
    stop,done,windows=threading.Event(),threading.Event(),[]
    monitor=threading.Thread(target=budget.monitor,args=(stop,done,windows),daemon=True);monitor.start()
    ledger=[];active=[];error=None
    try:
        for start in range(0,12,4):
            verify(inputs)
            while budget.baseline()>budget.BASELINE:assert not stop.is_set()
            assert not stop.is_set()
            active=collect(inputs['jobs'][start:start+4],stop);persist(active);ledger.extend(active);active=[]
            assert all(row['status'] in ['completed','truncated'] for row in ledger) and not stop.is_set()
            write(ARM/f'round-{start//4+1}.json',ledger)
            print(json.dumps({'recorded_games':len(ledger),'fits':0}),flush=True)
        verify(inputs)
    except (KeyboardInterrupt,Exception) as failure:stop.set();error=repr(failure)
    finally:
        persist(active);recorded={row['seed'] for row in ledger};ledger.extend(row for row in active if row['seed'] not in recorded)
        for job in inputs['jobs']:
            if not any(row['seed']==job['seed'] for row in ledger):ledger.append({**job,'status':'not_started'})
        persist(ledger);done.set();monitor.join()
        if stop.is_set() and error is None:error='CPU guard stopped run'
        write(ARM/'cpu-windows.json',windows);write(ARM/'ledger.json',ledger)
        complete=error is None and all(row['status'] in ['completed','truncated'] for row in ledger)
        write(ARM/'summary.json',{'completed':complete,'error':error,'recorded_jobs':len(ledger),
                                 'validated_games':sum(row['status'] in ['completed','truncated'] for row in ledger),
                                 'games_with_recorded_decisions':sum(Path(row['journal']).exists() for row in ledger),
                                 'gate':gate(ledger) if complete else None,'fits':0,'learned_strength_claim':False})
    print((ARM/'summary.json').read_text(),flush=True)


if __name__=='__main__':
    assert sys.argv[1] in ['prepare','run']
    prepare() if sys.argv[1]=='prepare' else run()
