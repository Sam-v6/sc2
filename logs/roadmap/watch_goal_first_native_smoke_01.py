"""One bounded native controller wiring smoke; no training/strength evaluation."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import psutil

root=Path.cwd()
output=root/'logs/roadmap/goal-first-native-smoke-01'
receipt=output.with_suffix('.telemetry.json')
assert not output.exists() and not receipt.exists()
runtime='/home/sam/repos/hobby-repos/exoplanet/.venv/bin/python'
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',PYTHONPATH=f'.:{root}/.venv/lib/python3.12/site-packages',SC2PATH='/home/sam/repos/sc2-repos/game/SC2.4.10/StarCraftII')
policy=root/'logs/roadmap/professional-mixed-history-01/policy.npz'
record=dict(status='running',samples=[],script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),policy_sha256=hashlib.sha256(policy.read_bytes()).hexdigest(),stop_reason=None,cpu_limit=80)
with output.with_suffix('.stdout.txt').open('x') as log:
    child=subprocess.Popen([runtime,'-W','ignore::DeprecationWarning','-m','src.learning.entity_play','--controller','goal-first','--policy',str(policy),'--output',str(output),'--map','AcropolisLE','--race','Zerg','--difficulty','VeryEasy','--seed','120601','--seconds','15','--wall-seconds','60','--wait-unavailable'],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
    record['pid']=child.pid
    high=0
    while child.poll() is None:
        cpu=psutil.cpu_percent(interval=1)
        record['samples'].append(dict(unix_time=time.time(),whole_cpu_percent=cpu))
        high=high+1 if cpu>80 else 0
        if high>=3:
            record['stop_reason']='Whole CPU above80percent on three consecutive samples'
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        receipt.write_text(json.dumps(record,indent=2)+'\n')
    record.update(status='completed' if child.returncode==0 else 'stopped',returncode=child.wait())
record['policy_unchanged']=hashlib.sha256(policy.read_bytes()).hexdigest()==record['policy_sha256']
receipt.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(status=record['status'],returncode=record['returncode'],peak_cpu=max(s['whole_cpu_percent'] for s in record['samples']),policy_unchanged=record['policy_unchanged'])),flush=True)
