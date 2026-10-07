"""Frozen scripted Terran development panel; sequential and CPU guarded."""
import hashlib
import json
import threading
from pathlib import Path
import psutil
from src.runner import play_job
from src.runtime import supervise

OUT = Path('logs/roadmap/primitives-hard-baseline-01/panel')


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), Path('src/runner.py'), Path('src/bots/primitive_terran.py'),
             Path('src/bots/terran_primitives.py'), Path('src/learning/production_clearance.py'),
             Path('src/learning/gameplay.py'), Path('src/learning/live.py')]
    bindings = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    matrix = [(r,b,m) for r in ('Terran','Zerg','Protoss')
              for m in ('AcropolisLE','AbyssalReefLE')
              for b in ('Rush','Timing','Power','Macro','Air')]
    # Interleave races; every job is frozen before any result is observed.
    matrix.sort(key=lambda x: (x[2], x[1], x[0]))
    jobs = [dict(bot='primitives', race=r, build=b, seed=819001+i, difficulty='Hard',
                 map=m, game_step=8, game_seconds=1200, dev=False,
                 replay=str((OUT/f'{r}-{b}-{m}'/'game.SC2Replay').resolve()))
            for i, (r,b,m) in enumerate(matrix)]
    for job in jobs:
        Path(job['replay']).parent.mkdir()
    (OUT/'contract.json').write_text(json.dumps(dict(jobs=jobs, bindings=bindings, training=False,
        rl=False, controller='scripted', acceptance=dict(min_wins=21, min_wins_per_race=7, games=30, games_per_race=10, failures_count_as_nonwins=True), wall_seconds=300, whole_host_cpu_limit=80), indent=2)+'\n')
    stop, done = threading.Event(), threading.Event()
    samples = []
    def watch():
        high = 0
        while not done.is_set():
            cpu = psutil.cpu_percent(interval=1)
            samples.append(cpu)
            high = high+1 if cpu > 80 else 0
            if high >= 3:
                stop.set()
            done.wait(4)
    assert psutil.cpu_percent(interval=1) < 70, 'Insufficient CPU headroom'
    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    results = []
    try:
        for job in jobs:
            if stop.is_set():
                break
            result = dict(job=job, **supervise(play_job, (job,), 300, stop_event=stop))
            results.append(result)
            (OUT/'progress.json').write_text(json.dumps(results, indent=2)+'\n')
            print(json.dumps(result), flush=True)
            if result['status'] not in ('completed', 'truncated'):
                break
    finally:
        done.set()
        watcher.join(6)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p,h in bindings.items())
    (OUT/'report.json').write_text(json.dumps(dict(results=results, bindings=bindings, cpu_samples=samples,
        peak_cpu=max(samples, default=0), training=False, rl=False,
        status='completed' if len(results)==30 and all(r['status'] in ('completed','truncated') for r in results) else 'stopped'), indent=2)+'\n')


if __name__ == '__main__':
    main()
