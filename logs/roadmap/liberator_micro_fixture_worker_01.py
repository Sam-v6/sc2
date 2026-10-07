"""Real native mode/kill/undeploy fixture; debug units, no model or RL."""
import json
from pathlib import Path
from sc2.bot_ai import BotAI
from sc2.data import Race,Difficulty
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.main import run_game
from sc2.player import Bot,Computer
from s2clientprotocol import sc2api_pb2 as pb
from src.runner import validate_map
from src.learning.gameplay import PlayerView,protocol_dict
from src.learning.live import issue
from src.bots.terran_primitives import combat_command
class Fixture(BotAI):
 def __init__(self,job,stream):
  super().__init__();self.job=job;self.stream=stream;self.view=PlayerView();self.error=None;self.frames=0;self.modes=set();self.tanks=set();self.dead=set();self.commands=[]
 async def on_start(self):
  self.client.game_step=8;data=protocol_dict((await self.client._execute(data=pb.RequestData(unit_type_id=True))).data);self.types={u['unit_id']:u for u in data['units']}
  self.point=self.start_location.towards(self.game_info.map_center,28)
  await self.client.debug_create_unit([[U.LIBERATOR,1,self.point,1],[U.SIEGETANKSIEGED,3,self.point.towards(self.game_info.map_center,8),2]])
  Path(self.job['static']).write_text(json.dumps(dict(game_data=data,point=tuple(self.point),debug_setup='One owned Liberator and three enemy sieged tanks; no resources, upgrades or model.'))+'\n')
 async def on_step(self,iteration):
  try:
   packet=self.state.response_observation;s=self.view.observe(packet);enemies=[u for u in s['units'] if u['alliance']==4];self.tanks.update(u['tag'] for u in enemies if u['unit_type']==32);self.dead.update(s.get('dead_units',[]));commands=[]
   for u in s['units']:
    if u['alliance']==1 and u['unit_type'] in (689,734):
     self.modes.add(u['unit_type']);command=combat_command(u,enemies,self.types,tuple(self.point),lambda p:True)
     if command:commands.append(command)
   result=await issue(self.client,commands) if commands else None;assert not result or all(c==1 for c in result.result);assert not s['action_errors']
   self.commands.extend(c.ability for c in commands);self.frames+=1
   self.stream.write(json.dumps(dict(observation=s,commands=[c.as_dict() for c in commands],results=list(result.result) if result else [],score=protocol_dict(packet.observation.score)))+'\n')
  except Exception as e:self.error=repr(e);raise

def episode(job):
 with Path(job['trace']).open('x',buffering=1) as stream:
  bot=Fixture(job,stream);result=run_game(validate_map('AcropolisLE'),[Bot(Race.Terran,bot),Computer(Race.Zerg,Difficulty.VeryEasy)],realtime=False,random_seed=job['seed'],game_time_limit=90,save_replay_as=job['replay'])
 assert bot.error is None and bot.modes=={689,734} and 2558 in bot.commands and 2560 in bot.commands,dict(error=bot.error,modes=list(bot.modes),commands=bot.commands)
 return dict(status='completed',frames=bot.frames,result=result.name,modes=sorted(bot.modes),commands=bot.commands,enemy_tanks=sorted(bot.tanks))
