"""One bounded paired post-failure behavior inspection; no fitting or selection."""
import hashlib
import json
import os
from pathlib import Path
import threading
import time

import psutil

from src.learning.entity_play import play_joint_job
from src.runtime import supervise


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert os.environ['CUDA_VISIBLE_DEVICES']==''
    assert os.environ['OPENBLAS_NUM_THREADS']==os.environ['OMP_NUM_THREADS']=='2'
    root=Path.cwd()
    output=root/'logs/roadmap/command-candidates-native-01'
    assert not output.exists()
    fit=root/'logs/roadmap/type-status-imitation-01'
    verified=json.loads((fit/'verification.json').read_text())
    comparison=json.loads((fit/'comparison.json').read_text())
    assert verified['status']=='verified_development_gate_result' and not verified['all_gates_passed']
    assert sha(fit/'comparison.json')==verified['comparison_sha256']
    for arm in ('baseline',):
        assert sha(fit/arm/'policy.npz')==comparison['arm_bindings'][arm]['policy.npz']
    output.mkdir()
    record=dict(status='running',pid=os.getpid(),script_sha256=sha(__file__),plan_sha256=sha('docs/superpowers/plans/2026-10-06-native-command-candidates.md'),comparison_verification_sha256=sha(fit/'verification.json'),cpu_limit=80,arms={},stop_reason=None)
    record['profile_sha256']=sha('logs/roadmap/professional-observation-profile-01.json')
    record['code_bindings']={str(p):sha(p) for p in [Path('src/learning/entity_play.py'),Path('src/learning/entity_execution.py'),Path('src/learning/goal_first_policy.py'),Path('src/learning/entity_type_status.py'),Path('src/learning/entity_examples.py'),Path('src/learning/entity_missing.py'),Path('src/learning/entity_spatial.py'),Path('src/learning/teacher_states.py'),Path('src/learning/gameplay.py'),Path('src/learning/live.py'),Path('src/runtime.py')]}
    for arm in ('baseline',):
        policy=fit/arm/'policy.npz'
        entry=dict(policy_sha256=sha(policy),samples=[])
        record['arms'][arm]=entry
        stop,done=threading.Event(),threading.Event()

        def guard():
            high=0
            while not done.is_set():
                cpu=psutil.cpu_percent(interval=1)
                entry['samples'].append(dict(unix_time=time.time(),whole_cpu_percent=cpu))
                high=high+1 if cpu>80 else 0
                if high>=3:
                    record['stop_reason']='Whole-host CPU above80percent on three consecutive samples'
                    stop.set()
                (output/'telemetry.json').write_text(json.dumps(record,indent=2)+'\n')
                if stop.is_set():
                    return

        monitor=threading.Thread(target=guard)
        monitor.start()
        job=dict(controller='goal-first',policy=str(policy),output=str(output/arm),map='AcropolisLE',race='Zerg',difficulty='VeryEasy',build='RandomBuild',seed=120602,max_game_step=32,seconds=180,wait_unavailable=True,condition_available=True,observation_profile=str(root/'logs/roadmap/professional-observation-profile-01.json'))
        try:
            # Cancellation reaches supervise's finally/_stop, including the
            # dedicated worker session and its SC2 children.
            result=supervise(play_joint_job,(job,),120,stop_event=stop)
        finally:
            done.set()
            monitor.join()
        entry['supervision']=result
        entry['policy_unchanged']=sha(policy)==entry['policy_sha256']
        assert entry['policy_unchanged']
        (output/f'{arm}.supervision.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(dict(stage='arm_terminal',arm=arm,status=result['status'],max_cpu=max((s['whole_cpu_percent'] for s in entry['samples']),default=0))),flush=True)
        if record['stop_reason']:
            break
    record['status']='completed' if len(record['arms'])==1 and all(x['supervision']['status'] in ('completed','truncated') for x in record['arms'].values()) else 'incomplete'
    (output/'telemetry.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(dict(status=record['status'],stop_reason=record['stop_reason'])),flush=True)


if __name__=='__main__':
    main()
