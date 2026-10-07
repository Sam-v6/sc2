import json
from pathlib import Path
from sc2.bot_ai import BotAI
from sc2.data import Race, Difficulty
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.main import run_game
from sc2.player import Bot, Computer
from src.runner import validate_map
from src.learning.gameplay import Command, PlayerView
from src.learning.live import issue
from src.learning.producer_bindings import ProducerBindings

class Fixture(BotAI):
 def __init__(self,job,stream):
  super().__init__();self.job=job;self.stream=stream;self.view=PlayerView();self.bindings=ProducerBindings();self.phase='bind';self.error=None;self.frames=0;self.addon=None
 async def on_start(self):
  self.client.game_step=8
  await self.client.debug_all_resources();await self.client.debug_fast_build()
  self.origin=await self.find_placement(U.BARRACKS,near=self.start_location.offset((10,8)),addon_place=True)
  assert self.origin is not None
  await self.client.debug_create_unit([[U.BARRACKS,1,self.origin,1],[U.FACTORYFLYING,1,self.origin.offset((0,7)),1]])
 async def on_step(self,iteration):
  try:
   state=self.view.observe(self.state.response_observation);commands=[]
   if self.phase=='bind':
    barracks=next((u for u in state['units'] if u['alliance']==1 and u['unit_type']==21),None)
    factory=next((u for u in state['units'] if u['alliance']==1 and u['unit_type']==43),None)
    if barracks and factory:
     self.bindings.bind(4355784706,barracks['tag']);self.bindings.bind(4360503299,factory['tag'])
     commands=[Command(3683,(barracks['tag'],))];self.phase='addon'
   else:
    barracks=self.bindings.resolve(4355784706,state);factory=self.bindings.resolve(4360503299,state)
    assert barracks and factory,'Bound producer disappeared'
    if self.phase=='addon' and barracks.get('add_on_tag'):
     tag=barracks['add_on_tag'];addon=next((u for u in state['units'] if u['tag']==tag),None)
     if addon and addon.get('build_progress',0)>=1:
      self.addon=tag;self.bindings.bind(4362600450,tag)
      commands=[Command(452,(barracks['tag'],))];self.phase='lift'
    elif self.phase=='lift' and barracks.get('is_flying'):
     commands=[Command(520,(factory['tag'],),target_point=tuple(self.origin))];self.phase='land'
    elif self.phase=='land' and not factory.get('is_flying',False) and factory.get('add_on_tag')==self.addon:
     assert self.bindings.resolve(4362600450,state)['tag']==self.addon
     self.phase='verified'
   result=await issue(self.client,commands) if commands else None
   self.stream.write(json.dumps(dict(loop=state['game_loop'],phase=self.phase,bindings=self.bindings.tags,observation=state,commands=[c.as_dict() for c in commands],results=list(result.result) if result else []))+'\n');self.frames+=1
  except Exception as e:self.error=repr(e);raise

def episode(job):
 with Path(job['trace']).open('x',buffering=1) as stream:
  bot=Fixture(job,stream)
  result=run_game(validate_map('Simple64'),[Bot(Race.Terran,bot),Computer(Race.Zerg,Difficulty.VeryEasy)],realtime=False,random_seed=job['seed'],game_time_limit=20,save_replay_as=job['replay'])
 assert bot.error is None and bot.phase=='verified',dict(error=bot.error,phase=bot.phase)
 return dict(status='completed',engineering_result=result.name,frames=bot.frames,addon=bot.addon,phase=bot.phase)
