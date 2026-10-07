"""Four bounded sequential addon command fixtures with whole-host CPU guard."""
import hashlib,json,threading,sys
from pathlib import Path
import psutil
sys.path.insert(0,str(Path(__file__).parent.resolve()))
from producer_binding_fixture_worker_03 import episode
from src.runtime import supervise
OUT=Path('logs/roadmap/producer-binding-fixture-03')
def main():
 OUT.mkdir(exist_ok=False);paths=[Path(__file__),Path('logs/roadmap/producer_binding_fixture_worker_03.py'),Path('src/learning/gameplay.py'),Path('src/learning/live.py'),Path('src/runtime.py'),Path('src/learning/producer_bindings.py')];bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 jobs=[]
 for i,case in enumerate(['producer_swap']):
  d=OUT/case;d.mkdir();jobs.append(dict(case=case,seed=819001+i,trace=str((d/'trace.jsonl').resolve()),replay=str((d/'game.SC2Replay').resolve()),catalog=str((d/'catalog.json').resolve())))
 (OUT/'contract.json').write_text(json.dumps(dict(jobs=jobs,bindings=bindings,engineering_only=True,training=False,rl=False,game_seconds=20,wall_seconds=60,cpu_limit=80),indent=2)+'\n')
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
   receipt=dict(job=job,**supervise(episode,(job,),60,stop_event=stop));results.append(receipt);print(json.dumps(receipt),flush=True)
   if receipt['status']!='completed':break
 finally:done.set();thread.join(6)
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in bindings.items())
 (OUT/'report.json').write_text(json.dumps(dict(results=results,bindings=bindings,peak_cpu=max(samples,default=0),status='completed' if len(results)==1 and all(x['status']=='completed' for x in results) else 'failed',training=False,rl=False),indent=2)+'\n')
if __name__=='__main__':main()
