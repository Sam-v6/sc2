"""Native availability census for a declared multiplayer Terran unit/state roster."""
import gzip
import hashlib
import json
from pathlib import Path
import time

from loguru import logger
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.position import Point2
from sc2.ids.unit_typeid import UnitTypeId
from sc2.player import Bot, Computer
from s2clientprotocol import sc2api_pb2 as pb

from src.learning.gameplay import Command, PlayerView, protocol_dict
from src.learning.live import ability_catalog, ability_query, issue
from src.runner import validate_map
from src.runtime import supervise

NAMES = '''SCV MULE Marine Reaper Marauder Ghost Hellion HellionTank WidowMine WidowMineBurrowed SiegeTank SiegeTankSieged Cyclone Thor ThorAP VikingAssault VikingFighter Medivac Banshee Raven Liberator LiberatorAG Battlecruiser AutoTurret CommandCenter CommandCenterFlying PlanetaryFortress OrbitalCommand OrbitalCommandFlying SupplyDepot SupplyDepotLowered Refinery RefineryRich Barracks BarracksFlying Factory FactoryFlying Starport StarportFlying BarracksTechLab BarracksReactor FactoryTechLab FactoryReactor StarportTechLab StarportReactor EngineeringBay Armory GhostAcademy FusionCore Bunker MissileTurret SensorTower'''.split()

class Probe(BotAI):
    async def on_start(self):
        self.client.game_step = 4
        self.view = PlayerView()
        self.records = []
        self.setup_commands = []
        self.setup_results = []
        data = (await self.client._execute(data=pb.RequestData(ability_id=True, unit_type_id=True))).data
        self.catalog = ability_catalog(data)
        by_name = {u.name:u for u in data.units}
        self.roster = {name:by_name[name].unit_id for name in NAMES}
        assert all(by_name[name].race == 1 for name in NAMES)
        self.inventory_game_data = protocol_dict(data)
        self.ping = protocol_dict((await self.client._execute(ping=pb.RequestPing())).ping)
        await self.client.debug_all_resources()
        # Engineering supersets; debug requirements differ from ordinary ladder.
        await self.client.debug_tech_tree()
        await self.client.debug_create_unit([[UnitTypeId(self.roster[name]),1,self.game_info.map_center.offset(((i%8-3.5)*7,(i//8-3)*7)),1] for i,name in enumerate(NAMES)])
        await self.client.debug_fast_build()
        self.addon_parents = []
        center = self.start_location.towards(self.game_info.map_center, 20)
        for i, (name, ability) in enumerate([('Barracks',421),('Barracks',422),('Factory',454),('Factory',455),('Starport',487),('Starport',488)]):
            for attempt in range(8):
                near = center.offset(((i%3-1)*14, (i//3*2-1)*10 + attempt*7))
                point = await self.find_placement(UnitTypeId(self.roster[name]), near=near, addon_place=True)
                if point and all(point.distance_to(other[2]) >= 7 for other in self.addon_parents):
                    break
            else:
                raise RuntimeError('No distinct addon-capable fixture placement')
            self.addon_parents.append((name,ability,point))
            await self.client.debug_create_unit([[UnitTypeId(self.roster[name]),1,point,1]])
        for name in ('EngineeringBay','MissileTurret'):
            point = await self.find_placement(UnitTypeId(self.roster[name]),near=self.start_location.towards(self.game_info.map_center,10))
            assert point is not None
            await self.client.debug_create_unit([[UnitTypeId(self.roster[name]),1,point,1]])


    async def on_step(self, iteration):
        if iteration not in (1,20):
            return
        state = self.view.observe(self.state.response_observation)
        tags = [u['tag'] for u in state['units'] if u['alliance']==1]
        queries = {}
        for ignore in (False,True):
            request = ability_query(tags)
            request.ignore_resource_requirements = ignore
            queries[str(ignore)] = protocol_dict((await self.client._execute(query=request)).query)
        self.records.append({'phase':'before_upgrades' if iteration==1 else 'after_upgrades', 'observation':state, 'queries':queries})
        if iteration==1:
            own = [u for u in state['units'] if u['alliance']==1]
            commands = []
            for name, ability, point in self.addon_parents:
                candidates = [u for u in own if u['unit_type']==self.roster[name]]
                unit = min(candidates,key=lambda u:point.distance_to(Point2(tuple(u['position'][:2]))))
                assert point.distance_to(Point2(tuple(unit['position'][:2]))) < 1
                commands.append(Command(ability,(unit['tag'],)))
            depot = next(u for u in own if u['unit_type']==19)
            commands.append(Command(556,(depot['tag'],)))
            self.setup_commands = [c.as_dict() for c in commands]
            self.setup_results = list((await issue(self.client,commands)).result)
            await self.client.debug_upgrade()

def job(output):
    logger.remove()
    logger.add(__import__('sys').stderr,level='WARNING')
    out = Path(output)
    out.mkdir(exist_ok=False)
    bot = Probe()
    start = time.monotonic()
    result = run_game(validate_map('AcropolisLE'),[Bot(Race.Terran,bot),Computer(Race.Zerg,Difficulty.VeryEasy)],realtime=False,random_seed=115010,game_time_limit=6,save_replay_as=str(out/'game.SC2Replay'))
    assert len(bot.records)==2
    (out/'catalog.json').write_text(json.dumps(bot.catalog)+'\n')
    (out/'game-data.json').write_text(json.dumps(bot.inventory_game_data)+'\n')
    with gzip.open(out/'trace.jsonl.gz','xt') as stream:
        for row in bot.records:stream.write(json.dumps(row)+'\n')
    observed = {u['unit_type'] for r in bot.records for u in r['observation']['units'] if u['alliance']==1}
    inventories = {}
    for r in bot.records:
        for ignore, query in r['queries'].items():
            for entry in query.get('abilities',[]):
                inventories.setdefault((r['phase'],ignore,entry['unit_type_id']),set()).update(a['ability_id'] for a in entry.get('abilities',[]))
    catalog = {a['ability_id']:a for a in bot.catalog}
    ability_ids = sorted(set().union(*inventories.values()))
    roundtrips = []
    unsupported = []
    for ability in ability_ids:
        a = catalog[ability]
        modes = {1:['none'],2:['point'],3:['unit'],4:['point','unit'],5:['none','point']}.get(a.get('target'))
        if not modes:
            unsupported.append({'ability':ability,'reason':'missing/unknown target metadata','catalogue':a})
            continue
        for mode in modes:
            for queued in (False,True):
                command = Command(ability,(2**54+1,2**54+2),target_unit=2**54+3 if mode=='unit' else None,target_point=(12.5,13.5) if mode=='point' else None,queue=queued)
                assert Command.from_proto(command.to_proto())==command
                roundtrips.append({'ability':ability,'mode':mode,'queue':queued})
        if a.get('allow_autocast'):
            command = Command(ability,(2**54+1,),autocast=True)
            assert Command.from_proto(command.to_proto())==command
            roundtrips.append({'ability':ability,'mode':'autocast','queue':False})
    report = {'status':'completed','engineering_only':True,'game_result':result.name,'ping':bot.ping,'roster':bot.roster,'roster_size':len(bot.roster),'setup_commands':bot.setup_commands,'setup_results':bot.setup_results,'observed_roster':sorted(name for name,type_id in bot.roster.items() if type_id in observed),'unobserved_roster':sorted(name for name,type_id in bot.roster.items() if type_id not in observed),'native_available_abilities':ability_ids,'available_by_phase_resource_and_type':[{'phase':phase,'ignore_resources':ignore=='True','unit_type':unit,'abilities':sorted(values)} for (phase,ignore,unit),values in inventories.items()],'schema_roundtrips':roundtrips,'unsupported_metadata':unsupported,'wall_seconds':time.monotonic()-start,'scope':'Curated52 Terran multiplayer unit/state names; static available=true includes campaign/weapon placeholders and is not a multiplayer filter. Native availability in debug-tech/resource/fast-build and upgraded scenes, real addon/depot setup commands, not execution/target-validation/completeness for every possible ladder state. Serializer roundtrips use synthetic tags/targets and do not issue commands. No training/RL.'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return {k:report[k] for k in ('status','roster_size','unobserved_roster','wall_seconds')}

if __name__=='__main__':
    root = Path('logs/roadmap')
    output = root/'terran-native-inventory-05'
    files = [Path(__file__),*sorted(Path('src/learning').glob('*.py')),Path('src/runtime.py'),Path(validate_map('AcropolisLE').path).resolve()]
    before = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (root/'terran-native-inventory-05.contract.json').write_text(json.dumps({'files_before':before,'wall_bound':60,'seed':115010,'map':'AcropolisLE','game_seconds':6,'no_training_no_rl':True,'roster':NAMES},indent=2)+'\n')
    result = supervise(job,(str(output),),60)
    assert before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (root/'terran-native-inventory-05.supervision.json').write_text(json.dumps(dict(result,files_after=before),indent=2)+'\n')
    print(json.dumps(result),flush=True)
    if result['status']!='completed':raise SystemExit(1)
