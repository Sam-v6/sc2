"""Fixed source instructions with physical primitives; no learned policy or RL."""
import gzip,json,math
from pathlib import Path
from sc2.bot_ai import BotAI
from sc2.data import Race,Difficulty,AIBuild
from sc2.main import run_game
from sc2.player import Bot,Computer
from sc2.position import Point2
from s2clientprotocol import sc2api_pb2 as pb,query_pb2 as query,common_pb2 as common
from src.runner import validate_map
from src.learning.gameplay import Command,PlayerView,protocol_dict
from src.learning.live import ability_query,issue
from src.learning.tournament_record import decode_record
from src.learning.producer_bindings import ProducerBindings
from src.learning.production_primitives import primitive_assistance,scripted_army_destination

class FixedPlan(BotAI):
 def __init__(self,job,stream):
  super().__init__();self.job=job;self.stream=stream;self.plan=json.loads(Path(job['plan']).read_text());self.tickets=self.plan['tickets'];self.view=PlayerView();self.bindings=ProducerBindings();self.index=0;self.pending=[];self.history=[];self.divergence=None;self.error=None;self.frames=0;self.attacking=False;self.search=0;self.next_mining=0;self.block=None
  record=decode_record(Path(job['record']).read_bytes());f=record['units']['fields'];self.entities={};self.neutrals={}
  for i,step in enumerate(record['units']['step']):
   tag=int(f['id'][i])
   if f['alliance'][i]==1 and tag not in self.entities:
    self.entities[tag]=dict(loop=int(record['steps']['game_loop'][step]),kind=int(f['unitType'][i]),point=list(map(float,f['pos'][i][:2])))
  n=record['neutral_units']['fields'] if 'neutral_units' in record else record['neutral']['fields']
  for i,tag in enumerate(n['id']):self.neutrals.setdefault(int(tag),list(map(float,n['pos'][i][:2])))
 async def on_start(self):
  self.client.game_step=8
  self.data=protocol_dict((await self.client._execute(data=pb.RequestData(ability_id=True,unit_type_id=True,upgrade_id=True))).data)
  self.catalog={a['ability_id']:a for a in self.data['abilities']};self.types={u['unit_id']:u for u in self.data['units']}
  self.products={}
  for u in self.data['units']:
   if 8 in u.get('attributes',[]) and u.get('ability_id'):
    self.products.setdefault(u['ability_id'],[]).append(u['unit_id'])
  source=self.entities[4347920385]['point']
  if math.dist(source,tuple(self.start_location))>.1:raise ValueError('Source spawn mismatch: '+str(tuple(self.start_location)))
 def source_product(self,ticket,point):
  kinds=self.products.get(ticket['command']['ability'],[])
  matches=[tag for tag,e in self.entities.items() if e['loop']>=ticket['loop'] and e['kind'] in kinds and math.dist(e['point'],point)<.1]
  return matches[0] if len(matches)==1 else None
 async def on_step(self,iteration):
  try:
   state=self.view.observe(self.state.response_observation);loop=state['game_loop'];own=[u for u in state['units'] if u['alliance']==1];self.frames+=1
   if not self.bindings.tags:
    bases=[u for u in own if u['unit_type']==18];assert len(bases)==1
    self.bindings.bind(4347920385,bases[0]['tag'])
   for pending in list(self.pending):
    candidates=[u for u in own if u['tag'] not in pending['before'] and u['unit_type'] in pending['kinds'] and math.dist(u['position'][:2],pending['point'])<.1]
    if len(candidates)==1:
     self.bindings.bind(pending['source'],candidates[0]['tag']);self.pending.remove(pending)
     self.history.append(dict(event='foundation_bound',loop=loop,source=pending['source'],native=candidates[0]['tag']))
    elif len(candidates)>1:raise ValueError('Ambiguous native foundation')
   commands=[];sent=None;self.block=None
   if self.index<len(self.tickets):
    ticket=self.tickets[self.index];source=ticket['command'];ability=source['ability'];point=source.get('target_point');target=None
    if loop>=ticket['loop']:
     actor=None
     if ticket['actor_types']==[45]:
      location=point or self.neutrals.get(source.get('target_unit'))
      candidates=[u for u in own if u['unit_type']==45 and not any(self.catalog.get(o['ability_id'],{}).get('friendly_name','').startswith('Build ') for o in u.get('orders',[]))]
      if candidates:actor=min(candidates,key=lambda u:math.dist(u['position'][:2],location or tuple(self.start_location)))
     elif len(source['units'])==1:actor=self.bindings.resolve(source['units'][0],state)
     if actor is None:self.block='source_actor_unbound_or_lost'
     elif source.get('target_unit'):
      location=self.neutrals.get(source['target_unit'])
      candidates=[u for u in state['units'] if u['alliance']==3 and location and math.dist(u['position'][:2],location)<.1 and u.get('display_type',1)==1]
      if len(candidates)==1:target=candidates[0]['tag']
      else:self.block='unobserved_or_ambiguous_target'
     if actor and self.block is None:
      packet=(await self.client._execute(query=ability_query([actor['tag']]))).query
      available={a.ability_id for entry in packet.abilities for a in entry.abilities}
      if ability not in available:self.block='native_ability_unavailable'
      if self.catalog[ability].get('friendly_name','').startswith(('Lift','Land','Build TechLab','Build Reactor')) and actor.get('orders'):self.block='producer_busy'
     if actor and self.block is None:
      command=Command(ability,(actor['tag'],),target_unit=target,target_point=tuple(point) if point else None,queue=source.get('queue',False))
      expected=None;product_point=point
      if ticket['name'].startswith('Build '):
       if target:product_point=next(u['position'][:2] for u in state['units'] if u['tag']==target)
       elif ticket['name'].startswith(('Build TechLab','Build Reactor')):
        product_point=[actor['position'][0]+2.5,actor['position'][1]-.5] if not point else [point[0]+2.5,point[1]-.5]
       expected=self.source_product(ticket,product_point) if product_point else None
       if expected is None:self.block='source_foundation_identity_unresolved'
      if self.block is None and (point or target) and (ticket['name'].startswith(('Build ','Land'))):
       check_point=point if point else product_point
       response=(await self.client._execute(query=query.RequestQuery(placements=[query.RequestQueryBuildingPlacement(ability_id=ability,placing_unit_tag=actor['tag'],target_pos=common.Point2D(x=check_point[0],y=check_point[1]))]))).query
       if response.placements[0].result!=1:self.block='native_exact_placement:'+str(response.placements[0].result)
      if self.block is None:
       commands=[command];sent=dict(ticket=self.index,loop=loop,source_loop=ticket['loop'],sequence=ticket['sequence'],name=ticket['name'],command=command.as_dict())
       if expected is not None:self.pending.append(dict(source=expected,point=product_point,kinds=self.products[ability],before=[u['tag'] for u in own]))
     if loop-ticket['loop']>672:
      self.divergence=dict(loop=loop,ticket=self.index,source_loop=ticket['loop'],name=ticket['name'],reason=self.block or 'timing_deadline',player=state['player'])
   selected={tag for c in commands for tag in c.units}
   selected.update(u['tag'] for u in own if u.get('orders') and any(self.catalog.get(o['ability_id'],{}).get('friendly_name','').startswith('Build ') for o in u['orders']))
   destination,self.attacking,self.search=scripted_army_destination(state,self.types,tuple(self.start_location),tuple(self.enemy_start_locations[0]),tuple(self.game_info.map_center),[tuple(p) for p in self.expansion_locations_list],self.attacking,self.search)
   mining=loop>=self.next_mining
   if mining:self.next_mining=loop+24
   assists=primitive_assistance(state,selected,self.types,self.catalog,destination,lambda p:self.in_map_bounds(Point2(p)) and self.in_pathing_grid(Point2(p)),mining)
   batch=commands+assists
   result=await issue(self.client,batch) if batch else pb.ResponseAction()
   if sent:
    sent['result']=result.result[0];self.history.append(sent)
    if result.result[0]==1:self.index+=1
    else:self.divergence=dict(loop=loop,ticket=self.index,reason='rejected_command',detail=sent)
   self.stream.write(json.dumps(dict(loop=loop,observation=state,index=self.index,block=self.block,bindings=self.bindings.tags,pending=self.pending,execution=sent,commands=[c.as_dict() for c in batch],results=list(result.result),divergence=self.divergence))+'\n')
   if self.divergence:await self.client.leave()
  except Exception as e:self.error=repr(e);raise

def episode(job):
 out=Path(job['output']);out.mkdir(exist_ok=False)
 with gzip.open(out/'trace.jsonl.gz','xt') as stream:
  bot=FixedPlan(job,stream);result=run_game(validate_map('AcropolisLE'),[Bot(Race.Terran,bot),Computer(Race.Zerg,Difficulty.VeryEasy,AIBuild.Rush)],realtime=False,random_seed=job['seed'],game_time_limit=600,save_replay_as=str(out/'game.SC2Replay'))
 assert bot.error is None,bot.error
 report=dict(status='diverged' if bot.divergence else 'finished',result=result.name,frames=bot.frames,instructions_sent=bot.index,total=len(bot.tickets),divergence=bot.divergence,history=bot.history,training=False,rl=False,fixed_human_plan=True,job=job)
 (out/'episode.json').write_text(json.dumps(report,indent=2)+'\n')
 return report
