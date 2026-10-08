"""Paired comparison of strategy-offset files on identical games (training seeds only).

Usage: offsets_ab.py OUT_DIR RACE SEED_BASE REPEATS NAME=OFFSETS.json [NAME=OFFSETS.json ...]
Every variant plays REPEATS x 5 builds x 2 maps games vs VeryHard RACE with the same seeds.
"""
import hashlib
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psutil

from src.runner import play_job
from src.runtime import supervise

POLICY = Path('logs/roadmap/strategy-imitation-fit-01/policy.npz').resolve()
BUILDS, MAPS, WORKERS = ('Rush', 'Timing', 'Power', 'Macro', 'Air'), ('AcropolisLE', 'AbyssalReefLE'), 5
SOURCES = ['src/runner.py', 'src/bots/primitive_terran.py', 'src/bots/terran_primitives.py',
           'src/bots/learned_strategy_terran.py', 'src/bots/searched_strategy_terran.py',
           'src/learning/strategy_offsets.py', 'src/learning/strategy_policy.py']


def main():
    out, race, seed, repeats = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    variants = dict(arg.split('=', 1) for arg in sys.argv[5:])
    out.mkdir(parents=True, exist_ok=False)
    bindings = {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest()
                for p in [__file__, POLICY, *SOURCES, *variants.values()]}
    games = [(b, m, seed + i) for i, (b, m) in enumerate((b, m) for _ in range(repeats) for b in BUILDS for m in MAPS)]
    jobs = [dict(variant=v, bot='searched-strategy', strategy_policy=str(POLICY),
                 strategy_offsets=json.loads(Path(f).read_text()), race=race, build=b, map=m, seed=s,
                 difficulty='VeryHard', game_step=8, game_seconds=1200, dev=False,
                 replay=str((out/v/f'{b}-{m}-{s}'/'game.SC2Replay').resolve()))
            for b, m, s in games for v, f in variants.items()]
    for job in jobs:
        Path(job['replay']).parent.mkdir(parents=True)
    (out/'contract.json').write_text(json.dumps(dict(bindings=bindings, variants=variants, games=games), indent=2)+'\n')
    stop, done = threading.Event(), threading.Event()

    def watch():
        high = 0
        while not done.is_set():
            high = high+1 if psutil.cpu_percent(interval=1) > 80 else 0
            if high >= 3:
                stop.set()
            done.wait(4)

    threading.Thread(target=watch, daemon=True).start()

    def play(job):
        if stop.is_set():
            return dict(job=job, status='skipped_cpu_guard', result=None)
        r = supervise(play_job, ({k: v for k, v in job.items() if k != 'variant'},), 300, stop_event=stop)
        print(json.dumps(dict(variant=job['variant'], build=job['build'], map=job['map'], seed=job['seed'],
                              status=r['status'], result=r.get('result'), seconds=r.get('game_seconds'))), flush=True)
        return dict(job=job, **r)

    try:
        with ThreadPoolExecutor(WORKERS) as pool:
            results = list(pool.map(play, jobs))
    finally:
        done.set()
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in bindings.items())
    summary = {v: {b: sum(r.get('result') == 'Victory' for r in results if r['job']['variant'] == v and r['job']['build'] == b)
                   for b in BUILDS} for v in variants}
    for v in summary:
        summary[v]['total'] = sum(summary[v].values())
    (out/'report.json').write_text(json.dumps(dict(summary=summary, results=results, bindings=bindings), indent=2)+'\n')
    print(json.dumps(dict(summary=summary)))


if __name__ == '__main__':
    main()
