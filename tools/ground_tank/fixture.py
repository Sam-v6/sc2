"""Six fixed isolated physical checks; no ordinary gameplay strength claim."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import threading
from fixture_worker import episode,entrypoint_probe
from recurrent_worker import digest
from strength_study import merge,write,fresh
from native_smoke import ROOT,budget,verify
from src.runtime import supervise

ARM=ROOT/'logs/ground-tank/physical-fixture'
PLAN=ROOT/'docs/superpowers/plans/2026-10-05-ground-aware-tank-primitive.md'


def cases():
    variants=[('control','SIEGETANK','OVERLORD'),('candidate','SIEGETANK','OVERLORD'),
              ('control','SIEGETANKSIEGED','OVERLORD'),('candidate','SIEGETANKSIEGED','OVERLORD'),
              ('candidate','SIEGETANK','ROACH'),('candidate','SIEGETANK','SUPPLYDEPOT')]
    return [{'seed':127000+i,'role':role,'tank':tank,'target':target,'engineering_only':True,
             'game_limit':8,'map':'Simple64'} for i,(role,tank,target) in enumerate(variants)]


def validate(job,row):
    assert row['status']=='completed' and row['replay_version']==['Base75689','B89B5D6FA7CBF6452E721311BFBC6CB2']
    assert Path(job['replay']).stat().st_size==row['replay_bytes']>0
    trace=[json.loads(line) for line in Path(job['trace']).read_text().splitlines()]
    assert len(trace)==row['frames']>=15 and all(0<=frame['time']<=8 for frame in trace)
    assert all(a['time']<b['time'] for a,b in zip(trace,trace[1:]))
    context=[tank for frame in trace for tank in frame['tanks'] if any(e['type']==job['target'] and e['distance']<12 for e in tank['enemies'])]
    assert len(context)>=6
    queued=[command['ability'] for frame in trace for command in frame['queued']]
    sieged=sum(tank['type']=='SIEGETANKSIEGED' for tank in context)
    mobile=sum(tank['type']=='SIEGETANK' for tank in context)
    if job['target']=='OVERLORD':
        assert all(not any(not e['flying'] and e['distance']<14 for e in tank['enemies']) for tank in context)
        if job['role']=='control':assert sieged>=1 and 'UNSIEGE_UNSIEGE' not in queued
        else:
            assert mobile>=5 and 'SIEGEMODE_SIEGEMODE' not in queued
            if job['tank']=='SIEGETANK':assert sieged==0
            else:assert 'UNSIEGE_UNSIEGE' in queued
    else:assert sieged>=1 and 'SIEGEMODE_SIEGEMODE' in queued
    return {'passed':True,'context_frames':len(context),'sieged_frames':sieged,'mobile_frames':mobile,
            'trace_sha256':digest(job['trace']),'replay_sha256':digest(job['replay'])}


def prepare():
    assert not ARM.exists()
    prior_path=ROOT/'logs/audit/micro-order-diagnostic-complete-independent-review.json'
    prior=json.loads(prior_path.read_text());assert prior['passed'] and prior['diagnostic_complete']
    review_path=ROOT/'logs/audit/ground-tank-fixture-implementation-review.json'
    review=json.loads(review_path.read_text());assert review['passed'] and review['fixture_ready']
    hashes=merge(prior['data_hashes'],prior['source_hashes'])
    hashes=merge(hashes,{**review['source_hashes'],str(prior_path):digest(prior_path),str(review_path):digest(review_path),str(PLAN):digest(PLAN)})
    scan=fresh(cases());probe=supervise(entrypoint_probe,(),10)
    assert probe['file']==str(ROOT/'tools/ground_tank/fixture_worker.py') and probe['games_launched']==0
    ARM.mkdir(parents=True)
    jobs=[{**case,**{key:str((ARM/str(case['seed'])).with_suffix(suffix)) for key,suffix in [
        ('trace','.trace.jsonl'),('replay','.SC2Replay'),('receipt','.json')]}} for case in cases()]
    inputs={'jobs':jobs,'hashes':hashes,'workers':2,'wall_seconds':60,'seed_scan':scan,'spawn_probe':probe}
    verify(inputs);write(ARM/'inputs.json',inputs);print(json.dumps({'prepared':True,'games_launched':0}),flush=True)


def collect(jobs,stop):
    assert len(jobs)<=2
    futures=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        try:
            for job in jobs:futures.append(pool.submit(supervise,episode,(job,),60,stop_event=stop))
            for future in futures:future.result()
        except (KeyboardInterrupt,Exception):stop.set()
    rows=[]
    for i,job in enumerate(jobs):
        try:result=futures[i].result() if i<len(futures) else {'status':'not_started'}
        except (KeyboardInterrupt,Exception) as failure:result={'status':'error','error':repr(failure)}
        rows.append({**job,**result})
    return rows


def run():
    inputs=json.loads((ARM/'inputs.json').read_text());assert inputs['workers']==2 and len(inputs['jobs'])==6
    assert [{key:job[key] for key in cases()[0]} for job in inputs['jobs']]==cases()
    inputs['hashes']=merge(inputs['hashes'],{str(ARM/'inputs.json'):digest(ARM/'inputs.json')})
    write(ARM/'started.json',{'inputs_sha256':digest(ARM/'inputs.json')})
    stop,done,windows=threading.Event(),threading.Event(),[]
    monitor=threading.Thread(target=budget.monitor,args=(stop,done,windows),daemon=True);monitor.start()
    rows=[];error=None
    try:
        verify(inputs)
        while budget.baseline()>budget.BASELINE:assert not stop.is_set()
        assert not stop.is_set()
        for start in range(0,6,2):
            batch=collect(inputs['jobs'][start:start+2],stop);rows.extend(batch)
            for row in batch:
                job=next(job for job in inputs['jobs'] if job['seed']==row['seed'])
                try:row['physical_audit']=validate(job,row)
                except Exception as failure:row.update(status='audit_failed',audit_error=repr(failure));stop.set()
                write(row['receipt'],row)
            assert len(batch)==2 and not stop.is_set()
        verify(inputs)
    except (KeyboardInterrupt,Exception) as failure:stop.set();error=repr(failure)
    finally:
        for job in inputs['jobs']:
            if not any(row['seed']==job['seed'] for row in rows):rows.append({**job,'status':'not_started'})
        for row in rows:
            if not Path(row['receipt']).exists():write(row['receipt'],row)
        done.set();monitor.join()
        if stop.is_set() and error is None:error='CPU guard stopped fixture'
        write(ARM/'ledger.json',rows);write(ARM/'cpu-windows.json',windows)
        write(ARM/'summary.json',{'completed':error is None,'error':error,'physical_gate_passed':error is None and
            all(row.get('physical_audit',{}).get('passed',False) for row in rows),'recorded_jobs':len(rows),
            'engineering_only':True,'fits':0,'learned_strength_claim':False})
    print((ARM/'summary.json').read_text(),flush=True)


if __name__=='__main__':
    assert sys.argv[1] in ['prepare','run']
    prepare() if sys.argv[1]=='prepare' else run()
