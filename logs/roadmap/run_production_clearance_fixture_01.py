"""Bounded debug mechanics fixture; no training or competence claim."""
import json,sys
from pathlib import Path
from sc2.bot_ai import BotAI
from sc2.data import Race,Difficulty
from sc2.player import Bot,Computer
from sc2.main import run_game
from sc2.ids.unit_typeid import UnitTypeId as U
from src.learning.gameplay import PlayerView,Command,protocol_dict
from src.learning.production_clearance import resolve_production_placement
from src.learning.live import issue
from src.runner import validate_map
from src.runtime import supervise
from s2clientprotocol import sc2api_pb2 as pb
OUT=Path('logs/roadmap/production-clearance-fixture-01')
class Fixture(BotAI):
    def __init__(self):
        super().__init__();self.view=PlayerView();self.checks={};self.error=None
    async def on_start(self):
        self.client.game_step=8
        await self.client.debug_all_resources()
        p=await self.find_placement(U.FACTORY,near=self.start_location.offset((10,10)),addon_place=True,random_alternative=False)
        q=await self.find_placement(U.FACTORY,near=self.start_location.offset((-12,10)),addon_place=True,random_alternative=False)
        await self.client.debug_create_unit([[U.FACTORY,1,p,1],[U.FACTORY,1,q,1],[U.SUPPLYDEPOT,1,q.offset((2.5,-.5)),1]])
        self.clear=p;self.blocked=q
        data=(await self.client._execute(data=pb.RequestData(ability_id=True,unit_type_id=True))).data
        self.catalog={a['ability_id']:a for a in protocol_dict(data)['abilities']}
    async def on_step(self,iteration):
        try:
            state=self.view.observe(self.state.response_observation);state['map_size']=[self.game_info.map_size.x,self.game_info.map_size.y]
            if iteration==1:
                clear=min(self.structures(U.FACTORY),key=lambda u:u.distance_to(self.clear));blocked=min(self.structures(U.FACTORY),key=lambda u:u.distance_to(self.blocked))
                yes,yt=await resolve_production_placement(self.client,Command(454,(clear.tag,)),self.catalog,state,39,[])
                no,nt=await resolve_production_placement(self.client,Command(454,(blocked.tag,)),self.catalog,state,39,[])
                self.checks.update(clear_command=len(yes)==1,blocked_command=len(no)==0,placement_queries=dict(clear=yt,blocked=nt))
                response=await issue(self.client,yes);self.checks['acknowledged']=list(response.result)==[1]
            if iteration==12:
                self.checks['actual_techlab_foundation']=bool(self.structures(U.FACTORYTECHLAB))
        except Exception as e:self.error=repr(e);raise

def play():
    from loguru import logger
    logger.remove();OUT.mkdir(exist_ok=False)
    bot=Fixture();r=run_game(validate_map('AcropolisLE'),[Bot(Race.Terran,bot),Computer(Race.Zerg,Difficulty.VeryEasy)],realtime=False,game_time_limit=20,random_seed=816020,save_replay_as=str(OUT/'game.SC2Replay'))
    assert not bot.error,bot.error
    assert all(bot.checks[k] for k in ('clear_command','blocked_command','acknowledged','actual_techlab_foundation')),bot.checks
    report=dict(status='verified_mechanics',checks=bot.checks,result=r.name,training=False,rl=False,competence=False)
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
    r=supervise(play,(),60);print(json.dumps(r),flush=True)
    if r['status']!='verified_mechanics':sys.exit(1)
