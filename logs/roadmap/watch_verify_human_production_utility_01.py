"""CPU/total-wall guard for one supervised expanded-source fit."""
import hashlib,json,os,subprocess,time
from pathlib import Path
import psutil
root=Path.cwd();script=root/'logs/roadmap/verify_human_production_utility_01.py'
receipt=root/'logs/roadmap/human-production-utility-01.verification-telemetry.json'
assert not receipt.exists()
runtime='/home/sam/repos/hobby-repos/exoplanet/.venv/bin/python'
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',PYTHONPATH=f'.:{root}/.venv/lib/python3.12/site-packages',SC2_FIT_WATCHDOG=str(Path(__file__).absolute()))
# Do not start this retry while whole-host background load leaves little headroom.
waiting=dict(status='waiting_for_cpu',start_cpu_threshold=70,samples=[],stop_reason=None)
wait_start=time.monotonic();low=0
while low<3:
    cpu=psutil.cpu_percent(interval=1)
    waiting['samples'].append(dict(time=time.time(),cpu=cpu))
    low=low+1 if cpu<70 else 0
    receipt.write_text(json.dumps(waiting,indent=2)+'\n')
    if time.monotonic()-wait_start>180:
        waiting.update(status='deferred_cpu',stop_reason='Insufficient CPU headroom within180seconds')
        receipt.write_text(json.dumps(waiting,indent=2)+'\n')
        print(json.dumps(dict(status=waiting['status'],latest_cpu=cpu)),flush=True)
        raise SystemExit(0)
    if low<3:time.sleep(4)
print(json.dumps(dict(stage='human_goal_fit_started',baseline_cpu=cpu)),flush=True)
child=subprocess.Popen([runtime,'-W','ignore::DeprecationWarning',str(script)],env=env)
record=dict(prestart=waiting,status='running',pid=child.pid,cpu_limit=80,total_wall_limit=900,runtime=runtime,script_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),watchdog_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),samples=[],stop_reason=None)
start=time.monotonic();high=0
while child.poll() is None:
    cpu=psutil.cpu_percent(interval=1);record['samples'].append(dict(time=time.time(),cpu=cpu));high=high+1 if cpu>80 else 0
    marker=root/'logs/roadmap/human-production-utility-01/optimizer-start.json'
    optimizer_over=False
    if high>=3 or optimizer_over or time.monotonic()-start>900:
        record['stop_reason']='cpu' if high>=3 else 'optimizer_wall' if optimizer_over else 'wall';child.terminate()
        try:child.wait(timeout=10)
        except subprocess.TimeoutExpired:child.kill();child.wait()
    receipt.write_text(json.dumps(record,indent=2)+'\n')
    if child.poll() is None:time.sleep(4)
record.update(returncode=child.wait(),status='completed' if child.returncode==0 else 'stopped')
receipt.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(status=record['status'],returncode=record['returncode'],peak_cpu=max(s['cpu'] for s in record['samples']))),flush=True)
