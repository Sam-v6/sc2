"""Fit command arguments conditioned on the actual human-selected unit group."""

import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from src.learning.actor_selection import group_features
from src.learning.global_imitation import global_features, coordinate_signs
from src.learning.imitation import FactorPolicy, action_labels
from src.learning.imitation_train import equal_replay_weights, metrics
from src.learning.teacher_states import teacher_states, own_actors
from src.runner import positive


def collect(directories, macro, seconds):
    features, labels, points, ranges, sources = [], [], [], [], []
    for directory in directories:
        receipt = json.loads((directory / "dataset.json").read_text())
        if receipt["status"] != "completed":
            raise ValueError("Argument teaching requires terminal reconstruction")
        sources.append(
            {"sha256": receipt["sha256"], "dataset": str(directory.resolve())}
        )
        begin = len(features)
        for row, state in teacher_states(directory, seconds):
            actors = {u["tag"]: u for u in own_actors(state)}
            x, origin = global_features(
                state,
                macro.unit_types,
                macro.sizes["ability"],
                canonical=True,
                summarize=True,
            )
            for command in row["commands"]:
                group = [actors[tag] for tag in command["units"]]
                features.append(
                    group_features(
                        state,
                        group,
                        macro.unit_types,
                        macro.sizes["ability"],
                        origin,
                        macro.command_context(x, command["ability"]),
                    )
                )
                target, point = action_labels(
                    command,
                    state,
                    {"position": origin},
                    macro.unit_types,
                    row.get("next_action_delay"),
                )
                target["ability"] = -1  # This model cannot choose the gameplay ability.
                labels.append(target)
                points.append(point * coordinate_signs(state, origin))
        ranges.append((begin, len(features)))
    return (
        np.stack(features),
        {k: np.asarray([r[k] for r in labels]) for k in labels[0]},
        np.stack(points),
        ranges,
        sources,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--macro", type=Path, required=True)
    parser.add_argument("--datasets", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=positive, default=120)
    parser.add_argument("--epochs", type=positive, default=400)
    args = parser.parse_args()
    macro = FactorPolicy.load(args.macro)
    if macro.evidence.get("entity_encoder") != "per_type_spatial_orders":
        raise ValueError("Use the spatial macro checkpoint for this argument fit")
    args.output.mkdir(parents=True, exist_ok=False)
    x, labels, points, ranges, sources = collect(args.datasets, macro, args.seconds)
    policy = FactorPolicy(x.shape[1], 1, macro.unit_types, seed=5001)
    policy.feature_mean = x.mean(axis=0)
    policy.feature_scale = np.maximum(x.std(axis=0), 0.1)
    weights = equal_replay_weights(np.ones(len(x)), ranges)
    rng = np.random.default_rng(5001)
    start = time.monotonic()
    for _ in range(args.epochs):
        order = rng.permutation(len(x))
        for begin in range(0, len(x), 128):
            index = order[begin : begin + 128]
            policy.learn(
                x[index],
                {k: v[index] for k, v in labels.items()},
                points[index],
                weights=weights[index],
            )
    report = {
        "status": "completed",
        "role": "argument_prediction",
        "scope": "supervised selected-group arguments; frozen macro; no strength claim",
        "macro_sha256": hashlib.sha256(args.macro.read_bytes()).hexdigest(),
        "seconds": args.seconds,
        "epochs": args.epochs,
        "commands": len(x),
        "sources": sources,
        "weighting": "equal total weight per replay",
        "training": metrics(policy, x, labels, points),
        "wall_seconds": round(time.monotonic() - start, 3),
    }
    policy.save(args.output / "arguments.npz", report)
    report["checkpoint_sha256"] = hashlib.sha256(
        (args.output / "arguments.npz").read_bytes()
    ).hexdigest()
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
