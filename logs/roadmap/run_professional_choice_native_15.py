"""One learned conditional-choice canary with explicitly scripted execution."""
import ast,hashlib,json,math,threading
from pathlib import Path
import psutil,torch
from s2clientprotocol import query_pb2 as query,common_pb2 as common
from src.learning import entity_play
from src.learning.entity_play import JointImitationBot
from src.learning.entity_examples import state_inputs
from src.learning.entity_execution import project_observation
from src.learning.gameplay import Command
from src.learning.live import ability_query
from src.learning.production_component import ProductionComponent
from src.learning.production_execution import command_cost,eligible_actors,resource_affordable_choices,canonical,affordable_production_intent,unreserved_resources,command_point,builder_approach_points,preferred_production_intent,supply_feasible_choices
from src.learning.production_clearance import resolve_production_placement,claimed_geysers,reservations,site_reservations,refinery_sites
from src.learning.production_request import ProductionRequest
from src.runtime import supervise
ROOT=Path('logs/roadmap');OUT=ROOT/'professional-choice-native-15'
class ChoiceCanary(JointImitationBot):
 async def on_start(self):
  await super().on_start();self.choice,_=ProductionComponent.load(ROOT/'professional-choice-fit-04/choice.npz');self.prices={}
  for a in self.choice.abilities:
   try:self.prices[a]=command_cost(a,self.data)
   except ValueError:pass
  self.intent=None;self.unavailable_until={};self.prepared=None;self.pending={};self.pending_limit={};self.retry=None;self.retry_count=0;self.failed_sites=[];self.names={u['unit_id']:u['name'] for u in self.data['units']}
  self.agent.decide=lambda state,candidates=None:(self.prepared,44) if self.prepared else (None,None)
 async def run_primitives(self,state,protected,submitted=()):
  self.learned_control.update(self.pending)
  return await super().run_primitives(state,set(protected)|set(self.pending),submitted)
 async def reactive_supply_command(self,state,protected,submitted=()):
  commitments=[p.command.ability for p in self.pending.values()]
  if self.intent and not any(c.ability==self.intent['ability'] for c in submitted):commitments.append(self.intent['ability'])
  minerals,gas=unreserved_resources(state['player'],commitments,self.prices)
  adjusted=dict(state,player=dict(state['player'],minerals=minerals,vespene=gas))
  return await super().reactive_supply_command(adjusted,protected,submitted)
 async def on_step(self,iteration):
  self.prepared=None;self.travel_allowance=0;state=self.view.observe(self.state.response_observation);state['map_size']=[self.game_info.map_size.x,self.game_info.map_size.y];loop=state['game_loop'];event={'loop':loop}
  event['pending_status']={}
  for tag,pending in list(self.pending.items()):
   status=pending.status(state);event['pending_status'][tag]=status
   if status=='started':
    del self.pending[tag];self.pending_limit.pop(tag);self.retry=None;self.retry_count=0;self.failed_sites=[]
   elif status in ('failed','actor_missing'):
    self.retry=pending.command;self.retry_count+=1
    if self.retry_count>3:raise RuntimeError('Construction retry bound exceeded')
    if self.retry.target_point:self.failed_sites.append((*self.retry.target_point,2))
    event['retry_requested']=self.retry.as_dict();del self.pending[tag];self.pending_limit.pop(tag)
   elif loop-pending.loop>self.pending_limit[tag]:raise RuntimeError('Accepted production request never echoed its effect')
  self.learned_control=set(self.pending)
  if loop>=self.agent.next_loop:
   features=project_observation(dict(state,recent_commands=[]),self.observation_profile)
   x=state_inputs(features,*self.agent.vocabulary,products=self.agent.products,missing_fields=True)
   probabilities=self.choice.predict(x);funded=resource_affordable_choices(probabilities,self.prices,state['player']['minerals'],state['player']['vespene'])
   tags=[u['tag'] for u in state['units'] if u['alliance']==1]
   queried=(await self.client._execute(query=ability_query(tags))).query
   available={row.unit_tag:[a.ability_id for a in row.abilities] for row in queried.abilities}
   technical=(await self.client._execute(query=ability_query(tags,ignore_resources=True))).query
   technical_available={row.unit_tag:[a.ability_id for a in row.abilities] for row in technical.abilities}
   event['technical_available']=technical_available
   gas_sites=refinery_sites(state,self.catalog);event['refinery_sites']=[u['tag'] for u in gas_sites]
   technical_abilities={canonical(a,self.catalog) for abilities in technical_available.values() for a in abilities}
   supply_feasible=supply_feasible_choices(probabilities,state,self.data,[p.command.ability for p in self.pending.values()]);event['supply_feasible']=list(supply_feasible)
   technical_abilities.intersection_update(canonical(a,self.catalog) for a in supply_feasible)
   if self.retry and canonical(self.retry.ability,self.catalog) not in technical_abilities:
    event['invalidated_retry']=dict(command=self.retry.as_dict(),reason='native_prerequisite_site_or_supply_unavailable');self.retry=None;self.retry_count=0
   if not gas_sites:technical_abilities.discard(canonical(320,self.catalog))
   if self.intent and canonical(self.intent['ability'],self.catalog) not in technical_abilities:
    event['invalidated_intent']=dict(self.intent,reason='native_prerequisite_site_or_supply_unavailable');self.intent=None
   if self.intent is None:
    possible={a:p for a,p in probabilities.items() if a in self.prices and canonical(a,self.catalog) in technical_abilities}
    if possible:
     a=preferred_production_intent(possible,self.unavailable_until,loop)
     if a is not None:self.intent=dict(ability=a,loop=loop,price=self.prices[a]);event['created_intent']=dict(self.intent)
   if self.intent and loop-self.intent['loop']>1344:raise RuntimeError('Unissued intent stalled more than60 game seconds')
   commitments=[p.command.ability for p in self.pending.values()]
   minerals,gas=unreserved_resources(state['player'],commitments,self.prices)
   event['unreserved_resources']=[minerals,gas];event['intent']=dict(self.intent) if self.intent else None
   affordable=affordable_production_intent({self.intent['ability']:1} if self.intent else {},self.prices,minerals,gas)
   protected=set(self.pending) | self.scout.protected | (set(self.supply_pending[0].units) if self.supply_pending else set())
   candidates=[]
   for a in funded:
    if a!=affordable or self.retry and a!=self.retry.ability:continue
    actors=[u for u in eligible_actors(state,a,available,self.catalog,self.names,max_train_orders=2) if u['tag'] not in protected]
    if actors:candidates.append((a,actors))
   event['pending_protected']=sorted(self.pending)
   event['retry_intent']=self.retry.as_dict() if self.retry else None
   event.update(probabilities=probabilities,funded=list(funded),eligible=[a for a,_ in candidates],available=available)
   if candidates:
    a,actors=max(candidates,key=lambda pair:probabilities[pair[0]]);actor=min(actors,key=lambda u:u['tag']);name=self.catalog[a].get('friendly_name','');cmd=Command(a,(actor['tag'],),queue=name.startswith('Train ') and bool(actor.get('orders')))
    if name.startswith('Build ') and actor['unit_type']==45:
     if name=='Build Refinery':
      targets=gas_sites
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
     products=self.agent.products.get(str(a),[]);resolved,diagnostics=await resolve_production_placement(self.client,cmd,self.catalog,state,products[0] if products else 0,reservations(state,self.units_by_id,self.catalog)+self.failed_sites+[site for pending in self.pending.values() if pending.point and pending.building for site in site_reservations(next(iter(pending.products),0),pending.point,self.catalog[pending.command.ability].get('footprint_radius',1))])
     event['placement']=diagnostics;cmd=resolved[0] if resolved else None
     if cmd is None:
      self.unavailable_until[a]=loop+224;event['invalidated_intent']=dict(self.intent,reason='placement_search_unavailable',recheck_loop=loop+224);self.intent=None
    points=builder_approach_points(cmd,state) if cmd else []
    if cmd and points and actor['unit_type']==45:
     entries=[(u,p) for u in actors for p in points]
     paths=(await self.client._execute(query=query.RequestQuery(pathing=[query.RequestQueryPathing(unit_tag=u['tag'],end_pos=common.Point2D(x=p[0],y=p[1])) for u,p in entries]))).query.pathing
     assert len(paths)==len(entries)
     routes=[(r.distance,u['tag'],p) for r,(u,p) in zip(paths,entries) if r.distance>0]
     event['builder_paths']=[dict(tag=u['tag'],point=p,distance=r.distance) for r,(u,p) in zip(paths,entries)];event['builder_approach_points']=points
     if routes:
      distance,tag,point=min(routes)
      cmd=Command(a,(tag,),target_unit=cmd.target_unit,target_point=cmd.target_point,queue=cmd.queue)
      speed=self.units_by_id[45]['movement_speed'];self.travel_allowance=math.ceil(distance/speed*22.4);event['travel_allowance']=self.travel_allowance
     else:
      cmd=None;self.unavailable_until[a]=loop+224;event['invalidated_intent']=dict(self.intent,reason='no_positive_builder_route',recheck_loop=loop+224);self.intent=None
    event['unavailable_until']=dict(self.unavailable_until)
    self.prepared=cmd;event['selected']=cmd.as_dict() if cmd else None
   if not self.prepared:self.agent.next_loop=loop+8
  await super().on_step(iteration)
  if self.prepared and self.agent.history and self.agent.history[-1]['game_loop']==loop:
   remembered=self.agent.history[-1]
   accepted=Command(remembered['ability'],tuple(remembered['units']),target_unit=remembered.get('target_unit'),target_point=tuple(remembered['target_point']) if remembered.get('target_point') else None,queue=remembered.get('queue',False))
   tag=accepted.units[0];assert tag not in self.pending;self.pending[tag]=ProductionRequest(accepted,state,self.data);self.pending_limit[tag]=448+self.travel_allowance;event['accepted_pending']=accepted.as_dict();assert self.intent['ability']==accepted.ability;event['submitted_intent']=dict(self.intent);self.intent=None
  self.stream.write(json.dumps(dict(phase='production_choice',observation=state,choice=event),separators=(',',':'))+'\n')
def play(job):
 torch.set_num_threads(2);original=entity_play.JointImitationBot;entity_play.JointImitationBot=ChoiceCanary
 try:return entity_play.play_joint_job(job)
 finally:entity_play.JointImitationBot=original

def main():
 OUT.mkdir(exist_ok=False)
 verified=json.loads((ROOT/'professional-resource-filter-01/verification.json').read_text());assert verified['status']=='verified_resource_only_inference_gates_passed'
 for p,h in verified['bindings'].items():
  if p=='src/learning/production_execution.py':
   prior=ROOT/'professional-choice-native-04/source-snapshot'/p
   assert hashlib.sha256(prior.read_bytes()).hexdigest()==h
   def functions(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
   old,new=functions(prior),functions(Path(p))
   assert set(new)==set(old)|{'affordable_production_intent','unreserved_resources','command_point','builder_approach_points','preferred_production_intent','supply_feasible_choices'} and all(old[k]==new[k] for k in old if k!='eligible_actors')
  else:assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
 profile=ROOT/'professional-observation-profile-01.json';job=dict(controller='goal-first',policy=str((ROOT/'expanded-professional-imitation-01/policy.npz').resolve()),observation_profile=str(profile.resolve()),output=str((OUT/'Zerg').resolve()),map='AcropolisLE',race='Zerg',difficulty='VeryEasy',build='Macro',seed=824101,seconds=600,max_game_step=8,primitive_assistance=True,reactive_supply=True,engine_placement=True,wait_unavailable=True)
 paths=[Path(__file__),profile,ROOT/'professional-choice-fit-04/choice.npz',ROOT/'professional-resource-filter-01/verification.json',*[p for p in Path('src/learning').glob('*.py')]];bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 (OUT/'contract.json').write_text(json.dumps(dict(job=job,bindings=bindings,training=False,rl=False,cpu_limit=80,wall_limit=180,decisions='At most two observed Train orders per producer; queued Train commands explicitly queue=True. Retain highest-probability priced technically available intent from resource-ignoring query; reserve pending request costs until verified start; no cheaper fallback; waiting funded/actor intent expires after60game seconds; physical placement or path rejection invalidates intent and withholds that ability for224loops (10game seconds), then permits native recheck; no strategic building caps; withhold Train choices lacking supply after observed waiting orders and unacknowledged requests, releasing stale supply-blocked intent/retry; reactive supply respects reservations; no worker/army/building quotas. Unknown prices withheld. Actor/placement scripted; shared refinery_sites considers unoccupied observed gas near all completed owned ground bases; no gas intent when no such site exists. Fixed44 cadence,8-loop retries,independent pending requests keyed by actor until order/foundation echo; all pending actors protected, pending construction sites reserved,448-loop failure timeout. Delayed failures trigger at most three retries of the same intent; physical reservations and failed-site avoidance; pending builders remain protected until actual foundation. Placement centers aligned with footprint grid; point-target builder routes use actual grid point; unit-target Refinery routes use eight observed-radius approach points outside blocked geyser center; builders selected by shortest positive queried route; timeout includes conservative route/movement-speed allowance plus448loops.',max_train_orders=2,gates=dict(worker_births=8,military_births=20,completed_production_buildings=2,action_errors=0)),indent=2)+'\n')
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
