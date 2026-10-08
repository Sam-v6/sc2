"""Re-import existing nonreserved human examples without changing old evidence."""
import hashlib,json,threading
from pathlib import Path
import psutil
from src.learning.tournament_import import import_game
from src.runtime import supervise

OUT=Path('logs/roadmap/human-visibility-reimport-01')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 jobs=json.loads((OUT/'jobs.json').read_text())
 paths=[Path(__file__),OUT/'jobs.json',Path('src/learning/tournament_import.py'),Path('src/learning/tournament_observation.py'),Path('src/learning/gameplay.py')]
 paths += [Path(j['original_job']) for j in jobs]+[Path(j['old'])/'dataset.json' for j in jobs]
 bindings={str(p):sha(p) for p in paths}
 (OUT/'contract.json').write_text(json.dumps(dict(bindings=bindings,jobs=jobs,training=False,rl=False,whole_host_cpu_limit=80),indent=2)+'\n')
 stop,done=threading.Event(),threading.Event();samples=[]
 def watch():
  high=0
  while not done.is_set():
   cpu=psutil.cpu_percent(interval=1);samples.append(cpu);high=high+1 if cpu>80 else 0
   if high>=3:stop.set()
   done.wait(4)
 assert psutil.cpu_percent(interval=1)<70
 t=threading.Thread(target=watch,daemon=True);t.start();results=[]
 try:
  for entry in jobs:
   if stop.is_set():break
   r=supervise(import_game,(entry['job'],),300,stop_event=stop)
   # Full source/label accounting remains in each dataset receipt.
   item=dict(source=entry['old'],output=entry['job']['output'],role=entry['role'],status=r['status'],error=r.get('error'))
   results.append(item);(OUT/'progress.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(item),flush=True)
   if r['status']!='completed':break
 finally:
  done.set();t.join(6)
 assert all(sha(p)==h for p,h in bindings.items())
 (OUT/'report.json').write_text(json.dumps(dict(status='completed' if len(results)==14 and all(r['status']=='completed' for r in results) else 'stopped',results=results,bindings=bindings,peak_cpu=max(samples,default=0),training=False,rl=False),indent=2)+'\n')
if __name__=='__main__':main()
