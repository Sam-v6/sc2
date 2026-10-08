"""Bounded CPU-only return-driven parameter search in native combat mini-games."""

import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import time
import numpy as np
from src.learning.micro_policy import MicroPolicy, episode_return, update_distribution
from src.learning.sandbox import sandbox_job, MAPS
from src.runner import positive, validate_map
from src.runtime import supervise


def evaluate(job):
    return supervise(sandbox_job, (job,), job.pop("wall_seconds"))


def train(args):
    validate_map(args.map)
    args.output.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(args.seed)
    mean, scale = np.zeros(MicroPolicy.dimension), np.ones(MicroPolicy.dimension)
    best_return, best_weights = -float("inf"), None
    start = time.monotonic()
    evidence = {
        "algorithm": "cross_entropy_policy_search",
        "seed": args.seed,
        "map": args.map,
        "step": args.step,
        "seconds": args.seconds,
        "population": args.population,
        "workers": args.workers,
        "reward": "killed_value + .2 damage_dealt - .5 damage_taken + survival_seconds + 1000 victory",
        "scope": "movement_and_visible_targeting_only",
        "ordinary_game_transfer": False,
    }
    for generation in range(args.generations):
        weights = rng.normal(mean, scale, (args.population, MicroPolicy.dimension))
        if best_weights is not None:
            weights[0] = best_weights
        jobs = []
        for index, row in enumerate(weights):
            directory = args.output / f"g{generation:03d}-p{index:03d}"
            checkpoint = directory.with_suffix(".policy.json")
            MicroPolicy(row).save(checkpoint, evidence)
            jobs.append(
                {
                    "map": args.map,
                    "output": str(directory.resolve()),
                    "seed": args.seed + generation,
                    "seconds": args.seconds,
                    "step": args.step,
                    "policy": str(checkpoint.resolve()),
                    "wall_seconds": args.wall_seconds,
                }
            )
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            receipts = list(pool.map(evaluate, jobs))
        if any(r["status"] not in ("completed", "truncated") for r in receipts):
            (args.output / "failed-batch.json").write_text(
                json.dumps(receipts, indent=2) + "\n"
            )
            raise RuntimeError(
                "Native worker failed; inspect failed-batch.json before continuing"
            )
        returns = np.asarray([episode_return(r) for r in receipts])
        winner = int(np.argmax(returns))
        if returns[winner] > best_return:
            best_return = float(returns[winner])
            best_weights = weights[winner].copy()
            MicroPolicy(best_weights).save(
                args.output / "best.json",
                dict(
                    evidence,
                    generation=generation,
                    development_return=best_return,
                    held_out=False,
                ),
            )
        mean, scale = update_distribution(
            weights, returns, max(2, args.population // 4)
        )
        np.savez(
            args.output / "search-state.npz",
            mean=mean,
            scale=scale,
            best_weights=best_weights,
            rng_state=json.dumps(rng.bit_generator.state),
            next_generation=generation + 1,
        )
        row = {
            "generation": generation,
            "returns": returns.tolist(),
            "mean_return": float(returns.mean()),
            "best_return": best_return,
            "wall_seconds": round(time.monotonic() - start, 3),
        }
        with (args.output / "training.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        print(json.dumps(row), flush=True)
    (args.output / "training.json").write_text(
        json.dumps(
            dict(
                evidence,
                status="completed",
                generations=args.generations,
                episodes=args.generations * args.population,
                best_return=best_return,
                wall_seconds=round(time.monotonic() - start, 3),
            ),
            indent=2,
        )
        + "\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--map", choices=MAPS, default="DefeatRoaches")
    parser.add_argument("--generations", type=positive, default=4)
    parser.add_argument("--population", type=positive, default=12)
    parser.add_argument("--workers", type=positive, default=2)
    parser.add_argument("--seed", type=int, default=2000)
    parser.add_argument("--step", type=positive, default=4)
    parser.add_argument("--seconds", type=positive, default=60)
    parser.add_argument("--wall-seconds", type=positive, default=90)
    args = parser.parse_args()
    if args.population < 4 or args.workers > max(1, int((os.cpu_count() or 1) * 0.8)):
        parser.error("Use population >=4 and workers within the approximate CPU budget")
    if args.output.exists():
        parser.error("Output exists; choose a new experiment directory")
    train(args)


if __name__ == "__main__":
    main()
