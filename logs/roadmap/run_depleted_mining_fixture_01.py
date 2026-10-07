"""Four bounded sequential addon command fixtures with whole-host CPU guard."""
import hashlib,json,threading,sys
from pathlib import Path
import psutil
sys.path.insert(0,str(Path(__file__).parent.resolve()))
from depleted_mining_fixture_worker_01 import episode
from src.runtime import supervise
OUT=Path('logs/roadmap/depleted-mining-fixture-01')
def main():
 OUT.mkdir(exist_ok=False);paths=[Path(__file__),Path('logs/roadmap/depleted_mining_fixture_worker_01.py'),Path('src/learning/production_clearance.py'),Path('src/learning/production_request.py'),Path('src/learning/production_execution.py'),Path('src/learning/gameplay.py'),Path('src/learning/live.py'),Path('src/bots/terran_primitives.py'),Path('src/runtime.py'),Path('src/runner.py')];bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 jobs=[dict(seed=825101,trace=str((OUT/'trace.jsonl').resolve()),replay=str((OUT/'game.SC2Replay').resolve()),static=str((OUT/'static.json').resolve()))]
 (OUT/'contract.json').write_text(json.dumps(dict(jobs=jobs,bindings=bindings,engineering_only=True,training=False,rl=False,game_seconds=150,wall_seconds=180,cpu_limit=80),indent=2)+'\n')
 assert psutil.cpu_percent(interval=1)<70
 stop,done=threading.Event(),threading.Event();samples=[]
 def watch():
  high=0
  while not done.is_set():
   cpu=psutil.cpu_percent(interval=1);samples.append(cpu);high=high+1 if cpu>80 else 0
   if high>=3:stop.set()
   done.wait(4)
 thread=threading.Thread(target=watch,daemon=True);thread.start();results=[]
 try:
  for job in jobs:
   if stop.is_set():break
   receipt=supervise(episode,(job,),180,stop_event=stop);receipt.setdefault('job',job);results.append(receipt);print(json.dumps({k:v for k,v in receipt.items() if k!='history'}),flush=True)
   if receipt['status'] not in ('completed',):break
 finally:done.set();thread.join(6)
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in bindings.items())
 (OUT/'report.json').write_text(json.dumps(dict(results=results,bindings=bindings,peak_cpu=max(samples,default=0),status='completed' if len(results)==1 and all(x['status'] in ('completed',) for x in results) else 'failed',training=False,rl=False),indent=2)+'\n')
if __name__=='__main__':main()
