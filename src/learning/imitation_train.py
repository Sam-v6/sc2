"""Fit and evaluate imitation using disjoint whole-game replay datasets."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from src.learning.imitation import FactorPolicy, unit_features, action_labels, DELAYS
from src.learning.global_imitation import global_features, global_labels
from src.runner import positive


def dataset(
    paths, unit_types, seed, decision_level="unit", abilities=None, prefix_seconds=None
):
    rng = np.random.default_rng(seed)
    features = []
    labels = []
    points = []
    sources = []
    weights = []
    audit = {"missing_actors": 0, "missing_targets": 0, "own_memory_selectors": 0}
    audit["replay_ranges"] = []
    for directory in paths:
        beginning = len(features)
        receipt = json.loads((directory / "dataset.json").read_text())
        if receipt["status"] != "completed":
            raise ValueError("Use terminal whole-game datasets for this experiment")
        sources.append(
            {
                "dataset": str(directory.resolve()),
                "replay_sha256": receipt["sha256"],
                "source": receipt["source"],
                "teacher_kind": receipt["teacher_kind"],
            }
        )
        size = json.loads((directory / "static.json").read_text())["game_info"][
            "start_raw"
        ]["map_size"]
        owned_memory = {}
        history = []
        with gzip.open(directory / "examples.jsonl.gz", "rt") as stream:
            for line in stream:
                row = json.loads(line)
                if (
                    prefix_seconds is not None
                    and row["action_loop"] > prefix_seconds * 22.4
                ):
                    break
                state = dict(
                    row["observation"],
                    recent_commands=history[-32:],
                    map_size=[size["x"], size["y"]],
                )
                own = {u["tag"]: u for u in state["units"] if u["alliance"] == 1}
                # Older additive schemas lack owned_memory. Retain only information
                # from earlier player-visible frames, never tracker/future state.
                for tag, unit in own.items():
                    owned_memory[tag] = {
                        "tag": tag,
                        "unit_type": unit["unit_type"],
                        "alliance": 1,
                        "position": unit["position"],
                        "last_seen_loop": state["game_loop"],
                        "observed": False,
                    }
                memory = (
                    {u["tag"]: u for u in state["owned_memory"]}
                    if "owned_memory" in state
                    else owned_memory
                )
                known_own = {**memory, **own}
                if decision_level == "global":
                    state = dict(
                        state,
                        owned_memory=[
                            unit for tag, unit in known_own.items() if tag not in own
                        ],
                    )
                    feature, origin = global_features(
                        state, unit_types, abilities, canonical=True, summarize=True
                    )
                    for command in row["commands"]:
                        absent = set(command["units"]) - known_own.keys()
                        if absent:
                            audit["missing_actors"] += len(absent)
                            continue
                        audit["own_memory_selectors"] += len(
                            set(command["units"]) - own.keys()
                        )
                        target, point = global_labels(
                            command,
                            state,
                            unit_types,
                            origin,
                            row.get("next_action_delay"),
                            canonical=True,
                        )
                        if target["mode"] == 2 and target["target_type"] == -1:
                            audit["missing_targets"] += 1
                        features.append(feature)
                        labels.append(target)
                        points.append(point)
                        weights.append(1.0)
                    history.extend(
                        dict(command, game_loop=row["action_loop"])
                        for command in row["commands"]
                    )
                    continue
                selected = set()
                for command in row["commands"]:
                    for tag in command["units"]:
                        if tag not in known_own:
                            audit["missing_actors"] += 1
                            continue
                        actor = known_own[tag]
                        selected.add(tag)
                        if tag not in own:
                            audit["own_memory_selectors"] += 1
                        target, point = action_labels(
                            command,
                            state,
                            actor,
                            unit_types,
                            row.get("next_action_delay"),
                        )
                        if target["mode"] == 2 and target["target_type"] == -1:
                            audit["missing_targets"] += 1
                        features.append(unit_features(state, actor, unit_types))
                        labels.append(target)
                        points.append(point)
                        weights.append(1 / len(command["units"]))
                others = [u for tag, u in own.items() if tag not in selected]
                for index in rng.choice(
                    len(others), size=min(2, len(others)), replace=False
                ):
                    actor = others[int(index)]
                    target, point = action_labels(None, state, actor, unit_types, None)
                    features.append(unit_features(state, actor, unit_types))
                    labels.append(target)
                    points.append(point)
                    weights.append(1 / min(2, len(others)))
                history.extend(
                    dict(command, game_loop=row["action_loop"])
                    for command in row["commands"]
                )
        audit["replay_ranges"].append((beginning, len(features)))
    if audit["missing_actors"]:
        raise ValueError(f"Dataset controlled-unit alignment failed: {audit}")
    return (
        np.stack(features),
        {name: np.asarray([row[name] for row in labels]) for name in labels[0]},
        np.stack(points),
        np.asarray(weights),
        sources,
        audit,
    )


def equal_replay_weights(weights, ranges):
    result = np.asarray(weights).copy()
    mass = result.sum() / len(ranges)
    for begin, end in ranges:
        if end <= begin:
            raise ValueError("Replay curriculum contains no examples")
        result[begin:end] *= mass / result[begin:end].sum()
    return result


def balance_abilities(abilities, weights):
    counts = np.bincount(abilities, weights=weights)
    balanced = weights / np.sqrt(counts[abilities])
    return balanced * weights.sum() / balanced.sum()


def metrics(policy, x, y, points):
    correct = {name: 0 for name in policy.sizes}
    total = {name: 0 for name in policy.sizes}
    ability_correct = ability_total = 0
    point_error = point_total = 0.0
    loss = 0.0
    for start in range(0, len(x), 128):
        end = min(start + 128, len(x))
        batch = {k: v[start:end] for k, v in y.items()}
        output = policy.predict(x[start:end])
        loss += policy.loss(x[start:end], batch, points[start:end]) * (end - start)
        for name in policy.sizes:
            valid = batch[name] >= 0
            total[name] += int(valid.sum())
            correct[name] += int(
                ((output[name].argmax(axis=1) == batch[name]) & valid).sum()
            )
        commanded = batch["ability"] > 0
        ability_total += int(commanded.sum())
        ability_correct += int(
            ((output["ability"].argmax(axis=1) == batch["ability"]) & commanded).sum()
        )
        targeted = batch["point_valid"].astype(bool)
        point_error += (
            float(
                np.linalg.norm(
                    output["point"][targeted, :2] - points[start:end][targeted, :2],
                    axis=1,
                ).sum()
            )
            * 128
        )
        point_total += int(targeted.sum())
    return {
        "examples": len(x),
        "loss": loss / len(x),
        "head_accuracy": {
            k: correct[k] / total[k] if total[k] else None for k in correct
        },
        "commanded_ability_accuracy": ability_correct / max(ability_total, 1),
        "target_mean_error_tiles": point_error / max(point_total, 1),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", nargs="+", type=Path, required=True)
    parser.add_argument("--validation", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=positive, default=30)
    parser.add_argument("--seed", type=int, default=4000)
    parser.add_argument("--decision-level", choices=["unit", "global"], default="unit")
    parser.add_argument(
        "--balance-abilities",
        action="store_true",
        help="Weight rare teacher commands using training-only inverse square-root frequency",
    )
    parser.add_argument(
        "--prefix-seconds",
        type=positive,
        help="Bounded opening curriculum, preserving all issued commands and equal total weight per replay",
    )
    args = parser.parse_args()
    if args.prefix_seconds and args.decision_level != "global":
        parser.error("Prefix curriculum currently requires global command decisions")
    args.output.mkdir(parents=True, exist_ok=False)
    static = json.loads((args.train[0] / "static.json").read_text())["game_data"]
    unit_types = sorted({u["unit_id"] for u in static["units"]})
    abilities = max(a["ability_id"] for a in static["abilities"]) + 1
    train_x, train_y, train_points, train_weights, train_sources, train_audit = dataset(
        args.train,
        unit_types,
        args.seed,
        args.decision_level,
        abilities,
        args.prefix_seconds,
    )
    valid_x, valid_y, valid_points, valid_weights, valid_sources, valid_audit = dataset(
        args.validation,
        unit_types,
        args.seed + 1,
        args.decision_level,
        abilities,
        args.prefix_seconds,
    )
    if {s["replay_sha256"] for s in train_sources} & {
        s["replay_sha256"] for s in valid_sources
    }:
        raise ValueError("Replay appears in training and validation")
    if args.balance_abilities:
        train_weights = balance_abilities(train_y["ability"], train_weights)
    if args.prefix_seconds:
        train_weights = equal_replay_weights(
            train_weights, train_audit["replay_ranges"]
        )
    policy = FactorPolicy(
        train_x.shape[1],
        abilities,
        unit_types,
        args.seed,
        extra_sizes={"actor_type": len(unit_types) + 1}
        if args.decision_level == "global"
        else None,
        point_dimensions=5 if args.decision_level == "global" else 2,
        autoregressive=args.decision_level == "global",
    )
    policy.feature_mean = train_x.mean(axis=0)
    policy.feature_scale = np.maximum(train_x.std(axis=0), 0.1)
    for name, size in policy.sizes.items():
        counts = np.bincount(
            train_y[name][train_y[name] >= 0],
            weights=train_weights[train_y[name] >= 0],
            minlength=size,
        )
        policy.parameters[name + "_bias"][:] = np.log(counts + 0.1)
    start = time.monotonic()
    rng = np.random.default_rng(args.seed)
    evidence = {
        "train_sources": train_sources,
        "validation_sources": valid_sources,
        "professional_corpus": False,
        "train_audit": train_audit,
        "validation_audit": valid_audit,
        "negative_units_per_command_frame": 0 if args.decision_level == "global" else 2,
        "group_weighting": "one total weight per raw command"
        if args.decision_level == "global"
        else "one total weight per raw command; one total weight per negative group",
        "prefix_seconds": args.prefix_seconds,
        "replay_weighting": "equal total weight per replay"
        if args.prefix_seconds
        else "per command",
        "ability_balancing": "inverse_sqrt_training_frequency"
        if args.balance_abilities
        else "none",
        "split": "whole_replay_sha256",
        "seed": args.seed,
        "algorithm": "factorized_entity_behavior_cloning",
        "decision_level": args.decision_level,
        "entity_encoder": "per_type_spatial_orders"
        if args.decision_level == "global"
        else "unit_context",
        "coordinate_frame": "base_toward_map_center"
        if args.decision_level == "global"
        else "absolute",
        "normalization": "training-only feature mean/std, minimum std .1",
        "spatial_loss": "Huber delta .05 in 128-tile units, weight 100; group count MSE",
        "head_priors": "training-only class counts plus .1 smoothing; all engine abilities retained",
        "limitations": "initial entity/context baseline; no recurrent encoder or map-grid model; missing unit targets mask target-type/alliance and target-coordinate losses",
    }
    before = metrics(policy, valid_x, valid_y, valid_points)
    for epoch in range(args.epochs):
        order = rng.permutation(len(train_x))
        losses = []
        for start_index in range(0, len(order), 128):
            index = order[start_index : start_index + 128]
            losses.append(
                policy.learn(
                    train_x[index],
                    {k: v[index] for k, v in train_y.items()},
                    train_points[index],
                    weights=train_weights[index],
                )
            )
        row = {
            "epoch": epoch,
            "training_loss": float(np.mean(losses)),
            "wall_seconds": round(time.monotonic() - start, 3),
        }
        with (args.output / "training.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        print(json.dumps(row), flush=True)
    report = dict(
        evidence,
        status="completed",
        epochs=args.epochs,
        updates=policy.updates,
        training=metrics(policy, train_x, train_y, train_points),
        validation_before=before,
        validation=metrics(policy, valid_x, valid_y, valid_points),
        wall_seconds=round(time.monotonic() - start, 3),
    )
    if args.prefix_seconds:
        production = {
            a["ability_id"]
            for a in static["abilities"]
            if a.get("friendly_name", "").startswith("Train ")
        }
        report["prefix_diagnostics"] = []
        for source, (begin, end) in zip(train_sources, train_audit["replay_ranges"]):
            x = train_x[begin:end]
            y = {k: v[begin:end] for k, v in train_y.items()}
            output = policy.predict(x)
            predicted = output["ability"].argmax(axis=1)
            errors = np.flatnonzero(predicted != y["ability"])
            selected = np.isin(y["ability"], list(production))
            joint = np.ones(len(x), dtype=bool)
            for name in policy.sizes:
                joint &= (y[name] < 0) | (output[name].argmax(axis=1) == y[name])
            timing = y["delay"] >= 0
            report["prefix_diagnostics"].append(
                dict(
                    source,
                    first_label=int(y["ability"][0]),
                    first_prediction=int(predicted[0]),
                    first_prediction_error_index=int(errors[0])
                    if len(errors)
                    else None,
                    production_recall=float(
                        (predicted[selected] == y["ability"][selected]).mean()
                    )
                    if selected.any()
                    else None,
                    joint_discrete_argument_accuracy=float(joint.mean()),
                    timing_mean_error_loops=float(
                        abs(
                            DELAYS[output["delay"].argmax(axis=1)[timing]]
                            - DELAYS[y["delay"][timing]]
                        ).mean()
                    )
                    if timing.any()
                    else None,
                )
            )
    policy.save(args.output / "policy.npz", report)
    report["checkpoint_sha256"] = hashlib.sha256(
        (args.output / "policy.npz").read_bytes()
    ).hexdigest()
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
