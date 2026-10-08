import asyncio,gzip,json
from pathlib import Path
from sc2.sc2process import SC2Process
from s2clientprotocol import sc2api_pb2 as pb,query_pb2 as q,common_pb2 as c,error_pb2 as errors
from src.learning.replay_extract import replay_metadata
ROOT=Path('logs/roadmap/human-inventory-native-01');p=ROOT/'I/game.SC2Replay'
with gzip.open(ROOT/'I/trace.jsonl.gz','rt') as f:rows=list(map(json.loads,f))
command=next(e['command'] for r in rows for e in r['execution'] if e['goal']=='unit:SupplyDepot')
async def main():
 m,_=replay_metadata(p)
 async with SC2Process(base_build=m['BaseBuild'],data_hash=m['DataVersion']) as server:
  r=await server._execute(start_replay=pb.RequestStartReplay(replay_data=p.read_bytes(),observed_player_id=1,options=pb.InterfaceOptions(raw=True),disable_fog=False));assert not r.start_replay.HasField('error')
  ob=(await server._execute(observation=pb.RequestObservation())).observation.observation
  tag=next(u.tag for u in ob.raw_data.units if u.alliance==1 and u.unit_type==45)
  result=(await server._execute(query=q.RequestQuery(ignore_resource_requirements=True,placements=[q.RequestQueryBuildingPlacement(ability_id=command['ability'],placing_unit_tag=tag,target_pos=c.Point2D(x=command['target_point'][0],y=command['target_point'][1]))]))).query
  report=dict(status='replay_placement_support_probe',actual_successful_live_command=command,replay_initial_loop=ob.game_loop,replay_placement_codes=[x.result for x in result.placements],code_names=[errors.ActionResult.Name(x.result) for x in result.placements])
  (ROOT/'replay-placement-support.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':asyncio.run(main())
