"""Native blocked-pad clearance followed by normal Reactor construction."""
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
from src.learning.production_clearance import resolve_production_placement
from src.learning.production_primitives import primitive_assistance
from src.learning.production_request import ProductionRequest
class Fixture(BotAI):
 def __init__(self,job,stream):
  super().__init__();self.job=job;self.stream=stream;self.view=PlayerView();self.error=None;self.pending=None;self.started=False;self.completed=False;self.withheld=0;self.moves=0;self.hold=set();self.points=[];self.issued=False
 async def on_start(self):
  self.client.game_step=8;self.data=protocol_dict((await self.client._execute(data=pb.RequestData(ability_id=True,unit_type_id=True))).data);self.catalog={a['ability_id']:a for a in self.data['abilities']};self.types={u['unit_id']:u for u in self.data['units']}
  self.origin=await self.find_placement(U.BARRACKS,near=self.start_location.offset((12,8)),addon_place=True);assert self.origin
  self.pad=tuple(self.origin.offset((2.5,-.5)))
  await self.client.debug_all_resources();await self.client.debug_create_unit([[U.BARRACKS,1,self.origin,1],[U.MARINE,1,self.origin.offset((2.5,-.5)),1]])
  Path(self.job['static']).write_text(json.dumps(dict(game_data=self.data,origin=tuple(self.origin),pad=self.pad,debug_setup='Completed Barracks, one Marine on addon pad, debug resources. Reactor uses normal native command.'))+'\n')
 async def on_step(self,iteration):
  try:
   s=self.view.observe(self.state.response_observation);s['map_size']=[self.game_info.map_size.x,self.game_info.map_size.y];own=[u for u in s['units'] if u['alliance']==1];commands=[];trace=[]
   parents=[u for u in own if u['unit_type']==21 and math.dist(u['position'][:2],tuple(self.origin))<1];marines=[u for u in own if u['unit_type']==48]
   if self.pending:
    status=self.pending.status(s);assert status not in ('failed','actor_missing')
    if status=='started':self.started=True;self.points=[]
   if parents and marines and s['player']['minerals']>=100 and s['player']['vespene']>=100 and not self.issued:
    commands,trace=await resolve_production_placement(self.client,Command(3683,(parents[0]['tag'],)),self.catalog,s,38,[])
    if not commands:self.withheld+=1;self.points=[tuple(p) for t in trace for p in t.get('clearance_points',[])]
    else:self.issued=True;self.points=[self.pad]
   result=await issue(self.client,commands) if commands else None;assert not result or all(code==1 for code in result.result)
   if commands:self.pending=ProductionRequest(commands[0],s,self.data)
   protected={u['tag'] for u in own if u['unit_type']!=48}
   assistance=primitive_assistance(s,protected,self.types,self.catalog,self.pad,lambda p:self.in_map_bounds(Point2(p)) and self.in_pathing_grid(Point2(p)),False,landing_points=self.points,landing_hold=self.hold)
   acks=await issue(self.client,assistance) if assistance else None;assert not acks or all(code==1 for code in acks.result);assert not s['action_errors'];self.moves+=sum(c.ability==16 for c in assistance)
   addons=[u for u in own if u['unit_type']==38 and math.dist(u['position'][:2],self.pad)<1 and u.get('build_progress',1)>=1]
   self.completed=self.completed or bool(addons and any(p.get('add_on_tag')==addons[0]['tag'] for p in parents))
   self.stream.write(json.dumps(dict(observation=s,commands=[c.as_dict() for c in commands],results=list(result.result) if result else [],placement=trace,clearance_points=self.points,assistance=[c.as_dict() for c in assistance],assistance_results=list(acks.result) if acks else [],started=self.started,completed=self.completed))+'\n')
  except Exception as e:self.error=repr(e);raise

def episode(job):
 with Path(job['trace']).open('x',buffering=1) as stream:
  bot=Fixture(job,stream);result=run_game(validate_map('AcropolisLE'),[Bot(Race.Terran,bot),Computer(Race.Zerg,Difficulty.VeryEasy)],realtime=False,random_seed=job['seed'],game_time_limit=90,save_replay_as=job['replay'])
 assert bot.error is None and bot.withheld>0 and bot.moves>0 and bot.started and bot.completed,dict(error=bot.error,withheld=bot.withheld,moves=bot.moves,started=bot.started,completed=bot.completed)
 return dict(status='completed',result=result.name,withheld=bot.withheld,clearance_moves=bot.moves,reactor_started=bot.started,reactor_completed_and_attached=bot.completed)
