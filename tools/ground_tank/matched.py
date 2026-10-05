"""Frozen24game teacher comparison; no learned strength or fitting claim."""
import json
from pathlib import Path
import sys
import threading
import numpy as np
import preflight
import matched_worker as worker
from recurrent_worker import digest
from strength_study import merge,write,fresh
from native_smoke import ROOT,budget,verify
from src.runtime import supervise

ARM=ROOT/'logs/ground-tank/matched-comparison'
PLAN=ROOT/'docs/superpowers/plans/2026-10-05-ground-tank-matched-comparison.md'


def cases():
    return [{'seed':128000+i,'policy_seed':128000+i,'race':['Terran','Protoss','Zerg'][i%3],
             'build':['Rush','Timing','Power','Macro','Air'][i%5],'map':['Simple64','TritonLE'][(i//3)%2],
             'difficulty':'Hard','mode':'evaluate','purpose':'macro-teacher-preflight',
             'experiment':'ground-tank-matched','role':role,'micro_version':'original' if role=='control' else 'ground-tank-v1'}
            for i in range(12) for role in ['control','candidate']]


def gate(rows):
    assert len(rows)==24 and {(r['seed'],r['role']) for r in rows}=={(r['seed'],r['role']) for r in cases()}
    for row in rows:assert all(row[key]==value for key,value in next(c for c in cases() if (c['seed'],c['role'])==(row['seed'],row['role'])).items())
    valid=all(row['status'] in ['completed','truncated'] and row['episode_audit']['passed'] for row in rows)
    wins={role:{race:sum(row.get('result')=='Victory' for row in rows if row['role']==role and row['race']==race)
                for race in ['Terran','Protoss','Zerg']} for role in ['control','candidate']}
    candidate=sum(wins['candidate'].values());control=sum(wins['control'].values())
    paired={seed:{r['role']:r['result'] for r in rows if r['seed']==seed} for seed in range(128000,128012)}
    return {'competent':valid and candidate>=8 and min(wins['candidate'].values())>=2 and candidate>=control,
        'wins_by_race':wins,'win_gain':candidate-control,'valid_all24':valid,
        'lost_control_wins':[seed for seed,pair in paired.items() if pair['control']=='Victory' and pair['candidate']!='Victory'],
        'gained_wins':[seed for seed,pair in paired.items() if pair['control']!='Victory' and pair['candidate']=='Victory'],
        'mean_discounted_return':{role:float(np.mean([row['episode_audit']['discounted_return'] for row in rows if row['role']==role])) for role in ['control','candidate']},
        'learned_strength_claim':False}


def prepare():
    assert not ARM.exists()
    prior_path=ROOT/'logs/audit/ground-tank-fixture-complete-independent-review.json'
    prior=json.loads(prior_path.read_text());assert prior['passed'] and prior['corrected_semantic_physical_gate_verified']
    review_path=ROOT/'logs/audit/ground-tank-matched-implementation-review.json'
    review=json.loads(review_path.read_text());assert review['passed'] and review['comparison_ready']
    hashes=merge(prior['data_hashes'],prior['source_hashes'])
    hashes=merge(hashes,{**review['source_hashes'],str(prior_path):digest(prior_path),str(review_path):digest(review_path),str(PLAN):digest(PLAN)})
    scan=fresh(cases());probe=supervise(worker.entrypoint_probe,(),10)
    assert probe['file']==str(ROOT/'tools/ground_tank/matched_worker.py') and probe['games_launched']==0
    template=json.loads((preflight.ARM/'inputs.json').read_text())['jobs'][0]
    ARM.mkdir(parents=True);jobs=[]
    for case in cases():
        base=ARM/f'{case["seed"]}-{case["role"]}'
        jobs.append({**template,**case,**{key:str(base.with_suffix(suffix)) for key,suffix in [
            ('actions','.actions.jsonl'),('journal','.journal.jsonl'),('replay','.SC2Replay'),('trajectory','.trajectory.npz'),
            ('production','.production.jsonl'),('commands','.commands.jsonl'),('receipt','.json')]}})
    inputs={'jobs':jobs,'hashes':hashes,'workers':4,'wall_seconds':180,'seed_scan':scan,'spawn_probe':probe}
    verify(inputs);write(ARM/'inputs.json',inputs);print(json.dumps({'prepared':True,'games_launched':0}),flush=True)


def run():
    inputs=json.loads((ARM/'inputs.json').read_text());assert inputs['workers']==4 and len(inputs['jobs'])==24
    assert [{key:job[key] for key in cases()[0]} for job in inputs['jobs']]==cases()
    inputs['hashes']=merge(inputs['hashes'],{str(ARM/'inputs.json'):digest(ARM/'inputs.json')})
    write(ARM/'started.json',{'inputs_sha256':digest(ARM/'inputs.json')})
    stop,done,windows=threading.Event(),threading.Event(),[]
    monitor=threading.Thread(target=budget.monitor,args=(stop,done,windows),daemon=True);monitor.start()
    rows=[];error=None;previous=preflight.episode
    try:
        preflight.episode=worker.episode
        for start in range(0,24,4):
            verify(inputs)
            while budget.baseline()>budget.BASELINE:assert not stop.is_set()
            assert not stop.is_set()
            rows.extend(preflight.collect(inputs['jobs'][start:start+4],stop));preflight.persist(rows)
            assert all(row['status'] in ['completed','truncated'] for row in rows) and not stop.is_set()
            write(ARM/f'round-{start//4+1}.json',rows)
            print(json.dumps({'recorded_games':len(rows),'fits':0}),flush=True)
        verify(inputs)
    except (KeyboardInterrupt,Exception) as failure:stop.set();error=repr(failure)
    finally:
        preflight.episode=previous
        for job in inputs['jobs']:
            if not any((r['seed'],r['role'])==(job['seed'],job['role']) for r in rows):rows.append({**job,'status':'not_started'})
        preflight.persist(rows);done.set();monitor.join()
        if stop.is_set() and error is None:error='CPU guard stopped comparison'
        write(ARM/'ledger.json',rows);write(ARM/'cpu-windows.json',windows)
        complete=error is None and all(row['status'] in ['completed','truncated'] for row in rows)
        write(ARM/'summary.json',{'completed':complete,'error':error,'recorded_jobs':len(rows),
            'gate':gate(rows) if complete else None,'fits':0,'learned_strength_claim':False})
    print((ARM/'summary.json').read_text(),flush=True)


if __name__=='__main__':
    assert sys.argv[1] in ['prepare','run']
    prepare() if sys.argv[1]=='prepare' else run()
