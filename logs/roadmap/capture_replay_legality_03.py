"""Capture native pre-command availability for Rom; no fit or model evaluation."""
import asyncio
import gzip
import hashlib
import json
from pathlib import Path
import time
from s2clientprotocol import sc2api_pb2 as pb
from src.learning.gameplay import PlayerView, protocol_dict
from src.learning.live import ability_query
from src.learning.replay_extract import replay_metadata, validate_replay_info
from src.runtime import supervise

ROOT=Path('logs/roadmap')
DATASET=ROOT/'issued-51482-rom-masked-01'
OUTPUT=ROOT/'replay-legality-rom-03'

async def capture(job):
    from sc2.sc2process import SC2Process
    from loguru import logger
    logger.remove()
    logger.add(__import__('sys').stderr,level='WARNING')
    dataset=Path(job['dataset']);output=Path(job['output'])
    receipt=json.loads((dataset/'dataset.json').read_text());replay=Path(receipt['replay'])
    metadata,_=replay_metadata(replay)
    files=[Path(__file__),replay]+[dataset/n for n in ('dataset.json','static.json','examples.jsonl.gz')]
    files += [Path('src/learning')/(n+'.py') for n in ('gameplay','live','replay_extract')]
    def hashes():return {str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    before=hashes();start=time.monotonic()
    output.mkdir(exist_ok=False)
    contract={'scope':'native legal-command capture at saved pre-action states, no predictions',
              'disable_fog':False,'ignore_resource_requirements':False,'files_before':before}
    (output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    with gzip.open(dataset/'examples.jsonl.gz','rt') as f:rows=[json.loads(line) for line in f]
    count=0
    async with SC2Process(base_build=metadata['BaseBuild'],data_hash=metadata['DataVersion']) as server:
        info=(await server._execute(replay_info=pb.RequestReplayInfo(replay_data=replay.read_bytes()))).replay_info
        validate_replay_info(info,receipt['player']['player_info']['player_id'])
        response=await server._execute(start_replay=pb.RequestStartReplay(replay_data=replay.read_bytes(),observed_player_id=receipt['player']['player_info']['player_id'],options=pb.InterfaceOptions(raw=True,score=True,raw_affects_selection=False,raw_crop_to_playable_area=False),disable_fog=False,realtime=False))
        if response.start_replay.HasField('error'):raise RuntimeError(protocol_dict(response.start_replay))
        view=PlayerView()
        packet=(await server._execute(observation=pb.RequestObservation())).observation
        state=view.observe(packet);loop=state['game_loop']
        with gzip.open(output/'availability.jsonl.gz','xt') as f:
            for row in rows:
                target=row['observation']['game_loop']
                assert target==row['action_loop']-1 and target>=loop
                while loop<target:
                    await server._execute(step=pb.RequestStep(count=1))
                    packet=(await server._execute(observation=pb.RequestObservation())).observation
                    state=view.observe(packet);loop=state['game_loop']
                assert loop==target
                own=lambda s:{u['tag']:u for u in s['units'] if u['alliance']==1}
                actual=own(state);saved=own(row['observation'])
                if actual!=saved:
                    changed=[]
                    for tag in sorted(set(actual)|set(saved)):
                        a=actual.get(tag,{});b=saved.get(tag,{})
                        delta={k:{'actual':a.get(k),'saved':b.get(k)} for k in set(a)|set(b) if a.get(k)!=b.get(k)}
                        if delta:changed.append({'tag':tag,'fields':delta})
                    (output/'state-mismatch.json').write_text(json.dumps({'loop':loop,'changed':changed},indent=2)+'\n')
                    raise ValueError(f'Pre-command own-unit state mismatch at {loop}')
                tags=sorted(set(actual)|{u['tag'] for u in row['observation'].get('owned_memory',[]) if u['alliance']==1})
                response=(await server._execute(query=ability_query(tags))).query
                entries={e.unit_tag:{'unit_type':e.unit_type_id,'abilities':[a.ability_id for a in e.abilities]} for e in response.abilities}
                if set(entries)!=set(tags):raise ValueError('Native query did not return all requested own tags')
                f.write(json.dumps({'action_loop':row['action_loop'],'observation_loop':loop,'available':entries},separators=(',',':'))+'\n');count+=1
        await server.quit()
    assert hashes()==before
    report=dict(contract,status='completed',captured_rows=count,wall_seconds=time.monotonic()-start,files_after=hashes(),availability_sha256=hashlib.sha256((output/'availability.jsonl.gz').read_bytes()).hexdigest())
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return {'status':'completed','captured_rows':count,'wall_seconds':report['wall_seconds']}

def worker(job):return asyncio.run(capture(job))

if __name__=='__main__':
    result=supervise(worker,({'dataset':str(DATASET.resolve()),'output':str(OUTPUT.resolve())},),120)
    (ROOT/'replay-legality-rom-03.supervision.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    if result['status']!='completed':raise SystemExit(1)
