"""Fit and audit a construction candidate scorer using whole-replay splits."""

import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from src.learning.imitation import FactorPolicy
from src.learning.global_imitation import global_features
from src.learning.teacher_states import teacher_states, own_actors
from src.learning.spatial_construction import (
    decode_terrain,
    spatial_candidates,
    candidate_features,
    rank_points,
)
from src.runner import positive


def collect(directories, macro, seconds):
    features, labels, weights, groups, sources = [], [], [], [], []
    for directory in directories:
        receipt = json.loads((directory / "dataset.json").read_text())
        if receipt["status"] != "completed":
            raise ValueError("Spatial teaching requires terminal reconstruction")
        sources.append(receipt["sha256"])
        static = json.loads((directory / "static.json").read_text())
        terrain = decode_terrain(static["terrain"])
        catalog = {a["ability_id"]: a for a in static["game_data"]["abilities"]}
        structures = [
            u["unit_id"]
            for u in static["game_data"]["units"]
            if 8 in u.get("attributes", [])
        ]
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
                descriptor = catalog[command["ability"]]
                if not descriptor.get("is_building") or command["target_point"] is None:
                    continue
                footprint = descriptor["footprint_radius"]
                points = spatial_candidates(state["map_size"], footprint)
                rows = candidate_features(
                    state,
                    [actors[t] for t in command["units"]],
                    origin,
                    macro.command_context(x, command["ability"]),
                    points,
                    terrain,
                    footprint,
                    structures,
                )
                distance = np.linalg.norm(points - command["target_point"], axis=1)
                near = distance <= distance.min() + 2.0
                weight = np.exp(-(distance[near] ** 2 - distance.min() ** 2) / 8.0)
                per_cell = np.full(len(points), 1.0 / (~near).sum())
                per_cell[near] = weight / weight.sum()
                begin = len(labels)
                features.append(rows)
                labels.extend(near.astype(int))
                weights.extend(per_cell)
                groups.append(
                    {
                        "begin": begin,
                        "end": len(labels),
                        "points": points,
                        "target": command["target_point"],
                        "ability": command["ability"],
                    }
                )
    return (
        np.concatenate(features),
        np.asarray(labels),
        np.asarray(weights),
        groups,
        sources,
        structures,
    )


def audit(policy, x, groups):
    errors, coverage, by_ability = [], [], {}
    for group in groups:
        ranked = rank_points(policy, x[group["begin"] : group["end"]], group["points"])
        error = float(np.linalg.norm(np.asarray(ranked[0]) - group["target"]))
        errors.append(error)
        coverage.append(
            float(np.linalg.norm(group["points"] - group["target"], axis=1).min())
        )
        by_ability.setdefault(str(group["ability"]), []).append(error)
    return {
        "commands": len(groups),
        "mean_target_error_tiles": float(np.mean(errors)),
        "mean_grid_coverage_error_tiles": float(np.mean(coverage)),
        "by_ability": {
            k: {"commands": len(v), "mean_error_tiles": float(np.mean(v))}
            for k, v in by_ability.items()
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--macro", type=Path, required=True)
    parser.add_argument("--train", nargs="+", type=Path, required=True)
    parser.add_argument("--validation", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=positive, default=240)
    parser.add_argument("--epochs", type=positive, default=150)
    args = parser.parse_args()
    macro = FactorPolicy.load(args.macro)
    x, y, w, groups, sources, structures = collect(args.train, macro, args.seconds)
    vx, _, _, vg, vs, _ = collect(args.validation, macro, args.seconds)
    if set(sources) & set(vs):
        raise ValueError("Replay overlap between training and validation")
    args.output.mkdir(parents=True, exist_ok=False)
    policy = FactorPolicy(x.shape[1], 2, [], seed=5002)
    policy.feature_mean = x.mean(axis=0)
    policy.feature_scale = np.maximum(x.std(axis=0), 0.1)
    labels = {k: np.full(len(x), -1, dtype=int) for k in policy.sizes}
    labels.update(ability=y, point_valid=np.zeros(len(x), dtype=int))
    points = np.full((len(x), 2), np.nan, dtype=np.float32)
    rng = np.random.default_rng(5002)
    start = time.monotonic()
    for epoch in range(args.epochs):
        order = rng.permutation(len(x))
        for begin in range(0, len(x), 512):
            index = order[begin : begin + 512]
            policy.learn(
                x[index],
                {k: v[index] for k, v in labels.items()},
                points[index],
                weights=w[index],
            )
        if epoch % 25 == 0:
            print(
                json.dumps({"epoch": epoch, "wall_seconds": time.monotonic() - start}),
                flush=True,
            )
    report = {
        "status": "completed",
        "role": "spatial_construction",
        "scope": "conditional human construction locations; no strength claim",
        "macro_sha256": hashlib.sha256(args.macro.read_bytes()).hexdigest(),
        "structure_types": structures,
        "grid_spacing": 4,
        "footprint_alignment": "native footprint fractional part",
        "sources": sources,
        "validation_sources": vs,
        "seconds": args.seconds,
        "epochs": args.epochs,
        "training": audit(policy, x, groups),
        "validation": audit(policy, vx, vg),
        "wall_seconds": round(time.monotonic() - start, 3),
    }
    policy.save(args.output / "spatial.npz", report)
    report["checkpoint_sha256"] = hashlib.sha256(
        (args.output / "spatial.npz").read_bytes()
    ).hexdigest()
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
