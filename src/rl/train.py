"""Bounded training, resume, and frozen evaluation against SC2 computers."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import threading
import numpy as np
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


def check_training_cadence(policy, requested, legacy):
    stored = policy.macro_seconds if policy.macro_seconds is not None else legacy
    if stored is None:
        raise ValueError('Legacy checkpoint has no cadence; declare its original --legacy-macro-seconds')
    if requested != stored:
        raise ValueError(f'Training cadence mismatch: checkpoint {stored}s, requested {requested}s; use a fresh checkpoint')
    policy.macro_seconds = stored


def episode(job):
    from loguru import logger
    logger.remove()
    logger.add(sys.stderr, level='WARNING')
    random.seed(job['seed'])
    policy = Policy.load(job['checkpoint'], FEATURES, ACTIONS)
    before = policy.updates
    if job['mode'] != 'evaluate':
        policy.rng = np.random.default_rng(job['policy_seed'])
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
    if job['mode'] == 'train':
        policy.experience.clear()
        policy.macro_seconds = job['macro_seconds']
        remember_episode(policy, bot.transitions)
        policy.save(job['candidate'])
    return {'status': 'truncated' if result.name == 'Tie' else 'completed', 'result': result.name,
            'game_seconds': bot.time, 'engine_wall_seconds': round(time.monotonic() - started, 3),
            'decisions': len(bot.decisions), 'transitions': len(bot.transitions),
            'updates_before': before, 'updates_after': policy.updates, 'epsilon': policy.epsilon,
            'reward': sum(t[2] for t in bot.transitions), 'replay_bytes': replay.stat().st_size,
            'replay_version': get_replay_version(str(replay)),
            'workers': bot.workers.amount, 'army_supply': bot.supply_army, 'bases': bot.townhalls.amount}


def learn_candidate(policy, path):
    collected = Policy.load(path, policy.features, policy.actions)
    before = policy.updates
    policy.experience.extend(collected.experience)
    losses = [policy.learn() for _ in collected.experience]
    policy.episodes += 1
    policy.epsilon = max(.05, .5 * (.995 ** policy.episodes))
    return {'learner_updates_before': before, 'learner_updates_after': policy.updates,
            'mean_loss': sum(losses) / len(losses) if losses else None}


def remove_candidate(path):
    path = Path(path)
    path.unlink(missing_ok=True)
    path.with_name(path.name + '.tmp').unlink(missing_ok=True)


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode', choices=['train', 'evaluate', 'random'], default='train')
    p.add_argument('--episodes', type=positive, default=10)
    p.add_argument('--workers', type=positive, default=4)
    p.add_argument('--checkpoint', type=Path, default=Path(SC2_VOID_BOT_HOME) / 'logs/rl/policy.npz')
    p.add_argument('--output', type=Path, default=Path(SC2_VOID_BOT_HOME) / 'logs/rl')
    p.add_argument('--maps', nargs='+', default=['Simple64'])
    p.add_argument('--races', nargs='+', choices=['Terran', 'Protoss', 'Zerg'], default=['Terran', 'Protoss', 'Zerg'])
    p.add_argument('--builds', nargs='+', choices=[b.name for b in AIBuild], default=['RandomBuild'])
    p.add_argument('--difficulty', choices=[d.name for d in Difficulty], default='Hard')
    p.add_argument('--seed', type=int, default=None)
    p.add_argument('--game-seconds', type=positive, default=1200)
    p.add_argument('--wall-seconds', type=positive, default=300)
    p.add_argument('--macro-seconds', type=positive, default=None)
    p.add_argument('--legacy-macro-seconds', type=positive, default=None, help='Declare the original cadence only for checkpoints missing that metadata')
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
        args.macro_seconds = args.macro_seconds or 5
        initial = Policy(FEATURES, ACTIONS, seed=args.seed if args.seed is not None else 7)
        initial.macro_seconds = args.macro_seconds
        initial.gamma = .99 ** (args.macro_seconds / 5)
        initial.save(checkpoint)
    policy = Policy.load(checkpoint, FEATURES, ACTIONS)
    args.macro_seconds = args.macro_seconds or policy.macro_seconds or args.legacy_macro_seconds or 5
    if args.mode == 'train':
        check_training_cadence(policy, args.macro_seconds, args.legacy_macro_seconds)
    offset = policy.attempts if args.mode == 'train' else 0
    seed_start = args.seed if args.seed is not None else (7 if args.mode == 'train' else 10000)
    source_root = Path(__file__).parents[2]
    provenance = {str(path.relative_to(source_root)): digest(path) for path in sorted((source_root / 'src').rglob('*.py'))}
    receipts = []
    run_id = match_id()
    checkpoint_before = digest(checkpoint)
    started = time.monotonic()
    stop = threading.Event()
    pool = ThreadPoolExecutor(max_workers=args.workers)
    active_jobs = []
    failed = ('error', 'wall_timeout', 'cancelled')
    try:
        for start in range(0, args.episodes, args.workers):
            active_jobs = []
            for index in range(start, min(start + args.workers, args.episodes)):
                episode_index = offset + index
                identity = match_id()
                base = args.output.resolve() / identity
                game_map = args.maps[(episode_index // (len(args.races) * len(args.builds))) % len(args.maps)]
                game_seed = seed_start + episode_index
                policy_seed = int(policy.rng.integers(2**63)) if args.mode == 'train' else game_seed
                job = {'id': identity, 'run': run_id, 'mode': args.mode, 'checkpoint': str(checkpoint),
                       'source_sha256': provenance, 'map_sha256': digest(validate_map(game_map).path),
                       'behavior_checkpoint_sha256': digest(checkpoint),
                       'checkpoint_before': digest(checkpoint), 'candidate': str(base.with_suffix('.candidate.npz')),
                       'actions': str(base.with_suffix('.actions.jsonl')), 'replay': str(base.with_suffix('.SC2Replay')),
                       'race': args.races[episode_index % len(args.races)],
                       'build': args.builds[(episode_index // len(args.races)) % len(args.builds)],
                       'map': game_map, 'difficulty': args.difficulty, 'seed': game_seed, 'policy_seed': policy_seed,
                       'game_limit': args.game_seconds, 'macro_seconds': args.macro_seconds}
                active_jobs.append(job)
            futures = [pool.submit(supervise, episode, (job,), args.wall_seconds, stop_event=stop) for job in active_jobs]
            # Collect the entire batch before replacing its shared behavior checkpoint.
            results = [future.result() for future in futures]
            for job, result in zip(active_jobs, results):
                receipt = {**job, **result}
                if args.mode == 'train' and receipt['status'] in ('completed', 'truncated'):
                    receipt.update(learn_candidate(policy, job['candidate']))
                    receipt['updates_after'] = policy.updates
                    receipt['epsilon_after'] = policy.epsilon
                    policy.attempts = offset + start + len(active_jobs)
                    policy.save(checkpoint)
                remove_candidate(job['candidate'])
                receipt['checkpoint_after'] = digest(checkpoint)
                Path(job['replay']).with_suffix('.json').write_text(json.dumps(receipt, indent=2) + '\n')
                receipts.append(receipt)
                print(json.dumps(receipt), flush=True)
            active_jobs = []
            if any(r['status'] in failed for r in receipts):
                break
    finally:
        stop.set()
        pool.shutdown(wait=True, cancel_futures=True)
        for job in active_jobs:
            remove_candidate(job['candidate'])
        counts = {name: sum(r['result'] == name for r in receipts) for name in ('Victory', 'Defeat', 'Tie')}
        summary = {'run': run_id, 'mode': args.mode, 'requested': args.episodes, 'finished': len(receipts),
                   'workers': args.workers, 'wall_seconds': round(time.monotonic() - started, 3),
                   'simulated_seconds': sum(r.get('game_seconds', 0) for r in receipts),
                   'interrupted': len(receipts) < args.episodes and not any(r['status'] in failed for r in receipts),
                   'source_sha256': provenance, 'counts': counts, 'failures': sum(r['status'] in failed for r in receipts),
                   'checkpoint_before': checkpoint_before, 'checkpoint_after': digest(checkpoint),
                   'receipts': [r['id'] for r in receipts]}
        (args.output / f'{run_id}.summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    if summary['failures']:
        raise SystemExit(1)
    if args.mode == 'evaluate' and summary['checkpoint_before'] != summary['checkpoint_after']:
        raise RuntimeError('Frozen evaluation changed the checkpoint')


if __name__ == '__main__':
    main()
