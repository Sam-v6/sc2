"""Live engine check of catalogue research resolution; no training or strength claim."""
import json
from pathlib import Path
from sc2.bot_ai import BotAI
from sc2.data import Race,Difficulty
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.main import run_game
from sc2.player import Bot,Computer
from s2clientprotocol import sc2api_pb2 as pb
from src.runner import validate_map
from src.learning.gameplay import Command,PlayerView,protocol_dict
from src.learning.live import issue,ability_query
from src.learning.production_execution import goal_catalog,eligible_actors
class Fixture(BotAI):
 def __init__(self,job,stream):
  super().__init__();self.job=job;self.stream=stream;self.view=PlayerView();self.issued=False;self.frames=0;self.error=None
 async def on_start(self):
  self.client.game_step=8;await self.client.debug_all_resources()
  p=await self.find_placement(U.ARMORY,near=self.start_location.offset((10,8)))
  f=await self.find_placement(U.FACTORY,near=self.start_location.offset((-10,8)))
  assert p is not None and f is not None
  await self.client.debug_create_unit([[U.ARMORY,1,p,1],[U.FACTORY,1,f,1]])
  self.data=protocol_dict((await self.client._execute(data=pb.RequestData(ability_id=True,unit_type_id=True,upgrade_id=True))).data)
  Path(self.job['catalog']).write_text(json.dumps(self.data)+'\n')
  self.goal=goal_catalog(self.data,['upgrade:TerranVehicleAndShipArmorsLevel1'])['upgrade:TerranVehicleAndShipArmorsLevel1']
  self.catalog={a['ability_id']:a for a in self.data['abilities']};self.names={u['unit_id']:u['name'] for u in self.data['units']}
 async def on_step(self,iteration):
  try:
   state=self.view.observe(self.state.response_observation);tags=[u['tag'] for u in state['units'] if u['alliance']==1 and u['unit_type']==29]
   available=(await self.client._execute(query=ability_query(tags))).query if tags else None
   abilities={e.unit_tag:[a.ability_id for a in e.abilities] for e in available.abilities} if available else {}
   actors=eligible_actors(state,self.goal['ability'],abilities,self.catalog,self.names);commands=[]
   if actors and not self.issued:
    commands=[Command(self.goal['ability'],(actors[0]['tag'],))];self.issued=True
   response=await issue(self.client,commands) if commands else None
   self.stream.write(json.dumps(dict(loop=int(self.state.game_loop),observation=state,available=abilities,goal=self.goal,commands=[c.as_dict() for c in commands],results=list(response.result) if response else [],delayed_errors=[protocol_dict(e) for e in self.state.response_observation.action_errors]))+'\n');self.frames+=1
  except Exception as e:self.error=repr(e);raise

def episode(job):
 with Path(job['trace']).open('x',buffering=1) as stream:
  bot=Fixture(job,stream);result=run_game(validate_map('Simple64'),[Bot(Race.Terran,bot),Computer(Race.Terran,Difficulty.VeryEasy)],realtime=False,random_seed=818501,game_time_limit=8,save_replay_as=job['replay'])
 assert bot.error is None and bot.issued and Path(job['replay']).stat().st_size>0
 return dict(status='completed',engineering_result=result.name,frames=bot.frames)
