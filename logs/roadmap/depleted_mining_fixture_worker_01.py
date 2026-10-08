"""Native engineering check: exhausted home minerals, visible remote mining."""
import json,math
from pathlib import Path
from sc2.bot_ai import BotAI
from sc2.data import Race,Difficulty
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.main import run_game
from sc2.player import Bot,Computer
from sc2.position import Point2
from src.runner import validate_map
from src.learning.gameplay import PlayerView,protocol_dict
from src.learning.live import issue
from src.bots.terran_primitives import mining_commands
class Fixture(BotAI):
 def __init__(self,job,stream):
  super().__init__();self.job=job;self.stream=stream;self.view=PlayerView();self.error=None;self.frames=0;self.remote_orders=0;self.max_minerals=0
 async def on_start(self):
  self.client.game_step=8;home=tuple(self.start_location)
  expansion=min((p for p in self.expansion_locations_list if p.distance_to(self.start_location)>10),key=lambda p:p.distance_to(self.start_location))
  await self.client.debug_kill_unit([u.tag for u in self.mineral_field if u.distance_to(self.start_location)<10])
  await self.client.debug_create_unit([[U.SCV,1,Point2(expansion),1]])
  Path(self.job['static']).write_text(json.dumps(dict(home=home,remote=tuple(expansion),debug_setup='Kill home mineral patches and add one SCV to reveal remote resources. No resource boost or remote townhall.'))+'\n')
 async def on_step(self,iteration):
  try:
   packet=self.state.response_observation;state=self.view.observe(packet)
   commands=mining_commands(state,0);result=await issue(self.client,commands) if commands else None
   assert not result or all(x==1 for x in result.result)
   assert not state['action_errors']
   remote={u['tag'] for u in state['units'] if u['alliance']==3 and u.get('mineral_contents',0)>0 and math.dist(u['position'][:2],tuple(self.start_location))>10}
   self.remote_orders+=sum(any(o.get('target_unit_tag') in remote for o in u.get('orders',[])) for u in state['units'] if u['alliance']==1 and u['unit_type']==45)
   self.max_minerals=max(self.max_minerals,state['player']['minerals']);self.frames+=1
   self.stream.write(json.dumps(dict(observation=state,commands=[c.as_dict() for c in commands],results=list(result.result) if result else [],score=protocol_dict(packet.observation.score)))+'\n')
  except Exception as e:self.error=repr(e);raise

def episode(job):
 with Path(job['trace']).open('x',buffering=1) as stream:
  bot=Fixture(job,stream);result=run_game(validate_map('AcropolisLE'),[Bot(Race.Terran,bot),Computer(Race.Zerg,Difficulty.VeryEasy)],realtime=False,random_seed=job['seed'],game_time_limit=150,save_replay_as=job['replay'])
 assert bot.error is None and bot.remote_orders>0 and bot.max_minerals>50,dict(error=bot.error,remote_orders=bot.remote_orders,max_minerals=bot.max_minerals)
 return dict(status='completed',frames=bot.frames,result=result.name,remote_orders=bot.remote_orders,max_minerals=bot.max_minerals)
