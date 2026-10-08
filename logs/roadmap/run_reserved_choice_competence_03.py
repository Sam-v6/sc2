"""Frozen three-race actual-game diagnostic after the passed production canary."""
import hashlib,json,sys,threading
from pathlib import Path
import psutil
sys.path.insert(0,str(Path(__file__).parent.resolve()))
from run_professional_choice_native_13 import play
from src.runtime import supervise
ROOT=Path('logs/roadmap');OUT=ROOT/'reserved-choice-competence-03'
def main():
 OUT.mkdir(exist_ok=False)
 proof=json.loads((ROOT/'professional-choice-native-11/verification.json').read_text());assert proof['gate_pass']
 for p,h in proof['bindings'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
 base=json.loads((ROOT/'professional-choice-native-11/contract.json').read_text())['job']
 jobs=[dict(base,race=r,seed=824201+i,seconds=1200,output=str((OUT/r).resolve())) for i,r in enumerate(('Terran','Zerg','Protoss'))]
 paths=[Path(__file__),ROOT/'run_professional_choice_native_13.py',ROOT/'professional-choice-fit-04/choice.npz',ROOT/'professional-choice-native-11/verification.json',*[p for p in Path('src/learning').glob('*.py')]];bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 (OUT/'contract.json').write_text(json.dumps(dict(jobs=jobs,bindings=bindings,choice_checkpoint=str(ROOT/'professional-choice-fit-04/choice.npz'),bootstrap_policy_role='Vocabulary and adapter initialization only; actual macro decisions are the independently verified production choice checkpoint.',training=False,rl=False,cpu_limit=80,wall_limit_per_game=300,game_seconds=1200,execution='Sequential CPU-only games with2torch threads; fixed model, reserved intents, native-verified gas sites, scripted timing/actor/placement/mining/supply/scout/micro. No quotas or strategic priorities added.',gate='Three actual Victories at VeryEasy plus zero immediate and delayed action errors. Cutoffs and failures do not count as wins. This does not establish Hard competence or full human imitation.'),indent=2)+'\n')
 stop,done=threading.Event(),threading.Event();samples=[]
 def watch():
  high=0
  while not done.is_set():
   cpu=psutil.cpu_percent(interval=1);samples.append(cpu);high=high+1 if cpu>80 else 0
   if high>=3:stop.set()
   done.wait(1)
 thread=threading.Thread(target=watch,daemon=True);thread.start();results=[]
 try:
  for job in jobs:
   if stop.is_set():break
   result=supervise(play,(job,),300,stop_event=stop);results.append(dict(race=job['race'],receipt=result))
   (OUT/'progress.json').write_text(json.dumps(dict(results=results,samples=samples),indent=2)+'\n')
   print(json.dumps(dict(race=job['race'],status=result['status'],result=result.get('result'),wall=result.get('wall_seconds'))),flush=True)
   if result['status'] not in ('completed','truncated'):break
 finally:done.set();thread.join(3)
 for p,h in bindings.items():
  source=Path(p);assert hashlib.sha256(source.read_bytes()).hexdigest()==h;relative=source.relative_to(Path.cwd()) if source.is_absolute() else source;dest=OUT/'source-snapshot'/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes())
 (OUT/'report.json').write_text(json.dumps(dict(results=results,peak_cpu=max(samples,default=0),samples=samples,bindings=bindings,training=False,rl=False),indent=2)+'\n')
if __name__=='__main__':main()
