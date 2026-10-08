"""Debug fixture: queue admission with full supply, then free three supply."""
import json
from pathlib import Path
from sc2.bot_ai import BotAI
from sc2.data import Race,Difficulty
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.main import run_game
from sc2.player import Bot,Computer
from src.runner import validate_map
from src.learning.gameplay import Command,PlayerView
from src.learning.live import issue,ability_query
class Fixture(BotAI):
 def __init__(self,job,stream):
  super().__init__();self.job=job;self.stream=stream;self.view=PlayerView();self.attempted=False;self.freed=False;self.retried=False;self.frames=0;self.error=None
 async def on_start(self):
  self.client.game_step=8
  await self.client.debug_all_resources()
  point=await self.find_placement(U.STARPORT,near=self.start_location.offset((10,8)))
  assert point is not None
  await self.client.debug_create_unit([[U.STARPORT,1,point,1],[U.MARINE,3,self.start_location.offset((5,5)),1]])
 async def on_step(self,iteration):
  try:
   state=self.view.observe(self.state.response_observation);commands=[];available=None;loop=state['game_loop'];actor=next((u for u in state['units'] if u['alliance']==1 and u['unit_type']==28),None)
   if actor and not self.attempted and state['player']['food_used']>=state['player']['food_cap']:
    q=(await self.client._execute(query=ability_query([actor['tag']],ignore_resources=True))).query
    available=[a.ability_id for row in q.abilities for a in row.abilities]
    commands=[Command(626,(actor['tag'],))];self.attempted=True
   if self.attempted and loop>=224 and not self.freed:
    marines=[u['tag'] for u in state['units'] if u['alliance']==1 and u['unit_type']==48]
    assert len(marines)==3
    await self.client.debug_kill_unit(marines);self.freed=True
   if self.freed and loop>=248 and not self.retried and actor and not actor.get('orders'):
    commands=[Command(626,(actor['tag'],))];self.retried=True
   results=await issue(self.client,commands) if commands else None
   self.stream.write(json.dumps(dict(loop=loop,observation=state,available=available,commands=[c.as_dict() for c in commands],results=list(results.result) if results else [],freed=self.freed))+'\n');self.frames+=1
  except Exception as e:self.error=repr(e);raise

def episode(job):
 with Path(job['trace']).open('x',buffering=1) as stream:
  bot=Fixture(job,stream);result=run_game(validate_map('Simple64'),[Bot(Race.Terran,bot),Computer(Race.Zerg,Difficulty.VeryEasy)],realtime=False,random_seed=job['seed'],game_time_limit=60,save_replay_as=job['replay'])
 assert bot.error is None and bot.frames>0 and bot.attempted and bot.freed,dict(error=bot.error,frames=bot.frames)
 return dict(status='completed',frames=bot.frames,result=result.name,retried=bot.retried)
