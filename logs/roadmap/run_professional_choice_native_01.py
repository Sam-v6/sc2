"""One learned conditional-choice canary with explicitly scripted execution."""
import hashlib,json,math,threading
from pathlib import Path
import psutil,torch
from src.learning import entity_play
from src.learning.entity_play import JointImitationBot
from src.learning.entity_examples import state_inputs
from src.learning.entity_execution import project_observation
from src.learning.gameplay import Command
from src.learning.live import ability_query
from src.learning.production_component import ProductionComponent
from src.learning.production_execution import command_cost,eligible_actors,resource_affordable_choices,canonical
from src.learning.production_clearance import resolve_production_placement,claimed_geysers
from src.runtime import supervise
ROOT=Path('logs/roadmap');OUT=ROOT/'professional-choice-native-01'
class ChoiceCanary(JointImitationBot):
 async def on_start(self):
  await super().on_start();self.choice,_=ProductionComponent.load(ROOT/'professional-choice-fit-04/choice.npz');self.prices={}
  for a in self.choice.abilities:
   try:self.prices[a]=command_cost(a,self.data)
   except ValueError:pass
  self.prepared=None;self.pending=None;self.names={u['unit_id']:u['name'] for u in self.data['units']}
  self.agent.decide=lambda state,candidates=None:(self.prepared,44) if self.prepared else (None,None)
 async def on_step(self,iteration):
  self.prepared=None;state=self.view.observe(self.state.response_observation);state['map_size']=[self.game_info.map_size.x,self.game_info.map_size.y];loop=state['game_loop'];event={'loop':loop}
  if self.pending:
   cmd,issued_loop=self.pending
   own=[u for u in state['units'] if u['alliance']==1]
   name=self.catalog[cmd.ability].get('friendly_name','')
   if name.startswith('Build ') and cmd.target_point:
    products=self.agent.products.get(str(cmd.ability),[])
    seen=any(u['unit_type'] in products and math.dist(u['position'][:2],cmd.target_point)<1 for u in own)
   else:seen=any(u['tag'] in cmd.units and any(canonical(o['ability_id'],self.catalog)==canonical(cmd.ability,self.catalog) for o in u.get('orders',[])) for u in own)
   event['pending_effect_seen']=seen
   if seen:self.pending=None
   elif loop-issued_loop>448:raise RuntimeError('Accepted production request never echoed its effect')
  if loop>=self.agent.next_loop and not self.pending:
   features=project_observation(dict(state,recent_commands=[]),self.observation_profile)
   x=state_inputs(features,*self.agent.vocabulary,products=self.agent.products,missing_fields=True)
   probabilities=self.choice.predict(x);funded=resource_affordable_choices(probabilities,self.prices,state['player']['minerals'],state['player']['vespene'])
   tags=[u['tag'] for u in state['units'] if u['alliance']==1]
   queried=(await self.client._execute(query=ability_query(tags))).query
   available={row.unit_tag:[a.ability_id for a in row.abilities] for row in queried.abilities}
   protected=self.scout.protected | (set(self.supply_pending[0].units) if self.supply_pending else set())
   candidates=[]
   for a in funded:
    if a not in self.prices:continue
    actors=[u for u in eligible_actors(state,a,available,self.catalog,self.names) if u['tag'] not in protected]
    if actors:candidates.append((a,actors))
   event.update(probabilities=probabilities,funded=list(funded),eligible=[a for a,_ in candidates],available=available)
   if candidates:
    a,actors=max(candidates,key=lambda pair:probabilities[pair[0]]);actor=min(actors,key=lambda u:u['tag']);name=self.catalog[a].get('friendly_name','');cmd=Command(a,(actor['tag'],))
    if name.startswith('Build ') and actor['unit_type']==45:
     if name=='Build Refinery':
      claimed=claimed_geysers(state,self.catalog);targets=[u for u in state['units'] if u['alliance']==3 and u.get('vespene_contents',0)>0 and u['tag'] not in claimed and math.dist(u['position'][:2],tuple(self.start_location))<15]
      if targets:cmd=Command(a,cmd.units,target_unit=min(targets,key=lambda u:math.dist(u['position'][:2],actor['position'][:2]))['tag'])
      else:cmd=None
     else:
      point=tuple(self.start_location.towards(self.game_info.map_center,16))
      if name=='Build CommandCenter':
       bases=[u for u in state['units'] if u['alliance']==1 and u['unit_type'] in (18,132,130)]
       sites=[p for p in self.expansion_locations_list if all(math.dist(tuple(p),u['position'][:2])>6 for u in bases)]
       if sites:point=tuple(min(sites,key=lambda p:p.distance_to(self.start_location)))
      cmd=Command(a,cmd.units,target_point=point)
    if cmd and self.catalog[a].get('is_building'):
     products=self.agent.products.get(str(a),[]);resolved,diagnostics=await resolve_production_placement(self.client,cmd,self.catalog,state,products[0] if products else 0,[])
     event['placement']=diagnostics;cmd=resolved[0] if resolved else None
    self.prepared=cmd;event['selected']=cmd.as_dict() if cmd else None
   if not self.prepared:self.agent.next_loop=loop+8
  before=len(self.agent.history);await super().on_step(iteration)
  if self.prepared and self.agent.history and self.agent.history[-1]['game_loop']==loop:
   self.pending=(self.prepared,loop);event['accepted_pending']=self.prepared.as_dict()
  self.stream.write(json.dumps(dict(phase='production_choice',observation=state,choice=event),separators=(',',':'))+'\n')
def play(job):
 torch.set_num_threads(2);original=entity_play.JointImitationBot;entity_play.JointImitationBot=ChoiceCanary
 try:return entity_play.play_joint_job(job)
 finally:entity_play.JointImitationBot=original
 def_unused=None

def main():
 OUT.mkdir(exist_ok=False)
 verified=json.loads((ROOT/'professional-resource-filter-01/verification.json').read_text());assert verified['status']=='verified_resource_only_inference_gates_passed'
 for p,h in verified['bindings'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
 profile=ROOT/'professional-observation-profile-01.json';job=dict(controller='goal-first',policy=str((ROOT/'expanded-professional-imitation-01/policy.npz').resolve()),observation_profile=str(profile.resolve()),output=str((OUT/'Zerg').resolve()),map='AcropolisLE',race='Zerg',difficulty='VeryEasy',build='Macro',seed=824101,seconds=600,max_game_step=8,primitive_assistance=True,reactive_supply=True,engine_placement=True,wait_unavailable=True)
 paths=[Path(__file__),profile,ROOT/'professional-choice-fit-04/choice.npz',ROOT/'professional-resource-filter-01/verification.json',*[p for p in Path('src/learning').glob('*.py')]];bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 (OUT/'contract.json').write_text(json.dumps(dict(job=job,bindings=bindings,training=False,rl=False,cpu_limit=80,wall_limit=180,decisions='Learned highest-probability funded native-available production ability; no worker/army/building quotas. Unknown prices withheld. Actor/placement scripted. Fixed44 cadence,8-loop retries,one accepted request pending until order/foundation echo,448-loop failure timeout.',gates=dict(worker_births=8,military_births=20,completed_production_buildings=2,action_errors=0)),indent=2)+'\n')
 stop,done=threading.Event(),threading.Event();samples=[]
 def watch():
  high=0
  while not done.is_set():
   cpu=psutil.cpu_percent(interval=1);samples.append(cpu);high=high+1 if cpu>80 else 0
   if high>=3:stop.set()
   done.wait(1)
 thread=threading.Thread(target=watch,daemon=True);thread.start()
 try:result=supervise(play,(job,),180,stop_event=stop)
 finally:done.set();thread.join(3)
 for p in paths:
  assert hashlib.sha256(p.read_bytes()).hexdigest()==bindings[str(p)];dest=OUT/'source-snapshot'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 (OUT/'report.json').write_text(json.dumps(dict(result=result,peak_cpu=max(samples,default=0),samples=samples,bindings=bindings,training=False,rl=False),indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
