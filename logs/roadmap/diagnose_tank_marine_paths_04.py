import asyncio,json
from pathlib import Path
from sc2.sc2process import SC2Process
from s2clientprotocol import sc2api_pb2 as pb,query_pb2 as q,common_pb2 as c
from src.learning.replay_extract import replay_metadata
from src.learning.gameplay import protocol_dict

async def main():
 p=Path('logs/roadmap/primitives-native-04/panel/Terran-Rush/game.SC2Replay')
 meta,_=replay_metadata(p)
 out=[]
 async with SC2Process(base_build=meta['BaseBuild'],data_hash=meta['DataVersion']) as server:
  r=await server._execute(start_replay=pb.RequestStartReplay(replay_data=p.read_bytes(),observed_player_id=1,options=pb.InterfaceOptions(raw=True,score=True),disable_fog=False))
  assert not r.start_replay.HasField('error'),r
  previous=0
  for seconds in (420,540,660,780):
   loop=round(seconds*22.4)
   await server._execute(step=pb.RequestStep(count=loop-previous));previous=loop
   ob=(await server._execute(observation=pb.RequestObservation())).observation.observation
   tanks=[u for u in ob.raw_data.units if u.alliance==1 and u.unit_type in(32,33,48)]
   endpoints=[(33.5,138.5),(133.86,41.83),(140.6,79.61)]
   response=(await server._execute(query=q.RequestQuery(pathing=[q.RequestQueryPathing(unit_tag=u.tag,end_pos=c.Point2D(x=x,y=y)) for u in tanks for x,y in endpoints]))).query
   rows=[dict(unit=protocol_dict(u),path_distances=[v.distance for v in response.pathing[i*3:(i+1)*3]]) for i,u in enumerate(tanks)]
   item=dict(seconds=seconds,endpoints=endpoints,tanks=rows)
   out.append(item);print(json.dumps(item),flush=True)
 Path('logs/roadmap/primitives-native-04/tank-marine-path-diagnosis.json').write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__':asyncio.run(main())
