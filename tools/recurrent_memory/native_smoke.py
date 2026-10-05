"""Two capped games and actual sequence updates before a separate strength study."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import threading
from recurrent_policy import RecurrentPolicy
from recurrent_worker import digest,episode,entrypoint_probe
from src.rl.actor_critic import ActorCritic
from src.rl.terran import FEATURES,ACTIONS
from src.runtime import supervise
from src.runner import validate_map
from src.path import SC2_GAME_PATH

ROOT=Path(__file__).resolve().parents[2]
ARM=ROOT/'logs/recurrent-memory/native-smoke'
CPU=ROOT/'logs/resource-collection-curriculum/runtime-v2/collection_cpu_budget.py'
sys.path.insert(0,str(CPU.parent))
import collection_cpu_budget as budget
TORCH=Path('/home/sam/repos/sc2-repos/SC2RL/.venv/bin/python')


def write(path,value):
    assert not path.exists()
    with path.open('x') as file:
        json.dump(value,file,indent=2,allow_nan=False);file.write('\n')


def verify(inputs):
    for path,expected in inputs['hashes'].items():
        assert digest(path)==expected,path


def prepare():
    assert not ARM.exists()
    roots=[ROOT/'logs',ROOT.parents[1]/'logs',ROOT.parents[1]/'.worktrees/terran-training-history/logs']
    scan=subprocess.run(['rg','-l','-U','-g','*.json',r'"(?:seed|game_seed|seed_start)"\s*:\s*119000\b',*map(str,roots)],capture_output=True,text=True)
    assert scan.returncode==1,(scan.stdout,scan.stderr)
    for root in roots:
        assert not any(path.is_file() and path.name.startswith(('119000-','119000.')) for path in root.rglob('*'))
    review_path=ROOT/'logs/audit/recurrent-smoke-implementation-review.json'
    review=json.loads(review_path.read_text());assert review['passed'] and review['smoke_ready']
    hashes=dict(review['source_hashes'])
    verify({'hashes':hashes})
    hashes[str(review_path)]=digest(review_path)
    for path in [CPU,ROOT/'tools/low_load.py',ROOT/'docs/superpowers/plans/2026-10-05-recurrent-native-smoke.md']:
        if str(path) in hashes: assert hashes[str(path)]==digest(path)
        hashes[str(path)]=digest(path)
    parent_path=ROOT/'logs/ppo-combat-kills/frozen-easy40.npz'
    expected='0f3e05d9efd5eba4fd238a6282e462599ffc675f008b98fd42925e99f6bb16c6'
    assert digest(parent_path)==expected;hashes[str(parent_path)]=expected
    parent=ActorCritic.load(parent_path,FEATURES,ACTIONS)
    for path in sorted((ROOT/'src').rglob('*.py')):
        if str(path) in hashes: assert hashes[str(path)]==digest(path)
        hashes[str(path)]=digest(path)
    for path in [Path(SC2_GAME_PATH)/'Versions/Base75689/SC2_x64',validate_map('Simple64').path]:
        hashes[str(path)]=digest(path)
    probe=supervise(entrypoint_probe,(),10)
    assert probe['file']==str(ROOT/'tools/recurrent_memory/recurrent_worker.py') and probe['games_launched']==0
    ARM.mkdir();jobs=[]
    for role,reset in [('recurrent',False),('reset',True)]:
        initial=ARM/f'{role}-initial.npz';RecurrentPolicy(parent,331,reset).save(initial)
        hashes[str(initial)]=digest(initial)
        base=ARM/f'119000-{role}'
        jobs.append({'role':role,'memory_reset':reset,'mode':'train','purpose':'engineering-smoke-only',
                     'seed':119000,'policy_seed':119000,'map':'Simple64','race':'Terran','build':'Rush','difficulty':'Medium',
                     'game_limit':1200,'macro_seconds':1,'gamma':parent.gamma,'reward_scale':parent.reward_scale,
                     'reward_version':parent.reward_version,'behavior_checkpoint':str(initial),'behavior_checkpoint_sha256':digest(initial),
                     'actions':str(base.with_suffix('.actions.jsonl')),'journal':str(base.with_suffix('.journal.jsonl')),
                     'replay':str(base.with_suffix('.SC2Replay')),'trajectory':str(base.with_suffix('.trajectory.npz')),
                     'receipt':str(base.with_suffix('.json')),'fitted_checkpoint':str(ARM/f'{role}-fitted.npz'),
                     'fit_receipt':str(ARM/f'{role}-fit.json')})
    inputs={'jobs':jobs,'hashes':hashes,'workers':2,'cpu_ceiling_percent':budget.CEILING,
            'cpu_baseline_percent':budget.BASELINE,'wall_seconds':180,'spawn_probe':probe}
    verify(inputs);write(ARM/'inputs.json',inputs)
    print(json.dumps({'prepared':True,'games_launched':0,'inputs_sha256':digest(ARM/'inputs.json')}),flush=True)


def fit_command(index):
    result=subprocess.run([str(TORCH),'-B',str(ROOT/'tools/recurrent_memory/fit_episode.py'),str(ARM/'inputs.json'),str(index)],capture_output=True,text=True,timeout=115)
    assert result.returncode==0,(result.stdout,result.stderr)
    return {'status':'completed','stdout':result.stdout}


def collect(jobs,stop):
    assert len(jobs)<=2
    pool=ThreadPoolExecutor(max_workers=2);futures=[]
    try:
        for job in jobs:
            futures.append(pool.submit(supervise,episode,(job,),180,stop_event=stop))
        for future in futures: future.result()
    except (KeyboardInterrupt,Exception):
        stop.set()
    finally:
        pool.shutdown(wait=True)
    results=[]
    for i in range(len(jobs)):
        try:
            result=futures[i].result() if i<len(futures) else {'status':'not_started'}
        except KeyboardInterrupt: result={'status':'interrupted'}
        except Exception as error: result={'status':'error','error':repr(error)}
        results.append(result)
    return results


def run():
    inputs=json.loads((ARM/'inputs.json').read_text());verify(inputs)
    assert len(inputs['jobs'])==2 and inputs['workers']==2
    assert not (ARM/'summary.json').exists()
    stop,done,windows=threading.Event(),threading.Event(),[]
    monitor=threading.Thread(target=budget.monitor,args=(stop,done,windows),daemon=True);monitor.start()
    receipts=[];results=[];fits=[];error=None;active_fit=None
    try:
        while budget.baseline()>budget.BASELINE:
            assert not stop.is_set()
        results=collect(inputs['jobs'],stop)
        for job,result in zip(inputs['jobs'],results):
            receipt={**job,**result};write(Path(job['receipt']),receipt);receipts.append(receipt)
        assert all(row['status'] in ['completed','truncated'] for row in receipts)
        assert not stop.is_set()
        verify(inputs)
        for index,job in enumerate(inputs['jobs']):
            active_fit=ARM/f'{job["role"]}-fit-supervision.json'
            result=supervise(fit_command,(index,),120,stop_event=stop)
            write(active_fit,result);fits.append(result);active_fit=None
            assert result['status']=='completed' and not stop.is_set(),result
            print(result['stdout'],flush=True)
        verify(inputs)
    except (KeyboardInterrupt,Exception) as failure:
        stop.set();error=repr(failure)
        if active_fit is not None and not active_fit.exists():
            write(active_fit,{'status':'interrupted' if isinstance(failure,KeyboardInterrupt) else 'error','error':error})
    finally:
        for job,result in zip(inputs['jobs'],results):
            if not Path(job['receipt']).exists(): write(Path(job['receipt']),{**job,**result})
        receipts=[{**job,**result} for job,result in zip(inputs['jobs'],results)]
        done.set();monitor.join();write(ARM/'cpu-windows.json',windows)
        if stop.is_set() and error is None: error='CPU guard stopped smoke'
        actual_updates={}
        for job in inputs['jobs']:
            path=ARM/f'{job["role"]}-fit.json'
            if path.exists(): actual_updates[job['role']]=json.loads(path.read_text())['optimizer_clock']
        write(ARM/'summary.json',{'completed':error is None,'error':error,'recorded_games':len(receipts),
                                  'completed_fits':sum(row['status']=='completed' for row in fits),
                                  'planned_sequence_updates_per_arm':4,'actual_sequence_updates':actual_updates,'strength_claim':False,
                                  'scope':'Engineering smoke only; candidates not promoted or used as strength-study initialization.'})
    print((ARM/'summary.json').read_text(),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='prepare': prepare()
    else:
        assert sys.argv[1]=='run';run()
