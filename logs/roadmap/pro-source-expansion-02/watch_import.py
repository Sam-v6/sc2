import json,os,subprocess,time,hashlib
from pathlib import Path
import psutil
P=Path(__file__).parent;receipt=P/'import-telemetry.json'
assert not receipt.exists()
script=P/'import_sources.py'
env=dict(os.environ,PYTHONPATH='.',OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',CUDA_VISIBLE_DEVICES='')
child=subprocess.Popen(['.venv/bin/python','-W','ignore::DeprecationWarning',str(script)],env=env)
record=dict(status='running',pid=child.pid,script_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),cpu_limit=80,wall_limit=900,samples=[],stop_reason=None)
start=time.monotonic();high=0
while child.poll() is None:
    cpu=psutil.cpu_percent(interval=1);record['samples'].append(dict(time=time.time(),cpu=cpu));high=high+1 if cpu>80 else 0
    if high>=3 or time.monotonic()-start>900:
        record['stop_reason']='cpu' if high>=3 else 'wall';child.terminate()
        try:child.wait(timeout=10)
        except subprocess.TimeoutExpired:child.kill();child.wait()
    receipt.write_text(json.dumps(record,indent=2)+'\n')
record.update(returncode=child.wait(),status='completed' if child.returncode==0 else 'stopped')
receipt.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(status=record['status'],returncode=record['returncode'],peak_cpu=max(s['cpu'] for s in record['samples']))),flush=True)
