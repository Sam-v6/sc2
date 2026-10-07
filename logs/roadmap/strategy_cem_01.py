"""Stage B: cross-entropy search of per-race strategy offsets vs VeryHard.

Base policy: Stage A imitation head. Each iteration samples CANDIDATES offset sets per
race, plays GAMES each vs that race on random builds/maps (training seeds 900000+),
and refits the race's Gaussian to the ELITES. State is saved after every iteration;
rerunning resumes. Evaluation must use fresh panel seeds, never these.
"""
import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import psutil

from src.learning.strategy_offsets import (
    RACES, cem_update, fitness, flatten, initial_distribution, sample_params, unflatten)
from src.runner import play_job
from src.runtime import supervise

OUT = Path('logs/roadmap/strategy-cem-01')
POLICY = Path('logs/roadmap/strategy-imitation-fit-01/policy.npz').resolve()
ITERATIONS, CANDIDATES, GAMES, ELITES, WORKERS = 8, 10, 2, 3, 5
BUILDS, MAPS = ('Rush', 'Timing', 'Power', 'Macro', 'Air'), ('AcropolisLE', 'AbyssalReefLE')


def as_json(params):
    return {r: {k: v.tolist() for k, v in p.items()} for r, p in params.items()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    state_path = OUT/'state.json'
    if state_path.exists():
        saved = json.loads(state_path.read_text())
        mean = {r: unflatten(np.array(v)) for r, v in saved['mean'].items()}
        std = {r: unflatten(np.array(v)) for r, v in saved['std'].items()}
        iteration = saved['iteration']
    else:
        mean, std = initial_distribution()
        iteration = 0
    floor = {r: .15 * flatten(initial_distribution()[1][r]) for r in RACES}
    bindings = {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in
                (__file__, POLICY, 'src/learning/strategy_offsets.py', 'src/bots/searched_strategy_terran.py',
                 'src/bots/learned_strategy_terran.py', 'src/bots/primitive_terran.py', 'src/bots/terran_primitives.py')}
    (OUT/'contract.json').write_text(json.dumps(dict(bindings=bindings, iterations=ITERATIONS, candidates=CANDIDATES,
                                                     games=GAMES, elites=ELITES, difficulty='VeryHard'), indent=2)+'\n')
    stop, done = threading.Event(), threading.Event()

    def watch():
        high = 0
        while not done.is_set():
            high = high+1 if psutil.cpu_percent(interval=1) > 80 else 0
            if high >= 3:
                stop.set()
            done.wait(4)

    threading.Thread(target=watch, daemon=True).start()
    try:
        while iteration < ITERATIONS and not stop.is_set():
            rng = np.random.default_rng(1000 + iteration)
            jobs, samples = [], {r: [] for r in RACES}
            for race in RACES:
                for c in range(CANDIDATES):
                    params, flat = sample_params(mean, std, race, rng)
                    samples[race].append(flat)
                    for g in range(GAMES):
                        seed = 900000 + iteration*1000 + RACES.index(race)*100 + c*GAMES + g
                        name = f'i{iteration}-{race}-c{c}-g{g}'
                        jobs.append(dict(bot='searched-strategy', strategy_policy=str(POLICY), strategy_offsets=as_json(params),
                                         race=race, build=str(rng.choice(BUILDS)), map=str(rng.choice(MAPS)), seed=seed,
                                         difficulty='VeryHard', game_step=8, game_seconds=1200, dev=False,
                                         replay=str((OUT/'games'/name/'game.SC2Replay').resolve()), candidate=c, name=name))
            for job in jobs:
                Path(job['replay']).parent.mkdir(parents=True, exist_ok=True)

            def play(job):
                if stop.is_set():
                    return dict(job=job, status='skipped_cpu_guard', result=None)
                return dict(job=job, **supervise(play_job, ({k: v for k, v in job.items() if k not in ('candidate', 'name')},),
                                                  300, stop_event=stop))

            with ThreadPoolExecutor(WORKERS) as pool:
                results = list(pool.map(play, jobs))
            if stop.is_set():
                break
            with (OUT/'results.jsonl').open('a') as f:
                for r in results:
                    f.write(json.dumps(dict(iteration=iteration, race=r['job']['race'], candidate=r['job']['candidate'],
                                            build=r['job']['build'], map=r['job']['map'], seed=r['job']['seed'],
                                            status=r['status'], result=r.get('result'), seconds=r.get('game_seconds', 0),
                                            fitness=fitness(r.get('result'), r.get('game_seconds', 0) or 0)))+'\n')
            summary = {}
            for race in RACES:
                scores = np.zeros(CANDIDATES)
                for r in results:
                    if r['job']['race'] == race:
                        scores[r['job']['candidate']] += fitness(r.get('result'), r.get('game_seconds', 0) or 0) / GAMES
                new_mean, new_std = cem_update(np.array(samples[race]), scores, ELITES, flatten(mean[race]),
                                               flatten(std[race]), floor[race])
                mean[race], std[race] = unflatten(new_mean), unflatten(new_std)
                wins = sum(r.get('result') == 'Victory' for r in results if r['job']['race'] == race)
                summary[race] = dict(wins=wins, games=CANDIDATES*GAMES, mean_fitness=float(scores.mean()),
                                     best_fitness=float(scores.max()))
            iteration += 1
            state_path.write_text(json.dumps(dict(iteration=iteration, mean={r: flatten(m).tolist() for r, m in mean.items()},
                                                  std={r: flatten(s).tolist() for r, s in std.items()}))+'\n')
            (OUT/f'mean-offsets-i{iteration}.json').write_text(json.dumps(as_json(mean), indent=1)+'\n')
            print(json.dumps(dict(iteration=iteration, **summary)), flush=True)
    finally:
        done.set()


if __name__ == '__main__':
    main()
