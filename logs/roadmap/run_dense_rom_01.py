"""Bounded diagnostic-only dense native replay extraction, CPU-only."""
import hashlib,json,os,signal,subprocess,time
from pathlib import Path
import psutil
ROOT=Path('logs/roadmap');OUT=ROOT/'human-rom-dense-01';receipt=ROOT/'human-rom-dense-01.guard.json'
assert not OUT.exists() and not receipt.exists()
source=ROOT/'issued-51482-rom-masked-01/dataset.json';prior=json.loads(source.read_text());replay=Path(prior['replay'])
files=[Path(__file__),source,replay,*sorted(Path('src/learning').glob('*.py'))]
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=hashes();assert before[str(replay)]==prior['sha256']
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',SC2PATH='/home/sam/repos/sc2-repos/game/SC2.4.10/StarCraftII',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONPATH='.')
cmd=['.venv/bin/python','-W','ignore::DeprecationWarning','-m','src.learning.replay_extract',str(replay),'--output',str(OUT),'--player','1','--max-loops','5300','--wall-seconds','120','--observation-stride','44','--source',prior['source']]
child=subprocess.Popen(cmd,env=env,start_new_session=True);start=time.monotonic();samples=[];high=0;reason=None
while child.poll() is None:
 cpu=psutil.cpu_percent(interval=1);samples.append(cpu);high=high+1 if cpu>80 else 0
 if high>=3 or time.monotonic()-start>140:
  reason='cpu' if high>=3 else 'wall';os.killpg(child.pid,signal.SIGTERM)
  try:child.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 time.sleep(.2)
assert hashes()==before
result=dict(status='completed' if child.returncode==0 else 'failed',returncode=child.returncode,stop_reason=reason,peak_cpu=max(samples,default=0),samples=samples,wall_seconds=time.monotonic()-start,bindings=before,role='reused_diagnostic',teacher='Masters human; no professional claim',training=False,rl=False)
receipt.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
if child.returncode:raise SystemExit(child.returncode)
