"""Matched engineering canaries with a frozen old checkpoint; no learning claim."""
import hashlib,json,threading
from pathlib import Path
import psutil
from src.learning.entity_play import play_joint_job
from src.runtime import supervise
OUT=Path('logs/roadmap/broad-primitive-canary-01')
def main():
 OUT.mkdir(exist_ok=False)
 model=Path('logs/roadmap/joint-professional-fit-05/policy.npz')
 profile=Path('logs/roadmap/professional-observation-profile-01.json')
 paths=[Path(__file__),model,profile,Path('src/runtime.py'),Path('src/runner.py'),Path('src/bots/terran_primitives.py')]
 paths.extend(Path('src/learning').glob('*.py'))
 bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 jobs=[dict(controller='joint',policy=str(model.resolve()),observation_profile=str(profile.resolve()),primitive_assistance=enabled,engine_placement=True,wait_unavailable=True,max_game_step=8,map='AcropolisLE',race='Zerg',difficulty='VeryEasy',build='Macro',seed=820501,seconds=90,output=str((OUT/('assisted' if enabled else 'control')).resolve())) for enabled in (False,True)]
 (OUT/'contract.json').write_text(json.dumps(dict(jobs=jobs,bindings=bindings,training=False,rl=False,engineering_only=True,cpu_limit=80,wall_seconds_per_game=90,limits=['Frozen historical checkpoint; not fitted on repaired cohort.','Two 90-second games verify integration only, not learned strength.']),indent=2)+'\n')
 assert psutil.cpu_percent(interval=1)<70
 done=threading.Event();stop=threading.Event();samples=[]
 def watch():
  while not done.is_set():
   usage=psutil.cpu_percent(interval=1);samples.append(usage)
   if usage>80:stop.set()
   done.wait(1)
 thread=threading.Thread(target=watch,daemon=True);thread.start();results=[]
 try:
  for job in jobs:
   if stop.is_set():break
   receipt=supervise(play_joint_job,(job,),90,stop_event=stop);results.append(receipt)
   print(json.dumps(receipt),flush=True)
   if receipt['status'] not in ('completed','truncated'):break
 finally:done.set();thread.join(3)
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in bindings.items())
 for p in paths:
  dest=OUT/'source-snapshot'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 (OUT/'report.json').write_text(json.dumps(dict(status='completed' if len(results)==2 and all(r['status'] in ('completed','truncated') for r in results) else 'failed',results=results,peak_cpu=max(samples,default=0),bindings=bindings,training=False,rl=False),indent=2)+'\n')
if __name__=='__main__':main()
