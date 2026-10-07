"""Index 3.16.1 ladder replay packs (metadata only) with the matching 3.16.1 engine.

Run with SC2PATH pointing at the 3.16.1 install. Appends one JSON line per replay;
rerunning skips replays already indexed. Usage: replay_index_3161_01.py PACK_DIR OUT.jsonl
"""
import asyncio
import json
import sys
from multiprocessing import Pool
from pathlib import Path

from s2clientprotocol import common_pb2 as common, sc2api_pb2 as pb
from sc2.sc2process import SC2Process

WORKERS = 6


async def index(paths):
    rows = []
    async with SC2Process() as server:
        for path in paths:
            info = (await server._execute(replay_info=pb.RequestReplayInfo(replay_path=str(path)))).replay_info
            rows.append(dict(replay=path.name, map=info.map_name, version=info.game_version,
                             base_build=info.base_build, seconds=info.game_duration_seconds,
                             loops=info.game_duration_loops, error=info.error,
                             players=[dict(id=p.player_info.player_id, race=common.Race.Name(p.player_info.race_actual),
                                           result=p.player_result.result, mmr=p.player_mmr, apm=p.player_apm)
                                      for p in info.player_info]))
    return rows


def run(paths):
    from loguru import logger
    logger.remove()
    return asyncio.run(index(paths))


def main():
    pack, out = Path(sys.argv[1]), Path(sys.argv[2])
    done = {json.loads(line)['replay'] for line in out.open()} if out.exists() else set()
    paths = [p for p in sorted(pack.glob('*.SC2Replay')) if p.name not in done]
    chunks = [paths[i:i + 500] for i in range(0, len(paths), 500)]
    with Pool(WORKERS) as pool, out.open('a') as f:
        for rows in pool.imap_unordered(run, chunks):
            f.writelines(json.dumps(row) + '\n' for row in rows)
            f.flush()
            print(len(rows), flush=True)


if __name__ == '__main__':
    main()
