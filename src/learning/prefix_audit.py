"""Audit short teaching sequences independently of neural prediction accuracy."""

import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import numpy as np
from src.learning.global_imitation import (
    global_features,
    global_labels,
    select_group,
    coordinate_signs,
)
from src.learning.imitation_play import decode_commands
from src.learning.actor_selection import select_actors
from src.runner import positive


def roundtrip(command, state, types, catalog, delay, entity_membership=False):
    _, origin = global_features(state, types, max(catalog) + 1, canonical=True)
    labels, point = global_labels(command, state, types, origin, delay, canonical=True)
    sizes = {
        "ability": max(catalog) + 1,
        "mode": 4,
        "actor_type": len(types) + 1,
        "target_type": len(types) + 1,
        "alliance": 5,
        "queue": 2,
        "delay": 10,
    }
    output = {name: np.zeros((1, size)) for name, size in sizes.items()}
    for name in sizes:
        if labels[name] >= 0:
            output[name][0, labels[name]] = 100.0
    point[:2] *= coordinate_signs(state, origin)
    point[2:4] *= coordinate_signs(state, origin)
    output["point"] = point[None, :]
    own = state["units"] + state["owned_memory"]
    # Synthetic availability deliberately allows every own actor: this is a
    # representation audit, not proof of native legality/execution.
    available = {u["tag"]: {command["ability"]} for u in own if u["alliance"] == 1}
    if entity_membership:
        actors = sorted((u for u in own if u["alliance"] == 1), key=lambda u: u["tag"])
        logits = np.array(
            [[0.0, 100.0 if u["tag"] in command["units"] else -100.0] for u in actors]
        )
        group = select_actors(actors, logits, available, command["ability"])
    else:
        group = select_group(
            state, output, available, command["ability"], types, origin
        )
    if not group:
        return ["units"]
    proxy = dict(group[0], position=[*origin, 0.0])
    output["point"] = output["point"][:, :2]
    decoded, _ = decode_commands(
        state,
        [proxy],
        output,
        {proxy["tag"]: {command["ability"]}},
        catalog,
        types,
        state["map_size"],
        chosen_abilities=[command["ability"]],
    )
    if not decoded:
        return ["decode"]
    actual = decoded[0].as_dict()
    actual["units"] = [u["tag"] for u in group]
    errors = []
    for field in ("ability", "target_unit", "queue", "autocast"):
        if actual[field] != command[field]:
            errors.append(field)
    if set(actual["units"]) != set(command["units"]):
        errors.append("units")
    if (actual["target_point"] is None) != (command["target_point"] is None):
        errors.append("target_point")
    elif command["target_point"] is not None and not np.allclose(
        actual["target_point"], command["target_point"], atol=0.001, rtol=0
    ):
        errors.append("target_point")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", nargs="+", type=Path, required=True)
    parser.add_argument("--seconds", type=positive, default=120)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--entity-membership",
        action="store_true",
        help="Audit full per-entity membership labels instead of coarse actor type/centroid",
    )
    args = parser.parse_args()
    reports = []
    for directory in args.datasets:
        static = json.loads((directory / "static.json").read_text())
        types = sorted(u["unit_id"] for u in static["game_data"]["units"])
        catalog = {a["ability_id"]: a for a in static["game_data"]["abilities"]}
        size = static["game_info"]["start_raw"]["map_size"]
        memory = {}
        counts = Counter()
        examples = 0
        failures = []
        for row in map(json.loads, gzip.open(directory / "examples.jsonl.gz", "rt")):
            if row["action_loop"] > args.seconds * 22.4:
                break
            state = dict(row["observation"], map_size=[size["x"], size["y"]])
            own = {u["tag"]: u for u in state["units"] if u["alliance"] == 1}
            for tag, unit in own.items():
                memory[tag] = dict(unit)
            state["owned_memory"] = [u for tag, u in memory.items() if tag not in own]
            for command in row["commands"]:
                errors = roundtrip(
                    command,
                    state,
                    types,
                    catalog,
                    row.get("next_action_delay"),
                    args.entity_membership,
                )
                examples += 1
                counts.update(errors)
                if errors:
                    failures.append(
                        {
                            "loop": row["action_loop"],
                            "command": command,
                            "errors": errors,
                        }
                    )
        reports.append(
            {
                "dataset": str(directory.resolve()),
                "examples": examples,
                "field_failures": dict(counts),
                "failed_commands": len(failures),
                "failures": failures,
            }
        )
    receipt = {
        "status": "passed"
        if all(r["failed_commands"] == 0 and r["examples"] for r in reports)
        else "failed",
        "scope": "teacher argument roundtrip; synthetic availability; no native execution evidence",
        "seconds": args.seconds,
        "entity_membership": args.entity_membership,
        "replays": reports,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(receipt, stream, indent=2)
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "replays": [
                    {k: v for k, v in r.items() if k != "failures"} for r in reports
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
