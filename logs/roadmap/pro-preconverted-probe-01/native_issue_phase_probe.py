import asyncio
import hashlib
import json
from pathlib import Path

from s2clientprotocol import sc2api_pb2 as pb
from src.learning.gameplay import Command
from src.learning.replay_extract import replay_metadata
from src.runtime import supervise

ROOT = Path(__file__).parent
REPLAY = Path('logs/roadmap/human-replays/51574.SC2Replay').absolute()

async def probe():
    from loguru import logger
    from sc2.sc2process import SC2Process
    logger.remove()
    metadata, _ = replay_metadata(REPLAY)
    rows = []
    async with SC2Process(base_build=metadata['BaseBuild'], data_hash=metadata['DataVersion']) as server:
        options = pb.InterfaceOptions(raw=True, score=True,
            raw_affects_selection=False, raw_crop_to_playable_area=False)
        response = await server._execute(start_replay=pb.RequestStartReplay(
            replay_data=REPLAY.read_bytes(),observed_player_id=2,options=options,
            disable_fog=False,realtime=False))
        if response.start_replay.HasField('error'):
            raise RuntimeError(response.start_replay.error_details)
        for _ in range(301):
            packet = (await server._execute(observation=pb.RequestObservation())).observation
            loop = packet.observation.game_loop
            player = packet.observation.player_common
            commands = []
            for action in packet.actions:
                if action.HasField('action_raw') and action.action_raw.HasField('unit_command'):
                    commands.append(dict(action_loop=action.game_loop,command=Command.from_proto(action).as_dict()))
            buildings = [dict(tag=u.tag,unit_type=u.unit_type,
                orders=[dict(ability=o.ability_id,progress=o.progress) for o in u.orders])
                for u in packet.observation.raw_data.units if u.alliance==1 and u.unit_type in (18,132)]
            rows.append(dict(loop=loop,minerals=player.minerals,food_used=player.food_used,
                             buildings=buildings,actions=commands))
            if loop >= 300:
                break
            await server._execute(step=pb.RequestStep(count=1))
    output = ROOT/'native-issue-phase-01.json'
    result = dict(replay=str(REPLAY),replay_sha256=hashlib.sha256(REPLAY.read_bytes()).hexdigest(),
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        metadata=metadata,rows=rows,optimizer_updates=0,scope='Existing teaching replay timing probe; no reserved game or training')
    output.write_text(json.dumps(result,indent=2)+'\n')
    for i,row in enumerate(rows):
        if row['actions']:
            print(json.dumps(rows[max(0,i-2):i+2]),flush=True)
    return dict(status='completed',observations=len(rows),receipt=str(output))

def worker():
    return asyncio.run(probe())

if __name__=='__main__':
    result=supervise(worker,(),120)
    print(json.dumps(result),flush=True)
    if result.get('status')!='completed':raise SystemExit(1)
