"""Extract strategy-head examples from 3.16.1 ladder replays (Terran player's fog-limited view).

Usage: replay_strategy_extract_3161_01.py INDEX.jsonl PACK_DIR OUT_DIR MIN_MMR LIMIT
Writes OUT_DIR/<replay>.npz (x, per-head labels) and OUT_DIR/receipts.jsonl.
Run with SC2PATH pointing at the 3.16.1 install.
"""
import asyncio
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from s2clientprotocol import sc2api_pb2 as pb

from src.learning.gameplay import PlayerView
from src.learning.live import protocol_dict
from src.learning.replay_strategy import human_strategy_labels
from src.learning.strategy_policy import HEADS, encode_targets, strategy_features

WORKERS = 4
STEP = 24
HORIZON = 1344  # 60 game seconds


async def extract(server, path, player, enemy_race, out):
    response = await server._execute(start_replay=pb.RequestStartReplay(
        replay_path=str(path), observed_player_id=player,
        options=pb.InterfaceOptions(raw=True, score=True), realtime=False, disable_fog=False))
    data = protocol_dict((await server._execute(data=pb.RequestData(unit_type_id=True))).data)
    types = {u['unit_id']: u for u in data['units']}
    info = (await server._execute(game_info=pb.RequestGameInfo())).game_info
    enemy_start = (info.start_raw.start_locations[0].x, info.start_raw.start_locations[0].y)
    view, states = PlayerView(), []
    while True:
        packet = (await server._execute(observation=pb.RequestObservation())).observation
        state = view.observe(packet)
        states.append(state)
        if packet.player_result:
            break
        step = await server._execute(step=pb.RequestStep(count=STEP))
        if step.status != pb.Status.in_replay:
            break
    own = [u for u in states[0]['units'] if u['alliance'] == 1 and u['unit_type'] in (18, 132, 130)]
    own_start = tuple(own[0]['position'][:2])
    labels = human_strategy_labels(states, own_start, enemy_start, HORIZON)
    xs, ys, previous = [], {h: [] for h in HEADS}, False
    for state, (targets, attack) in zip(states, labels):
        xs.append(strategy_features(state, previous, enemy_race, types))
        for head, index in encode_targets(targets, attack).items():
            ys[head].append(index)
        previous = attack
    np.savez_compressed(out, x=np.stack(xs), **{h: np.asarray(v, dtype=np.int16) for h, v in ys.items()})
    return dict(frames=len(xs), final_loop=states[-1]['game_loop'], start_error=response.start_replay.error)


async def work(jobs):
    from sc2.sc2process import SC2Process
    receipts = []
    async with SC2Process() as server:
        for job in jobs:
            try:
                receipts.append(dict(job, status='completed', **await extract(
                    server, Path(job['path']), job['player'], job['enemy_race'], job['out'])))
            except Exception as error:  # record and continue; one bad replay must not stop the batch
                receipts.append(dict(job, status='error', error=repr(error)))
    return receipts


def run(jobs):
    from loguru import logger
    logger.remove()
    return asyncio.run(work(jobs))


def main():
    index, pack, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    min_mmr, limit = int(sys.argv[4]), int(sys.argv[5])
    out.mkdir(parents=True, exist_ok=True)
    receipts = out / 'receipts.jsonl'
    done = {json.loads(line)['out'] for line in receipts.open()} if receipts.exists() else set()
    jobs = []
    for line in index.open():
        row = json.loads(line)
        if len(row['players']) != 2 or row['seconds'] < 300:
            continue
        for p, other in (row['players'], row['players'][::-1]):
            if p['race'] == 'Terran' and p['mmr'] >= min_mmr and other['race'] in ('Terran', 'Zerg', 'Protoss'):
                jobs.append(dict(replay=row['replay'], path=str(pack / row['replay']), player=p['id'],
                                 mmr=p['mmr'], result=p['result'], enemy_race=other['race'], map=row['map'],
                                 out=str(out / f"{row['replay'].removesuffix('.SC2Replay')}-p{p['id']}.npz")))
    jobs = [j for j in sorted(jobs, key=lambda j: -j['mmr'])[:limit] if j['out'] not in done]
    chunks = [jobs[i::WORKERS] for i in range(WORKERS)]
    chunks = [c[i:i + 25] for c in chunks for i in range(0, len(c), 25)]
    with Pool(WORKERS) as pool, receipts.open('a') as f:
        for rows in pool.imap_unordered(run, chunks):
            f.writelines(json.dumps(row) + '\n' for row in rows)
            f.flush()
            print(sum(r['status'] == 'completed' for r in rows), len(rows), flush=True)


if __name__ == '__main__':
    main()
