"""Frozen 30-game Terran panel (3 races x 2 maps x 5 builds), parallel and CPU guarded.

Usage: panel.py OUT_DIR BOT DIFFICULTY SEED_BASE [STRATEGY_POLICY]
Same contract as the scripted Hard baseline: 1200 game s, 300 wall s, step 8,
failures count as non-wins, 80% whole-host CPU guard; WORKERS games run at once.
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

WORKERS = 4
SOURCES = ['src/runner.py', 'src/bots/primitive_terran.py', 'src/bots/terran_primitives.py',
           'src/bots/learned_strategy_terran.py', 'src/learning/strategy_policy.py',
           'src/learning/production_clearance.py', 'src/learning/gameplay.py', 'src/learning/live.py']


def main():
    out, bot, difficulty, seed = Path(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4])
    policy = Path(sys.argv[5]).resolve() if len(sys.argv) > 5 else None
    out.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), *map(Path, SOURCES), *([policy] if policy else [])]
    bindings = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    matrix = sorted([(r, b, m) for r in ('Terran', 'Zerg', 'Protoss') for m in ('AcropolisLE', 'AbyssalReefLE')
                     for b in ('Rush', 'Timing', 'Power', 'Macro', 'Air')], key=lambda x: (x[2], x[1], x[0]))
    jobs = [dict(bot=bot, race=r, build=b, seed=seed+i, difficulty=difficulty, map=m, game_step=8,
                 game_seconds=1200, dev=False, replay=str((out/f'{r}-{b}-{m}'/'game.SC2Replay').resolve()),
                 **({'strategy_policy': str(policy)} if policy else {}))
            for i, (r, b, m) in enumerate(matrix)]
    for job in jobs:
        Path(job['replay']).parent.mkdir()
    (out/'contract.json').write_text(json.dumps(dict(jobs=jobs, bindings=bindings, workers=WORKERS, wall_seconds=300,
                                                     whole_host_cpu_limit=80), indent=2)+'\n')
    stop, done, samples = threading.Event(), threading.Event(), []

    def watch():
        high = 0
        while not done.is_set():
            samples.append(psutil.cpu_percent(interval=1))
            high = high+1 if samples[-1] > 80 else 0
            if high >= 3:
                stop.set()
            done.wait(4)

    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()

    def play(job):
        if stop.is_set():
            return dict(job=job, status='skipped_cpu_guard', result=None)
        result = dict(job=job, **supervise(play_job, (job,), 300, stop_event=stop))
        print(json.dumps(dict(race=job['race'], build=job['build'], map=job['map'], status=result['status'],
                              result=result.get('result'))), flush=True)
        return result

    try:
        with ThreadPoolExecutor(WORKERS) as pool:
            results = list(pool.map(play, jobs))
    finally:
        done.set()
        watcher.join(6)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in bindings.items())
    wins = sum(r.get('result') == 'Victory' for r in results)
    (out/'report.json').write_text(json.dumps(dict(results=results, bindings=bindings, wins=wins,
                                                   peak_cpu=max(samples, default=0), cpu_samples=samples), indent=2)+'\n')
    print(json.dumps(dict(wins=wins, games=len(results))))


if __name__ == '__main__':
    main()
