"""Whole-host CPU and total-wall guard for the single declared supervised fit."""
import hashlib,json,os,signal,subprocess,time
from pathlib import Path
import psutil
ROOT=Path.cwd();script=ROOT/'logs/roadmap/run_professional_choice_fit_04.py';receipt=ROOT/'logs/roadmap/professional-choice-fit-04.guard.json';assert not receipt.exists()
runtime='/home/sam/repos/hobby-repos/exoplanet/.venv/bin/python';env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',PYTHONPATH=f'.:{ROOT}/.venv/lib/python3.12/site-packages',SC2_FIT_WATCHDOG=str(Path(__file__).absolute()))
child=subprocess.Popen([runtime,str(script)],env=env,start_new_session=True);start=time.monotonic();high=0;samples=[];reason=None
while child.poll() is None:
 cpu=psutil.cpu_percent(interval=1);samples.append(cpu);high=high+1 if cpu>80 else 0
 if high>=3 or time.monotonic()-start>1200:
  reason='cpu' if high>=3 else 'wall';os.killpg(child.pid,signal.SIGTERM)
  try:child.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 receipt.write_text(json.dumps(dict(status='running',pid=child.pid,samples=samples,stop_reason=reason))+'\n');time.sleep(.5)
receipt.write_text(json.dumps(dict(status='completed' if child.returncode==0 else 'failed',returncode=child.returncode,stop_reason=reason,peak_cpu=max(samples,default=0),samples=samples,wall=time.monotonic()-start,runtime=runtime,script_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),watchdog_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
print(json.dumps(dict(returncode=child.returncode,peak_cpu=max(samples,default=0),stop_reason=reason)),flush=True)
if child.returncode:raise SystemExit(child.returncode)
