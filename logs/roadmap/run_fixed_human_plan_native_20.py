"""Four bounded sequential addon command fixtures with whole-host CPU guard."""
import hashlib,json,threading,sys
from pathlib import Path
import psutil
sys.path.insert(0,str(Path(__file__).parent.resolve()))
from src.learning.fixed_plan_play import play_fixed_human_plan as episode
from src.runtime import supervise
OUT=Path('logs/roadmap/fixed-human-plan-native-20')
def main():
 OUT.mkdir(exist_ok=False);paths=[Path(__file__),Path('src/learning/fixed_plan_play.py'),Path('src/learning/gameplay.py'),Path('src/learning/live.py'),Path('src/runtime.py'),Path('src/learning/producer_bindings.py'),Path('src/learning/production_execution.py'),Path('src/learning/tournament_record.py'),Path('src/runner.py'),Path('logs/roadmap/pro-preconverted-probe-01/fall-record-870.bin'),Path('src/learning/production_primitives.py'),Path('src/bots/terran_primitives.py'),Path('logs/roadmap/fixed-human-production-plan-05/plan.json')];bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 jobs=[dict(seed=817501,plan='logs/roadmap/fixed-human-production-plan-05/plan.json',record='logs/roadmap/pro-preconverted-probe-01/fall-record-870.bin',output=str((OUT/'episode').resolve()))]
 (OUT/'contract.json').write_text(json.dumps(dict(jobs=jobs,bindings=bindings,engineering_only=True,training=False,rl=False,game_seconds=600,wall_seconds=300,cpu_limit=80),indent=2)+'\n')
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
   receipt=supervise(episode,(job,),300,stop_event=stop);receipt.setdefault('job',job);results.append(receipt);print(json.dumps({k:v for k,v in receipt.items() if k!='history'}),flush=True)
   if receipt['status'] not in ('finished','diverged'):break
 finally:done.set();thread.join(6)
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in bindings.items())
 (OUT/'report.json').write_text(json.dumps(dict(results=results,bindings=bindings,peak_cpu=max(samples,default=0),status='completed' if len(results)==1 and all(x['status'] in ('finished','diverged') for x in results) else 'failed',training=False,rl=False),indent=2)+'\n')
if __name__=='__main__':main()
