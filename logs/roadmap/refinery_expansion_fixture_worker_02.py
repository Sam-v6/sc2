"""Engineering fixture: real Refinery builds at home and a debug-created expansion."""
import json,math
from pathlib import Path
from sc2.bot_ai import BotAI
from sc2.data import Race,Difficulty
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.main import run_game
from sc2.player import Bot,Computer
from sc2.position import Point2
from s2clientprotocol import sc2api_pb2 as pb
from src.runner import validate_map
from src.learning.gameplay import Command,PlayerView,protocol_dict
from src.learning.live import issue
from src.learning.production_clearance import refinery_sites,claimed_geysers,resolve_production_placement
from src.learning.production_request import ProductionRequest
from src.bots.terran_primitives import mining_commands
class Fixture(BotAI):
 def __init__(self,job,stream):
  super().__init__();self.job=job;self.stream=stream;self.view=PlayerView();self.phase='home';self.pending={};self.home_targets=[];self.expansion_target=None;self.error=None;self.frames=0
 async def on_start(self):
  self.client.game_step=8
  self.data=protocol_dict((await self.client._execute(data=pb.RequestData(ability_id=True,unit_type_id=True,upgrade_id=True))).data)
  self.catalog={a['ability_id']:a for a in self.data['abilities']}
  self.home=tuple(self.start_location);self.expansion=tuple(min((p for p in self.expansion_locations_list if p.distance_to(self.start_location)>10),key=lambda p:p.distance_to(self.start_location)))
  await self.client.debug_all_resources()
  await self.client.debug_create_unit([[U.COMMANDCENTER,1,Point2(self.expansion),1],[U.SCV,4,Point2((self.expansion[0]+5,self.expansion[1]+5)),1]])
  Path(self.job['static']).write_text(json.dumps(dict(game_data=self.data,home=self.home,expansion=self.expansion,debug_setup='Resources,one completed expansion CommandCenter,four SCVs; all three Refineries are built through normal commands.'))+'\n')
 async def on_step(self,iteration):
  try:
   packet=self.state.response_observation;state=self.view.observe(packet);state['map_size']=[self.game_info.map_size.x,self.game_info.map_size.y];loop=state['game_loop'];events=[];commands=[];placements=[]
   for tag,request in list(self.pending.items()):
    status=request.status(state);events.append(dict(actor=tag,status=status))
    if status=='started':del self.pending[tag]
    elif status in ('failed','actor_missing'):raise RuntimeError('Refinery request failed: '+status)
   own=[u for u in state['units'] if u['alliance']==1];ready=[u for u in own if u['unit_type']==20 and u.get('build_progress',1)>=1];sites=refinery_sites(state,self.catalog)
   if self.phase=='home' and not self.home_targets:
    home_sites=[u for u in sites if math.dist(u['position'][:2],self.home)<15];assert len(home_sites)==2
    workers=[u for u in own if u['unit_type']==45 and math.dist(u['position'][:2],self.home)<15]
    for site in home_sites:
     worker=min(workers,key=lambda w:math.dist(w['position'][:2],site['position'][:2]));workers.remove(worker)
     commands.append(Command(320,(worker['tag'],),target_unit=site['tag']));self.home_targets.append(site['tag'])
   elif self.phase=='home' and len(ready)==2:
    assert not set(self.home_targets)&{u['tag'] for u in sites}
    targets=[u for u in sites if math.dist(u['position'][:2],self.expansion)<15];assert len(targets)==2
    site=min(targets,key=lambda u:u['tag']);workers=[u for u in own if u['unit_type']==45 and not any(self.catalog.get(o['ability_id'],{}).get('friendly_name','').startswith('Build ') for o in u.get('orders',[]))]
    worker=min(workers,key=lambda w:math.dist(w['position'][:2],site['position'][:2]));commands=[Command(320,(worker['tag'],),target_unit=site['tag'])];self.expansion_target=site['tag'];self.phase='expansion'
   elif self.phase=='expansion' and len(ready)==3:self.phase='mining'
   resolved=[]
   for command in commands:
    batch,trace=await resolve_production_placement(self.client,command,self.catalog,state,20,[]);assert len(batch)==1,trace;resolved.extend(batch);placements.extend(trace)
   results=await issue(self.client,resolved) if resolved else None
   for command,code in zip(resolved,list(results.result) if results else [],strict=True):
    assert code==1;self.pending[command.units[0]]=ProductionRequest(command,state,self.data)
   protected=set(self.pending)|{tag for c in resolved for tag in c.units}
   assistance=mining_commands(state,9,protected);acks=await issue(self.client,assistance) if assistance else None
   assert not state['action_errors']
   assert not acks or all(code==1 for code in acks.result)
   self.stream.write(json.dumps(dict(loop=loop,observation=state,phase=self.phase,sites=[u['tag'] for u in sites],claimed=sorted(claimed_geysers(state,self.catalog)),commands=[c.as_dict() for c in resolved],results=list(results.result) if results else [],placement=placements,pending=events,assistance=[c.as_dict() for c in assistance],assistance_results=list(acks.result) if acks else [],score=protocol_dict(packet.score)))+'\n');self.frames+=1
  except Exception as e:self.error=repr(e);raise

def episode(job):
 with Path(job['trace']).open('x',buffering=1) as stream:
  bot=Fixture(job,stream);result=run_game(validate_map('AcropolisLE'),[Bot(Race.Terran,bot),Computer(Race.Zerg,Difficulty.VeryEasy)],realtime=False,random_seed=job['seed'],game_time_limit=120,save_replay_as=job['replay'])
 assert bot.error is None and bot.phase=='mining',dict(error=bot.error,phase=bot.phase)
 return dict(status='completed',frames=bot.frames,result=result.name,home_targets=bot.home_targets,expansion_target=bot.expansion_target)
