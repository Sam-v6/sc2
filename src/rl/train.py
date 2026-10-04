"""Bounded training, resume, and frozen evaluation against SC2 computers."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
import time

from src.path import SC2_VOID_BOT_HOME
from src.runtime import match_id, supervise
from src.runner import positive, validate_map
from src.rl.returns import remember_episode
from src.rl.policy import Policy
from src.rl.terran import ACTIONS, FEATURES, TerranLearner
from sc2.data import AIBuild, Difficulty, Race
from sc2.main import run_game, get_replay_version
from sc2.player import Bot, Computer


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def episode(job):
    from loguru import logger
    logger.remove()
    logger.add(sys.stderr, level='WARNING')
    random.seed(job['seed'])
    policy = Policy.load(job['checkpoint'], FEATURES, ACTIONS)
    before = policy.updates
    if job['mode'] == 'random':
        policy.epsilon = 1
    bot = TerranLearner(policy, training=job['mode'] == 'train', action_log=job['actions'],
                        macro_seconds=job['macro_seconds'], random_policy=job['mode'] == 'random')
    started = time.monotonic()
    result = run_game(validate_map(job['map']),
                      [Bot(Race.Terran, bot), Computer(Race[job['race']], Difficulty[job['difficulty']], AIBuild[job['build']])],
                      realtime=False, random_seed=job['seed'], game_time_limit=job['game_limit'], save_replay_as=job['replay'])
    if bot.callback_error or not bot.started:
        raise RuntimeError(bot.callback_error or 'Bot failed to initialize')
    replay = Path(job['replay'])
    if not replay.is_file() or not replay.stat().st_size:
        raise RuntimeError('No replay was saved')
    losses = []
    if job['mode'] == 'train':
        remember_episode(policy, bot.transitions)
        for _ in bot.transitions:
            losses.append(policy.learn())
        policy.episodes += 1
        policy.epsilon = max(.05, .5 * (.995 ** policy.episodes))
        policy.save(job['candidate'])
    return {'status': 'truncated' if result.name == 'Tie' else 'completed', 'result': result.name,
            'game_seconds': bot.time, 'engine_wall_seconds': round(time.monotonic() - started, 3),
            'decisions': len(bot.decisions), 'transitions': len(bot.transitions),
            'updates_before': before, 'updates_after': policy.updates, 'epsilon': policy.epsilon,
            'mean_loss': sum(losses) / len(losses) if losses else None,
            'reward': sum(t[2] for t in bot.transitions), 'replay_bytes': replay.stat().st_size,
            'replay_version': get_replay_version(str(replay)),
            'workers': bot.workers.amount, 'army_supply': bot.supply_army, 'bases': bot.townhalls.amount}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode', choices=['train', 'evaluate', 'random'], default='train')
    p.add_argument('--episodes', type=positive, default=10)
    p.add_argument('--checkpoint', type=Path, default=Path(SC2_VOID_BOT_HOME) / 'logs/rl/policy.npz')
    p.add_argument('--output', type=Path, default=Path(SC2_VOID_BOT_HOME) / 'logs/rl')
    p.add_argument('--maps', nargs='+', default=['Simple64'])
    p.add_argument('--races', nargs='+', choices=['Terran', 'Protoss', 'Zerg'], default=['Terran', 'Protoss', 'Zerg'])
    p.add_argument('--builds', nargs='+', choices=[b.name for b in AIBuild], default=['RandomBuild'])
    p.add_argument('--difficulty', choices=[d.name for d in Difficulty], default='Hard')
    p.add_argument('--seed', type=int, default=None)
    p.add_argument('--game-seconds', type=positive, default=1200)
    p.add_argument('--wall-seconds', type=positive, default=300)
    p.add_argument('--macro-seconds', type=positive, default=5)
    return p


def main():
    args = parser().parse_args()
    for name in args.maps:
        validate_map(name)
    args.output.mkdir(parents=True, exist_ok=True)
    checkpoint = args.checkpoint.resolve()
    if not checkpoint.exists():
        if args.mode != 'train':
            raise FileNotFoundError(f'Checkpoint not found: {checkpoint}')
        initial = Policy(FEATURES, ACTIONS, seed=args.seed if args.seed is not None else 7)
        initial.gamma = .99 ** (args.macro_seconds / 5)
        initial.save(checkpoint)
    policy = Policy.load(checkpoint, FEATURES, ACTIONS)
    offset = policy.episodes if args.mode == 'train' else 0
    seed_start = args.seed if args.seed is not None else (7 if args.mode == 'train' else 10000)
    provenance = {str(path.relative_to(Path(__file__).parents[2])): digest(path)
                  for path in (Path(__file__), Path(__file__).with_name('terran.py'),
                               Path(__file__).with_name('policy.py'), Path(__file__).with_name('returns.py'), Path(__file__).parents[1] / 'runtime.py')}
    receipts = []
    run_id = match_id()
    checkpoint_before = digest(checkpoint)
    try:
        for index in range(args.episodes):
            episode_index = offset + index
            identity = match_id()
            base = args.output.resolve() / identity
            job = {'id': identity, 'run': run_id, 'mode': args.mode, 'checkpoint': str(checkpoint),
                   'source_sha256': provenance, 'map_sha256': digest(validate_map(args.maps[(episode_index // (len(args.races) * len(args.builds))) % len(args.maps)]).path),
                   'checkpoint_before': digest(checkpoint), 'candidate': str(base.with_suffix('.candidate.npz')),
                   'actions': str(base.with_suffix('.actions.jsonl')), 'replay': str(base.with_suffix('.SC2Replay')),
                   'race': args.races[episode_index % len(args.races)],
                   'build': args.builds[(episode_index // len(args.races)) % len(args.builds)],
                   'map': args.maps[(episode_index // (len(args.races) * len(args.builds))) % len(args.maps)],
                   'difficulty': args.difficulty, 'seed': seed_start + episode_index,
                   'game_limit': args.game_seconds, 'macro_seconds': args.macro_seconds}
            receipt = {**job, **supervise(episode, (job,), args.wall_seconds)}
            if args.mode == 'train' and receipt['status'] in ('completed', 'truncated'):
                Path(job['candidate']).replace(checkpoint)
            else:
                Path(job['candidate']).unlink(missing_ok=True)
            receipt['checkpoint_after'] = digest(checkpoint)
            base.with_suffix('.json').write_text(json.dumps(receipt, indent=2) + '\n')
            receipts.append(receipt)
            print(json.dumps(receipt), flush=True)
            if receipt['status'] in ('error', 'wall_timeout'):
                break
    finally:
        counts = {name: sum(r['result'] == name for r in receipts) for name in ('Victory', 'Defeat', 'Tie')}
        summary = {'run': run_id, 'mode': args.mode, 'requested': args.episodes, 'finished': len(receipts),
                   'interrupted': len(receipts) < args.episodes and not any(r['status'] in ('error', 'wall_timeout') for r in receipts),
                   'source_sha256': provenance, 'counts': counts, 'failures': sum(r['status'] in ('error', 'wall_timeout') for r in receipts),
                   'checkpoint_before': checkpoint_before, 'checkpoint_after': digest(checkpoint),
                   'receipts': [r['id'] for r in receipts]}
        (args.output / f'{run_id}.summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    if summary['failures']:
        raise SystemExit(1)
    if args.mode == 'evaluate' and summary['checkpoint_before'] != summary['checkpoint_after']:
        raise RuntimeError('Frozen evaluation changed the checkpoint')


if __name__ == '__main__':
    main()
