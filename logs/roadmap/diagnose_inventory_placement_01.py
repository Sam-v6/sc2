"""Read-only native replay queries for the failed inventory placement requests."""
import asyncio,hashlib,json,math
from pathlib import Path
from sc2.sc2process import SC2Process
from s2clientprotocol import sc2api_pb2 as pb
from src.learning.replay_extract import replay_metadata
from src.learning.gameplay import Command,PlayerView
from src.learning.production_clearance import reservations,resolve_production_placement
ROOT=Path('logs/roadmap/human-inventory-native-01');replay=ROOT/'I/game.SC2Replay'
static=json.loads((ROOT/'I/static.json').read_text());catalog={a['ability_id']:a for a in static['abilities']};types={u['unit_id']:u for u in static['units']}
def seed(base,center):
 length=math.dist(base,center);return tuple(a+10*(b-a)/length for a,b in zip(base,center))
async def main():
 meta,_=replay_metadata(replay);out=[];view=PlayerView()
 async with SC2Process(base_build=meta['BaseBuild'],data_hash=meta['DataVersion']) as server:
  start=await server._execute(start_replay=pb.RequestStartReplay(replay_data=replay.read_bytes(),observed_player_id=1,options=pb.InterfaceOptions(raw=True,score=True),disable_fog=False))
  assert not start.start_replay.HasField('error'),start
  info=(await server._execute(game_info=pb.RequestGameInfo())).game_info
  state=view.observe((await server._execute(observation=pb.RequestObservation())).observation)
  home=next(u['position'][:2] for u in state['units'] if u['alliance']==1 and u['unit_type']==18)
  center=(info.start_raw.map_size.x/2,info.start_raw.map_size.y/2);previous=0
  for loop in [11200,12992,13432]:
   await server._execute(step=pb.RequestStep(count=loop-previous));previous=loop
   state=view.observe((await server._execute(observation=pb.RequestObservation())).observation);state['map_size']=[info.start_raw.map_size.x,info.start_raw.map_size.y]
   own=[u for u in state['units'] if u['alliance']==1];bases=[u for u in own if u['unit_type'] in (18,132,130) and u.get('build_progress',1)==1 and not u.get('is_flying')]
   workers=[u for u in own if u['unit_type']==45 and (not u.get('orders') or all(o['ability_id'] in (295,3666) for o in u['orders']))]
   tests=[]
   for product in [19,21]:
    ability=types[product]['ability_id']
    for origin,label in [(seed(home,center),'original')]+[(seed(u['position'][:2],center),'base:'+str(u['tag'])) for u in bases]:
     worker=min(workers,key=lambda u:math.dist(u['position'][:2],origin))
     commands,trace=await resolve_production_placement(server,Command(ability,(worker['tag'],),target_point=origin),catalog,state,product,reservations(state,types,catalog))
     tests.append(dict(product=types[product]['name'],origin_label=label,origin=origin,worker=worker['tag'],commands=[c.as_dict() for c in commands],placement=trace))
   out.append(dict(loop=state['game_loop'],player=state['player'],queries=tests));print(json.dumps(out[-1]),flush=True)
 def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
 (ROOT/'placement-diagnosis.json').write_text(json.dumps(dict(status='native_replay_placement_diagnostic',read_only=True,observations=out,bindings={str(p):sha(p) for p in [Path(__file__),replay,ROOT/'I/static.json',Path('src/learning/production_clearance.py')]}),indent=2)+'\n')
if __name__=='__main__':asyncio.run(main())
