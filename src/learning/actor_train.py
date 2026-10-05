"""Teach individual actor membership using a frozen macro representation."""

import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from src.learning.actor_selection import actor_features, select_actors
from src.learning.global_imitation import global_features
from src.learning.imitation import FactorPolicy
from src.runner import positive
from src.learning.teacher_states import teacher_states, own_actors


def collect(directories, macro, seconds):
    features = []
    labels = []
    weights = []
    groups = []
    sources = []
    for directory in directories:
        receipt = json.loads((directory / "dataset.json").read_text())
        if receipt["status"] != "completed":
            raise ValueError("Actor teaching requires terminal reconstruction")
        sources.append(
            {"sha256": receipt["sha256"], "dataset": str(directory.resolve())}
        )
        for row, state in teacher_states(directory, seconds):
            actors = own_actors(state)
            x, origin = global_features(
                state,
                macro.unit_types,
                macro.sizes["ability"],
                canonical=True,
                summarize=True,
            )
            for command in row["commands"]:
                selected = set(command["units"])
                known = {u["tag"] for u in actors}
                if not selected <= known:
                    raise ValueError("Unknown actor teaching label")
                context = macro.command_context(x, command["ability"])
                begin = len(features)
                negative = len(actors) - len(selected)
                for index, unit in enumerate(actors):
                    positive_label = unit["tag"] in selected
                    features.append(
                        actor_features(
                            state,
                            unit,
                            index,
                            macro.unit_types,
                            macro.sizes["ability"],
                            origin,
                            context,
                        )
                    )
                    labels.append(int(positive_label))
                    weights.append(
                        1 / len(selected) if positive_label else 1 / max(negative, 1)
                    )
                groups.append(
                    {
                        "begin": begin,
                        "end": len(features),
                        "loop": row["action_loop"],
                        "ability": command["ability"],
                        "actors": actors,
                        "selected": sorted(selected),
                        "dataset": str(directory),
                    }
                )
    return np.stack(features), np.asarray(labels), np.asarray(weights), groups, sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--macro", type=Path, required=True)
    parser.add_argument("--datasets", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=positive, default=120)
    parser.add_argument("--epochs", type=positive, default=250)
    args = parser.parse_args()
    macro = FactorPolicy.load(args.macro)
    if macro.evidence.get("entity_encoder") != "per_type_spatial_orders":
        raise ValueError("Use the spatial macro checkpoint for this actor fit")
    args.output.mkdir(parents=True, exist_ok=False)
    x, y, weights, groups, sources = collect(args.datasets, macro, args.seconds)
    policy = FactorPolicy(x.shape[1], 2, [], seed=5000)
    policy.feature_mean = x.mean(axis=0)
    policy.feature_scale = np.maximum(x.std(axis=0), 0.1)
    labels = {name: np.full(len(x), -1, dtype=int) for name in policy.sizes}
    labels["ability"] = y
    labels["point_valid"] = np.zeros(len(x), dtype=int)
    points = np.full((len(x), 2), np.nan, dtype=np.float32)
    rng = np.random.default_rng(5000)
    start = time.monotonic()
    for epoch in range(args.epochs):
        order = rng.permutation(len(x))
        for begin in range(0, len(x), 128):
            index = order[begin : begin + 128]
            policy.learn(
                x[index],
                {k: v[index] for k, v in labels.items()},
                points[index],
                weights=weights[index],
            )
    logits = policy.predict(x)["ability"]
    failures = []
    matched = 0
    for group in groups:
        available = {u["tag"]: {group["ability"]} for u in group["actors"]}
        selected = sorted(
            u["tag"]
            for u in select_actors(
                group["actors"],
                logits[group["begin"] : group["end"]],
                available,
                group["ability"],
            )
        )
        if selected == group["selected"]:
            matched += 1
        else:
            failures.append(
                {
                    k: v
                    for k, v in dict(group, predicted=selected).items()
                    if k != "actors"
                }
            )
    report = {
        "status": "completed",
        "role": "actor_selection",
        "scope": "initial supervised pointer fit; frozen macro context; no strength claim",
        "macro_sha256": hashlib.sha256(args.macro.read_bytes()).hexdigest(),
        "feature_unit_types": macro.unit_types,
        "macro_abilities": macro.sizes["ability"],
        "sources": sources,
        "seconds": args.seconds,
        "epochs": args.epochs,
        "weighting": "equal positive and negative total weight per human command",
        "entity_examples": len(x),
        "command_groups": len(groups),
        "exact_group_matches": matched,
        "failures": failures,
        "positive_recall": float((logits[y == 1, 1] > logits[y == 1, 0]).mean()),
        "negative_recall": float((logits[y == 0, 0] >= logits[y == 0, 1]).mean()),
        "wall_seconds": round(time.monotonic() - start, 3),
    }
    policy.save(args.output / "actors.npz", report)
    report["checkpoint_sha256"] = hashlib.sha256(
        (args.output / "actors.npz").read_bytes()
    ).hexdigest()
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k not in ("feature_unit_types", "failures")
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
