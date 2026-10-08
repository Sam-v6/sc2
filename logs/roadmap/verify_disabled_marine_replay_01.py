import asyncio,json
from pathlib import Path
from sc2.sc2process import SC2Process
from s2clientprotocol import sc2api_pb2 as pb, query_pb2 as q
from src.learning.replay_extract import replay_metadata
from src.learning.gameplay import protocol_dict
from src.bots.terran_primitives import combat_command

async def main():
 out=Path('logs/roadmap/primitives-hard-baseline-01/panel')
 example=json.loads((out/'action-error-audit.json').read_text())['examples'][0]
 replay=Path(example['job']['replay']);meta,_=replay_metadata(replay)
 async with SC2Process(base_build=meta['BaseBuild'],data_hash=meta['DataVersion']) as server:
  response=await server._execute(start_replay=pb.RequestStartReplay(replay_data=replay.read_bytes(),observed_player_id=1,options=pb.InterfaceOptions(raw=True),disable_fog=False))
  assert not response.start_replay.HasField('error')
  await server._execute(step=pb.RequestStep(count=example['loop']))
  obs=(await server._execute(observation=pb.RequestObservation())).observation.observation
  tag=example['command']['units'][0]
  unit=next(u for u in obs.raw_data.units if u.tag==tag)
  assert 5 in unit.buff_ids and unit.health>0
  control=next(u for u in obs.raw_data.units if u.alliance==1 and u.unit_type==48 and u.health>0 and 5 not in u.buff_ids)
  response=(await server._execute(query=q.RequestQuery(abilities=[q.RequestQueryAvailableAbilities(unit_tag=t) for t in (tag,control.tag)],ignore_resource_requirements=True))).query
  assert len(response.abilities)==2
  abilities=[a.ability_id for a in response.abilities[0].abilities]
  control_abilities=[a.ability_id for a in response.abilities[1].abilities]
  data=(await server._execute(data=pb.RequestData(ability_id=True))).data
  catalogue={a.ability_id:a.friendly_name for a in data.abilities}
  assert any(catalogue[a].startswith(('Move','Attack')) for a in control_abilities)
  assert not any(catalogue[a].startswith(('Move','Attack')) for a in abilities)
  actor=protocol_dict(unit);actor['position']=[unit.pos.x,unit.pos.y,unit.pos.z]
  assert combat_command(actor,[],{},(20,20),lambda p:True) is None
  result=dict(status='verified_disabled_actor_guard',loop=obs.game_loop,actor=actor,available_abilities=abilities,control_tag=control.tag,control_abilities=control_abilities,replay=str(replay),rl=False,training=False,
  limits=['Replay state/ability query proves the recorded disabled actor cannot move/attack; it is not a new strength panel.'])
  (out/'disabled-marine-guard.json').write_text(json.dumps(result,indent=2)+'\n')
  print(json.dumps({'status':result['status'],'loop':result['loop'],'available_abilities':abilities,'control_abilities':control_abilities}))
if __name__=='__main__':asyncio.run(main())
