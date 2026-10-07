"""Run explicit scripted-bot comparisons; learning is in src.rl.train."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import random
import sys
import time

# Preserve python src/runner.py as well as python -m src.runner.
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.path import SC2_GAME_PATH, SC2_VOID_BOT_HOME
from src.runtime import match_id, supervise

from sc2 import maps
from sc2.data import AIBuild, Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer

BOTS = {
    'primitives': ('src.bots.primitive_terran', 'PrimitiveTerranBot', Race.Terran),
    'learned-strategy': ('src.bots.learned_strategy_terran', 'LearnedStrategyTerranBot', Race.Terran),
    'reaper': ('src.bots.mass_reaper', 'MassReaperBot', Race.Terran),
    'battlecruiser': ('src.bots.one_base_battlecruiser', 'BCRushBot', Race.Terran),
    'proxy': ('src.bots.proxy_rax', 'ProxyRaxBot', Race.Terran),
    'warpgate': ('src.bots.warpgate_push', 'WarpGateBot', Race.Protoss),
    'zergling': ('src.bots.zerg_rush', 'ZergRushBot', Race.Zerg),
}


def positive(value):
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError('must be positive')
    return value


def validate_map(name):
    game = Path(SC2_GAME_PATH)
    if not (game / 'Versions').is_dir():
        raise FileNotFoundError(f'SC2 installation missing at {game}; set SC2PATH')
    try:
        return maps.get(name)
    except KeyError as error:
        raise FileNotFoundError(str(error)) from error


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bot', choices=BOTS, default='reaper')
    p.add_argument('--map', default='Simple64')
    p.add_argument('--race', choices=['Terran', 'Protoss', 'Zerg'], default='Zerg')
    p.add_argument('--difficulty', choices=[d.name for d in Difficulty], default='Hard')
    p.add_argument('--build', choices=[b.name for b in AIBuild], default='RandomBuild')
    p.add_argument('--games', type=positive, default=1)
    p.add_argument('--workers', type=positive, default=4)
    p.add_argument('--game-step', type=positive, default=8)
    p.add_argument('--game-seconds', type=positive, default=1200)
    p.add_argument('--wall-seconds', type=positive, default=300)
    p.add_argument('--seed', type=int, default=7)
    p.add_argument('--dev', action='store_true', help='Save score telemetry')
    p.add_argument('--output', type=Path, default=Path(SC2_VOID_BOT_HOME) / 'logs/scripted')
    return p


def play_job(job):
    from importlib import import_module
    from loguru import logger
    logger.remove()
    logger.add(sys.stderr, level='WARNING')
    random.seed(job['seed'])
    if job['dev']:
        os.environ['DEV'] = '1'
    else:
        os.environ.pop('DEV', None)
    module, name, race = BOTS[job['bot']]
    bot = getattr(import_module(module), name)()
    bot.requested_game_step = job['game_step']
    if job['bot'] == 'learned-strategy':
        bot.policy_path = job['strategy_policy']
    if job['bot'] in ('primitives', 'learned-strategy'):
        bot.trace_path = str(Path(job['replay']).with_suffix('.primitives.jsonl.gz'))
    start = time.monotonic()
    result = run_game(validate_map(job['map']),
                      [Bot(race, bot), Computer(Race[job['race']], Difficulty[job['difficulty']], AIBuild[job['build']])],
                      realtime=False, random_seed=job['seed'], game_time_limit=job['game_seconds'],
                      save_replay_as=job['replay'])
    if getattr(bot, 'callback_error', None) or not getattr(bot, 'started', False):
        return {'status': 'error', 'result': None, 'error': getattr(bot, 'callback_error', 'Bot did not initialize')}
    replay = Path(job['replay'])
    if not replay.is_file() or replay.stat().st_size == 0:
        raise RuntimeError('Game did not save a replay')
    return {**({'primitives': bot.summary} if job['bot'] in ('primitives', 'learned-strategy') else {}),
            'status': 'truncated' if result.name == 'Tie' else 'completed',
            'result': result.name, 'game_seconds': bot.time, 'engine_wall_seconds': time.monotonic() - start,
            'replay_bytes': replay.stat().st_size}


def main():
    args = parser().parse_args()
    validate_map(args.map)
    args.output.mkdir(parents=True, exist_ok=True)
    jobs = []
    for index in range(args.games):
        job = vars(args).copy()
        job['output'] = str(args.output.resolve())
        job['seed'] = args.seed + index
        job['id'] = match_id()
        job['replay'] = str(args.output.resolve() / f"{job['id']}.SC2Replay")
        jobs.append(job)
    failed = False
    with ThreadPoolExecutor(max_workers=min(args.workers, args.games)) as pool:
        futures = [(job, pool.submit(supervise, play_job, (job,), args.wall_seconds)) for job in jobs]
        for job, future in futures:
            receipt = {**job, **future.result()}
            (args.output / f"{job['id']}.json").write_text(json.dumps(receipt, indent=2) + '\n')
            print(json.dumps(receipt), flush=True)
            failed |= receipt['status'] in ('error', 'wall_timeout')
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
