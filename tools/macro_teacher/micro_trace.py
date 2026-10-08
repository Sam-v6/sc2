"""Four observation-only games; never extend the closed teacher gate."""
import json
from pathlib import Path
import sys
import threading
import preflight
import micro_trace_worker as worker
from recurrent_worker import digest
from native_smoke import ROOT,budget,verify
from strength_study import write,merge,fresh
from src.runtime import supervise

ARM=ROOT/'logs/macro-teacher/micro-order-diagnostic'
PLAN=ROOT/'docs/superpowers/plans/2026-10-05-micro-order-diagnostic.md'


def cases():
    return [{'seed':126000+i,'policy_seed':126000+i,'race':'Terran',
             'build':['Rush','Timing','Air','Macro'][i],'map':['Simple64','Simple64','TritonLE','TritonLE'][i],
             'difficulty':'Hard','mode':'evaluate','purpose':'macro-teacher-preflight',
             'experiment':'micro-order-diagnostic','diagnostic_only':True} for i in range(4)]


def prepare():
    assert not ARM.exists()
    prior_path=ROOT/'logs/audit/macro-teacher-complete-independent-review.json'
    prior=json.loads(prior_path.read_text());assert prior['passed'] and prior['preflight_complete']
    review_path=ROOT/'logs/audit/micro-order-diagnostic-implementation-review.json'
    review=json.loads(review_path.read_text());assert review['passed'] and review['diagnostic_ready']
    hashes=merge(prior['data_hashes'],prior['source_hashes'])
    hashes=merge(hashes,{**review['source_hashes'],str(prior_path):digest(prior_path),str(review_path):digest(review_path),str(PLAN):digest(PLAN)})
    scan=fresh(cases());probe=supervise(worker.entrypoint_probe,(),10)
    assert probe['file']==str(ROOT/'tools/macro_teacher/micro_trace_worker.py') and probe['games_launched']==0
    template=json.loads((preflight.ARM/'inputs.json').read_text())['jobs'][0]
    ARM.mkdir(parents=True);jobs=[]
    for case in cases():
        base=ARM/str(case['seed'])
        jobs.append({**template,**case,**{key:str(base.with_suffix(suffix)) for key,suffix in [
            ('actions','.actions.jsonl'),('journal','.journal.jsonl'),('replay','.SC2Replay'),
            ('trajectory','.trajectory.npz'),('production','.production.jsonl'),('commands','.commands.jsonl'),
            ('receipt','.json'),('micro_trace','.micro-trace.jsonl')]}})
    inputs={'jobs':jobs,'hashes':hashes,'workers':4,'cpu_ceiling_percent':80,'cpu_baseline_percent':50,
            'wall_seconds':180,'seed_scan':scan,'spawn_probe':probe}
    verify(inputs);write(ARM/'inputs.json',inputs);print(json.dumps({'prepared':True,'games_launched':0}),flush=True)


def run():
    inputs=json.loads((ARM/'inputs.json').read_text());assert inputs['workers']==4 and len(inputs['jobs'])==4
    assert [{key:job[key] for key in cases()[0]} for job in inputs['jobs']]==cases()
    inputs['hashes']=merge(inputs['hashes'],{str(ARM/'inputs.json'):digest(ARM/'inputs.json')})
    write(ARM/'started.json',{'inputs_sha256':digest(ARM/'inputs.json')})
    stop,done,windows=threading.Event(),threading.Event(),[]
    monitor=threading.Thread(target=budget.monitor,args=(stop,done,windows),daemon=True);monitor.start()
    rows=[];error=None;previous=preflight.episode
    try:
        verify(inputs)
        while budget.baseline()>budget.BASELINE:assert not stop.is_set()
        assert not stop.is_set();preflight.episode=worker.episode
        rows=preflight.collect(inputs['jobs'],stop)
        assert all(row['status'] in ['completed','truncated'] for row in rows) and not stop.is_set()
        for row in rows:
            path=Path(row['micro_trace']);assert path.stat().st_size==row['micro_trace_bytes']>0
            assert digest(path)==row['micro_trace_sha256']
        verify(inputs)
    except (KeyboardInterrupt,Exception) as failure:stop.set();error=repr(failure)
    finally:
        preflight.episode=previous
        for job in inputs['jobs']:
            if not any(row['seed']==job['seed'] for row in rows):rows.append({**job,'status':'not_started'})
        preflight.persist(rows);done.set();monitor.join()
        if stop.is_set() and error is None:error='CPU guard stopped run'
        write(ARM/'ledger.json',rows);write(ARM/'cpu-windows.json',windows)
        write(ARM/'summary.json',{'completed':error is None,'error':error,'recorded_jobs':len(rows),
            'validated_games':sum(row['status'] in ['completed','truncated'] for row in rows),
            'diagnostic_only':True,'fits':0,'teacher_gate_changed':False,'learned_strength_claim':False})
    print((ARM/'summary.json').read_text(),flush=True)


if __name__=='__main__':
    assert sys.argv[1] in ['prepare','run']
    prepare() if sys.argv[1]=='prepare' else run()
