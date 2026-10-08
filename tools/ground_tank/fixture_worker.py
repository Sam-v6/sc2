"""Isolated debug-unit physics check, never a training or opponent-win result."""
import json
from pathlib import Path
from sc2.bot_ai import BotAI
from sc2.data import Race,Difficulty
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.main import run_game,get_replay_version
from sc2.player import Bot,Computer
from src.rl.terran import TerranLearner
from src.runner import validate_map
from learner import ground_micro


class Fixture(BotAI):
    army_units=TerranLearner.army_units

    def __init__(self,job,file):
        super().__init__();self.job=job;self.file=file;self.error=None;self.frames=0
        self.next_gather=1e9;self.attacking=True;self.stance_changed=False

    async def on_start(self):
        self.client.game_step=8
        center=self.game_info.map_center
        await self.client.debug_create_unit([[U[self.job['tank']],1,center,1],
                                            [U[self.job['target']],1,center.offset((6,0)),2]])

    async def on_step(self,iteration):
        try:
            tanks=self.units.of_type({U.SIEGETANK,U.SIEGETANKSIEGED})
            rows=[]
            for unit in tanks:
                enemies=list(self.enemy_units)+list(self.enemy_structures)
                rows.append({'tag':unit.tag,'type':unit.type_id.name,'health':unit.health,
                    'orders':[order.ability.id.name for order in unit.orders],
                    'enemies':[{'tag':enemy.tag,'type':enemy.type_id.name,'flying':enemy.is_flying,
                                'structure':enemy.is_structure,'distance':enemy.distance_to(unit)} for enemy in enemies]})
            micro=TerranLearner.micro if self.job['role']=='control' else ground_micro
            await micro(self)
            self.file.write(json.dumps({'time':self.time,'tanks':rows,
                'queued':[{'unit':command.unit.tag,'ability':command.ability.name} for command in self.actions]})+'\n')
            self.frames+=1
        except Exception as failure:self.error=repr(failure);raise


def episode(job):
    assert job['engineering_only'] is True and job['game_limit']==8
    for key in ['trace','replay']:assert not Path(job[key]).exists()
    with Path(job['trace']).open('x',buffering=1) as file:
        bot=Fixture(job,file)
        result=run_game(validate_map('Simple64'),[Bot(Race.Terran,bot),Computer(Race.Terran,Difficulty.VeryEasy)],
            realtime=False,random_seed=job['seed'],game_time_limit=8,save_replay_as=job['replay'])
    assert bot.error is None and bot.frames>0 and Path(job['replay']).stat().st_size>0
    return {'status':'completed','engineering_result':result.name,'frames':bot.frames,
            'replay_version':list(get_replay_version(job['replay'])),'replay_bytes':Path(job['replay']).stat().st_size}


def entrypoint_probe():return {'file':__file__,'games_launched':0}
