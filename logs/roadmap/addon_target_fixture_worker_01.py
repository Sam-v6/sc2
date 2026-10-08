"""Debug-assisted addon execution fixture; never training or a strength result."""
import json
from pathlib import Path
from sc2.bot_ai import BotAI
from sc2.data import Race,Difficulty
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.main import run_game
from sc2.player import Bot,Computer
from src.runner import validate_map
from src.learning.gameplay import Command,PlayerView
from src.learning.live import issue

class Fixture(BotAI):
 def __init__(self,job,stream):
  super().__init__();self.job=job;self.stream=stream;self.frames=0;self.error=None;self.view=PlayerView();self.issued=False
 async def on_start(self):
  self.client.game_step=8;await self.client.debug_all_resources()
  self.origin=await self.find_placement(U.BARRACKS,near=self.start_location.offset((10,8)),addon_place=True)
  self.destination=await self.find_placement(U.BARRACKS,near=self.start_location.offset((22,8)),addon_place=True)
  assert self.origin is not None and self.destination is not None and self.origin.distance_to(self.destination)>5
  kind=U.BARRACKSFLYING if self.job['case']=='flying_remote' else U.BARRACKS
  await self.client.debug_create_unit([[kind,1,self.origin,1]])
 async def on_step(self,iteration):
  try:
   commands=[]
   if not self.issued and self.structures.of_type([U.BARRACKS,U.BARRACKSFLYING]):
    producer=self.structures.of_type([U.BARRACKS,U.BARRACKSFLYING]).first;self.tag=producer.tag
    point=None if self.job['case']=='no_target' else tuple(self.origin if self.job['case']=='own_point' else self.destination)
    commands=[Command(3682,(self.tag,),target_point=point)];self.issued=True
   result=await issue(self.client,commands) if commands else None
   state=self.view.observe(self.state.response_observation)
   self.stream.write(json.dumps(dict(loop=int(self.state.game_loop),observation=state,commands=[c.as_dict() for c in commands],results=list(result.result) if result else [],origin=list(self.origin),destination=list(self.destination),delayed_errors=[dict(ability=int(e.ability_id),unit=int(e.unit_tag),result=int(e.result)) for e in self.state.response_observation.action_errors]))+'\n');self.frames+=1
  except Exception as e:self.error=repr(e);raise

def episode(job):
 with Path(job['trace']).open('x',buffering=1) as stream:
  bot=Fixture(job,stream);result=run_game(validate_map('Simple64'),[Bot(Race.Terran,bot),Computer(Race.Terran,Difficulty.VeryEasy)],realtime=False,random_seed=job['seed'],game_time_limit=30,save_replay_as=job['replay'])
 assert bot.error is None and bot.issued and Path(job['replay']).stat().st_size>0
 return dict(status='completed',engineering_result=result.name,frames=bot.frames,replay_bytes=Path(job['replay']).stat().st_size)
