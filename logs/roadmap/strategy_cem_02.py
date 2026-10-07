"""Stage B rerun for TvT only, with common random numbers.

strategy-cem-01 drew a fresh random build/map per game with 2 games per candidate, so TvT
elites were mostly selected by which builds they happened to face and the TvT distribution
collapsed (11 -> 5 wins/20). Here every candidate in an iteration plays the same five games
(one per build, maps alternating, shared seeds), and candidate 0 is the unperturbed mean as a
control. Starts from zero offsets. Training seeds 910000+; evaluation must use fresh panel seeds.
"""
import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import psutil

from src.learning.strategy_offsets import cem_update, fitness, flatten, initial_distribution, sample_params, unflatten
from src.runner import play_job
from src.runtime import supervise

OUT = Path('logs/roadmap/strategy-cem-02')
POLICY = Path('logs/roadmap/strategy-imitation-fit-01/policy.npz').resolve()
RACE = 'Terran'
ITERATIONS, CANDIDATES, ELITES, WORKERS = 6, 10, 3, 5
BUILDS, MAPS = ('Rush', 'Timing', 'Power', 'Macro', 'Air'), ('AcropolisLE', 'AbyssalReefLE')


def as_json(params):
    return {r: {k: v.tolist() for k, v in p.items()} for r, p in params.items()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    state_path = OUT/'state.json'
    mean, std = initial_distribution()
    iteration = 0
    if state_path.exists():
        saved = json.loads(state_path.read_text())
        mean[RACE], std[RACE] = unflatten(np.array(saved['mean'])), unflatten(np.array(saved['std']))
        iteration = saved['iteration']
    floor = .15 * flatten(initial_distribution()[1][RACE])
    bindings = {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in
                (__file__, POLICY, 'src/learning/strategy_offsets.py', 'src/bots/searched_strategy_terran.py',
                 'src/bots/learned_strategy_terran.py', 'src/bots/primitive_terran.py', 'src/bots/terran_primitives.py')}
    (OUT/'contract.json').write_text(json.dumps(dict(bindings=bindings, race=RACE, iterations=ITERATIONS,
                                                     candidates=CANDIDATES, games=len(BUILDS), elites=ELITES,
                                                     difficulty='VeryHard', common_random_numbers=True), indent=2)+'\n')
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
            rng = np.random.default_rng(2000 + iteration)
            games = [(b, MAPS[(i + iteration) % 2], 910000 + iteration*100 + i) for i, b in enumerate(BUILDS)]
            jobs, samples = [], []
            for c in range(CANDIDATES):
                params, flat = sample_params(mean, std, RACE, rng)
                if c == 0:
                    params, flat = {r: dict(offsets=m['offsets'].copy(), attack=m['attack'].copy()) for r, m in mean.items()}, flatten(mean[RACE])
                samples.append(flat)
                for build, map_name, seed in games:
                    name = f'i{iteration}-c{c}-{build}'
                    jobs.append(dict(bot='searched-strategy', strategy_policy=str(POLICY), strategy_offsets=as_json(params),
                                     race=RACE, build=build, map=map_name, seed=seed, difficulty='VeryHard', game_step=8,
                                     game_seconds=1200, dev=False, replay=str((OUT/'games'/name/'game.SC2Replay').resolve()),
                                     candidate=c, name=name))
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
            scores = np.zeros(CANDIDATES)
            with (OUT/'results.jsonl').open('a') as f:
                for r in results:
                    score = fitness(r.get('result'), r.get('game_seconds', 0) or 0)
                    scores[r['job']['candidate']] += score / len(BUILDS)
                    f.write(json.dumps(dict(iteration=iteration, candidate=r['job']['candidate'], build=r['job']['build'],
                                            map=r['job']['map'], seed=r['job']['seed'], status=r['status'],
                                            result=r.get('result'), seconds=r.get('game_seconds', 0), fitness=score))+'\n')
            wins = [sum(r.get('result') == 'Victory' for r in results if r['job']['candidate'] == c) for c in range(CANDIDATES)]
            new_mean, new_std = cem_update(np.array(samples), scores, ELITES, flatten(mean[RACE]), flatten(std[RACE]), floor)
            mean[RACE], std[RACE] = unflatten(new_mean), unflatten(new_std)
            iteration += 1
            state_path.write_text(json.dumps(dict(iteration=iteration, mean=new_mean.tolist(), std=new_std.tolist()))+'\n')
            (OUT/f'mean-offsets-i{iteration}.json').write_text(json.dumps(as_json(mean), indent=1)+'\n')
            print(json.dumps(dict(iteration=iteration, control_wins=wins[0], wins=wins, total=sum(wins),
                                  games=len(results), best_fitness=float(scores.max()))), flush=True)
    finally:
        done.set()


if __name__ == '__main__':
    main()
