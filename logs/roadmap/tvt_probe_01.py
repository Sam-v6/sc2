"""Diagnostic (training seeds only): VeryHard TvT over 5 builds x 5 maps x REPEATS.

Usage: tvt_probe_01.py OUT_DIR SEED_START REPEATS
Runs against whatever bot source is on PYTHONPATH, so two checkouts give a paired code comparison.
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

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT/'logs/roadmap/strategy-imitation-fit-01/policy.npz'
OFFSETS = ROOT/'logs/roadmap/strategy-offsets-final-01/zero-terran.json'
BUILDS = ('Rush', 'Timing', 'Power', 'Macro', 'Air')
MAPS = ('AcropolisLE', 'AbyssalReefLE', 'OdysseyLE', 'InterloperLE', 'CatalystLE')


def main():
    out, start, repeats = Path(sys.argv[1]).resolve(), int(sys.argv[2]), int(sys.argv[3])
    games = [(b, m) for _ in range(repeats) for b in BUILDS for m in MAPS]
    out.mkdir(parents=True, exist_ok=False)
    sources = ['src/bots/primitive_terran.py', 'src/bots/terran_primitives.py', 'src/bots/macro_rules.py']
    bindings = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources}
    jobs = [dict(bot='searched-strategy', strategy_policy=str(POLICY), strategy_offsets=json.loads(OFFSETS.read_text()),
                 race='Terran', build=b, map=m, seed=start+i, difficulty='VeryHard', game_step=8,
                 game_seconds=1200, dev=False, replay=str(out/f'{b}-{m}-{start+i}'/'game.SC2Replay'))
            for i, (b, m) in enumerate(games)]
    for job in jobs:
        Path(job['replay']).parent.mkdir()
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
            return dict(seed=job['seed'], build=job['build'], map=job['map'], status='skipped_cpu_guard', result=None)
        r = supervise(play_job, (job,), 300, stop_event=stop)
        row = dict(seed=job['seed'], build=job['build'], map=job['map'], status=r['status'], result=r.get('result'), seconds=r.get('game_seconds'))
        print(json.dumps(row), flush=True)
        return row

    try:
        with ThreadPoolExecutor(4) as pool:
            rows = list(pool.map(play, jobs))
    finally:
        done.set()
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in bindings.items())
    wins = sum(r['result'] == 'Victory' for r in rows)
    (out/'report.json').write_text(json.dumps(dict(wins=wins, games=len(rows), rows=rows, bindings=bindings), indent=2)+'\n')
    print(json.dumps(dict(wins=wins, games=len(rows))))


if __name__ == '__main__':
    main()
