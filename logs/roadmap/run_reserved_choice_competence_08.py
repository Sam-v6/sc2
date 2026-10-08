"""Frozen three-race actual-game diagnostic after the passed production canary."""
import hashlib,json,sys,threading
from pathlib import Path
import psutil
sys.path.insert(0,str(Path(__file__).parent.resolve()))
from run_professional_choice_native_18 import play
from src.runtime import supervise
ROOT=Path('logs/roadmap');OUT=ROOT/'reserved-choice-competence-08'
def main():
 OUT.mkdir(exist_ok=False)
 prior_root=ROOT/'reserved-choice-competence-07';prior=json.loads((prior_root/'contract.json').read_text())
 import ast
 def functions(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
 for p,h in prior['bindings'].items():
  source=Path(p);rel=source.relative_to(Path.cwd()) if source.is_absolute() else source;saved=prior_root/'source-snapshot'/rel
  assert hashlib.sha256(saved.read_bytes()).hexdigest()==h,p
  if p=='src/learning/production_execution.py':
   old,new=functions(saved),functions(source)
   assert set(new)==set(old) and all(old[k]==new[k] for k in old if k!='preferred_production_intent')
  elif p not in ('src/bots/terran_primitives.py','src/learning/production_request.py','src/learning/production_clearance.py','src/learning/entity_play.py'):assert hashlib.sha256(source.read_bytes()).hexdigest()==h,p
 fixture=json.loads((ROOT/'occupied-addon-fixture-01/report.json').read_text());assert fixture['status']=='completed'
 for p,h in fixture['bindings'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
 base=json.loads((ROOT/'professional-choice-native-11/contract.json').read_text())['job']
 jobs=[dict(base,race='Protoss',seed=824203,seconds=1200,output=str((OUT/'Protoss').resolve()))]
 paths=[Path(__file__),ROOT/'run_professional_choice_native_18.py',ROOT/'professional-choice-fit-04/choice.npz',ROOT/'professional-choice-native-11/verification.json',Path('src/bots/terran_primitives.py'),ROOT/'depleted-mining-fixture-01/report.json',*[p for p in Path('src/learning').glob('*.py')]];bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 (OUT/'contract.json').write_text(json.dumps(dict(jobs=jobs,bindings=bindings,choice_checkpoint=str(ROOT/'professional-choice-fit-04/choice.npz'),bootstrap_policy_role='Vocabulary and adapter initialization only; actual macro decisions are the independently verified production choice checkpoint.',training=False,rl=False,cpu_limit=80,wall_limit_per_game=300,game_seconds=1200,execution='Sequential CPU-only games with2torch threads; fixed model, reserved intents, native-verified gas sites, scripted timing/actor/placement/mining/supply/scout/micro. Physical placement/path rejection releases the intent and withholds that ability224loops before recheck. Training choices require supply after waiting queue and pending reservations; stale supply-blocked intent/retry invalidated. Depleted local mineral patches permit visible safe remote harvesting. CommandCenters retain exact requested expansion sites; try subsequent unoccupied native expansion sites on placement rejection. A delayed production failure displaces an unrelated retained intent; retry selection explicitly prioritizes the failed ability, without a contradictory second candidate filter. Addon-pad ground blockers withhold issue and request physical clearance held through foundation; failed-request attempt chain is independent of unrelated completion. Includes separately native-verified Liberator micro. No quotas or strategic priorities added.',gate='Single matched Protoss retry diagnostic: no unrelated-intent retry deadlock; normal finish and zero errors assessed separately. Retry bound is three per logical failed-request chain; unrelated production cannot reset attempt number. Actual victory is reported separately; no all-race or Hard claim.'),indent=2)+'\n')
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
