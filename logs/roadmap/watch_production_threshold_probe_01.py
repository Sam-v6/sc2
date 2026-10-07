import json
import os
from pathlib import Path
import subprocess
import time
import psutil
p=Path('logs/roadmap/production-threshold-probe-01.telemetry.json')
assert not p.exists()
env=dict(os.environ,OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',CUDA_VISIBLE_DEVICES='')
child=subprocess.Popen(['/home/sam/repos/hobby-repos/exoplanet/.venv/bin/python','logs/roadmap/run_production_threshold_probe_01.py'],env=env)
record=dict(pid=child.pid,status='running',cpu_limit=80,wall_limit=300,samples=[],stop_reason=None)
started=time.monotonic(); high=0
while child.poll() is None:
    cpu=psutil.cpu_percent(interval=1)
    record['samples'].append(dict(time=time.time(),cpu=cpu))
    high=high+1 if cpu>80 else 0
    if high>=3 or time.monotonic()-started>300:
        record['stop_reason']='cpu' if high>=3 else 'wall'
        child.terminate()
        try: child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill(); child.wait()
    p.write_text(json.dumps(record,indent=2)+'\n')
record.update(returncode=child.wait(),status='completed' if child.returncode==0 else 'stopped')
p.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(status=record['status'],returncode=record['returncode'],peak_cpu=max(s['cpu'] for s in record['samples']))),flush=True)
