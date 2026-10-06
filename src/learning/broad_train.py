"""Bounded broad-ability PPO experiment with frozen human unit/target models."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from src.learning.broad_rl import ResidualPPO
from src.learning.imitation import FactorPolicy
from src.learning.imitation_play import play_job
from src.runner import positive
from src.runtime import supervise

COLUMNS = ("states", "priors", "masks", "actions", "log_probs", "advantages", "returns")
RACES = ("Terran", "Protoss", "Zerg")


def checked_rollout(path, policy, snapshot_sha):
    with np.load(path, allow_pickle=False) as data:
        metadata = json.loads(str(data["metadata"]))
        if (
            metadata["base_sha256"] != policy.base_sha256
            or metadata["residual_sha256"] != snapshot_sha
            or metadata["sampling"] != "mixture"
            or metadata["epsilon"] != policy.epsilon
        ):
            raise ValueError("Rollout does not match the frozen sampling policy")
        arrays = [data[k].copy() for k in COLUMNS]
    x, prior, mask, actions, old, adv, returns = arrays
    n = len(x)
    f, k = policy.parameters["actor"].shape
    if (
        not n
        or x.shape != (n, f)
        or prior.shape != (n, k)
        or mask.shape != (n, k)
        or mask.dtype != np.bool_
        or any(not np.isfinite(a).all() for a in arrays)
        or not mask.any(axis=1).all()
        or actions.shape != (n,)
        or not np.issubdtype(actions.dtype, np.integer)
        or np.any(actions < 0)
        or np.any(actions >= k)
        or any(a.shape != (n,) for a in (old, adv, returns))
        or not mask[np.arange(n), actions].all()
    ):
        raise ValueError("Invalid native PPO rollout")
    for start in range(0, n, 128):
        end = min(start + 128, n)
        q, _, values = policy.distribution(
            x[start:end], prior[start:end], mask[start:end]
        )
        observed = np.log(q[np.arange(end - start), actions[start:end]])
        if not np.allclose(
            observed, old[start:end], rtol=0, atol=1e-8
        ) or not np.allclose(
            values, returns[start:end] - adv[start:end], rtol=0, atol=1e-8
        ):
            raise ValueError("Native mixture likelihood/value replay mismatch")
    return arrays


def evaluate(job):
    return supervise(play_job, (job,), job["wall_seconds"])


def outcome(receipt):
    return {"Victory": 1, "Defeat": -1, "Tie": 0}[receipt["result"]]


def combat_return(receipt):
    return receipt["score"]["killed_value"] / 100 + 100 * outcome(receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "policy",
        "actor-policy",
        "argument-policy",
        "spatial-policy",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--episodes", type=positive, default=24)
    parser.add_argument("--seconds", type=positive, default=600)
    parser.add_argument("--workers", type=positive, default=3)
    parser.add_argument("--wall-seconds", type=positive, default=240)
    parser.add_argument("--seed", type=int, default=40200)
    args = parser.parse_args()
    if args.episodes % 3 or args.workers > 4:
        parser.error("Use whole three-race batches and at most four workers")
    macro = FactorPolicy.load(args.policy)
    base_sha = hashlib.sha256(args.policy.read_bytes()).hexdigest()
    args.output.mkdir(parents=True, exist_ok=False)
    policy = ResidualPPO(32, macro.sizes["ability"], base_sha)
    zero = args.output / "zero.npz"
    policy.save(zero)
    common = {
        name: str(getattr(args, name).resolve())
        for name in ("policy", "actor_policy", "argument_policy", "spatial_policy")
    }
    common.update(
        difficulty="VeryEasy",
        build="RandomBuild",
        map="Simple64",
        seconds=args.seconds,
        step=4,
        initial_harvest=False,
        idle_worker_harvest=True,
        wait_unavailable=False,
        fixed_cadence=True,
        wall_seconds=args.wall_seconds,
    )
    contract = {
        "scope": "bounded ability-only RL bridge; frozen human unit/target/spatial models; no professional/Hard acceptance",
        "episodes": args.episodes,
        "seconds": args.seconds,
        "workers": args.workers,
        "epsilon": policy.epsilon,
        "reward": "incremental killed-resource value /100 +100 victory -100 defeat; timeout 0",
        "gate": "six fresh paired cases must increase native wins AND ordinary combat return; no automatic extension",
        "components": {
            key: hashlib.sha256(Path(value).read_bytes()).hexdigest()
            for key, value in common.items()
            if key.endswith("policy")
        },
        "seed": args.seed,
        "finite_horizon": True,
    }
    (args.output / "contract.json").write_text(json.dumps(contract, indent=2) + "\n")
    started = time.monotonic()
    training = []
    for batch in range(args.episodes // 3):
        snapshot = args.output / f"batch-{batch:02d}.npz"
        policy.save(snapshot)
        sha = hashlib.sha256(snapshot.read_bytes()).hexdigest()
        jobs = [
            dict(
                common,
                residual_policy=str(snapshot.resolve()),
                sample=True,
                race=race,
                seed=args.seed + batch * 3 + i,
                output=str((args.output / f"train-{batch:02d}-{race}").resolve()),
            )
            for i, race in enumerate(RACES)
        ]
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            receipts = list(pool.map(evaluate, jobs))
        (args.output / f"batch-{batch:02d}-receipts.json").write_text(
            json.dumps(receipts, indent=2) + "\n"
        )
        if any(r["status"] not in ("completed", "truncated") for r in receipts):
            raise RuntimeError(
                "Native RL worker failed; no learning update or synthetic return"
            )
        columns = [
            checked_rollout(Path(j["output"]) / "rollout.npz", policy, sha)
            for j in jobs
        ]
        arrays = [
            np.concatenate([row[i] for row in columns]) for i in range(len(COLUMNS))
        ]
        update = policy.update(arrays, args.seed + batch)
        training.extend(receipts)
        policy.save(args.output / "latest.npz")
        record = dict(
            batch=batch,
            **update,
            returns=[combat_return(r) for r in receipts],
            results=[r["result"] for r in receipts],
            wall_seconds=time.monotonic() - started,
        )
        with (args.output / "training.jsonl").open("a") as stream:
            stream.write(json.dumps(record) + "\n")
        print(json.dumps(record), flush=True)
    final = args.output / "latest.npz"
    jobs = []
    for i in range(6):
        for arm, checkpoint in [("zero", zero), ("trained", final)]:
            jobs.append(
                dict(
                    common,
                    residual_policy=str(checkpoint.resolve()),
                    sample=False,
                    race=RACES[i % 3],
                    seed=args.seed + 1000 + i,
                    output=str((args.output / f"eval-{i:02d}-{arm}").resolve()),
                )
            )
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        receipts = list(pool.map(evaluate, jobs))
    (args.output / "evaluation.json").write_text(json.dumps(receipts, indent=2) + "\n")
    if any(r["status"] not in ("completed", "truncated") for r in receipts):
        raise RuntimeError("Evaluation worker failed; comparison is invalid")
    control, trained = receipts[::2], receipts[1::2]
    outcome_delta = float(
        np.mean([outcome(b) - outcome(a) for a, b in zip(control, trained)])
    )
    return_delta = float(
        np.mean([combat_return(b) - combat_return(a) for a, b in zip(control, trained)])
    )
    report = dict(
        contract,
        status="completed",
        updates=policy.updates,
        training_games=len(training),
        zero_wins=sum(r["result"] == "Victory" for r in control),
        trained_wins=sum(r["result"] == "Victory" for r in trained),
        mean_outcome_delta=outcome_delta,
        mean_combat_return_delta=return_delta,
        bounded_gate_passed=sum(r["result"] == "Victory" for r in trained)
        > sum(r["result"] == "Victory" for r in control)
        and return_delta > 0,
        hard_acceptance=False,
        wall_seconds=time.monotonic() - started,
    )
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
