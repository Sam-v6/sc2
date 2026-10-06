"""Add genuine quiet replay frames without replacing any issued-command example."""

import argparse
import gzip
import json
from pathlib import Path
import shutil
from src.runner import positive


def occupancy_rows(states, events, stride, unresolved_loops):
    # Preserve exact command-time observations. Regular quiet samples near any
    # issued event (including unresolved events) are excluded, not relabelled WAIT.
    events = list(events)
    blocked = sorted({r["action_loop"] for r in events} | set(unresolved_loops))
    quiet = []
    previous = -1
    for state in states:
        loop = state["game_loop"]
        if loop <= previous or loop % stride:
            raise ValueError("Quiet observations must have an increasing stride clock")
        previous = loop
        issued = loop + 1
        if not any(abs(t - issued) <= stride for t in blocked):
            quiet.append(
                {
                    "observation": state,
                    "action_loop": issued,
                    "commands": [],
                    "next_action_delay": None,
                }
            )
    yield from sorted(events + quiet, key=lambda r: r["action_loop"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issued", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=positive, default=240)
    parser.add_argument("--stride", type=positive, default=4)
    args = parser.parse_args()
    source = json.loads((args.issued / "dataset.json").read_text())
    dense = json.loads((args.observations / "dataset.json").read_text())
    limit = int(args.seconds * 22.4)
    if (
        source["status"] != "completed"
        or dense["sha256"] != source["sha256"]
        or dense["player"] != source["player"]
        or dense["disable_fog"]
        or dense.get("observation_stride") != args.stride
        or dense["last_loop"] < limit
    ):
        raise ValueError(
            "Require matching fog-safe observations covering the entire prefix"
        )
    with gzip.open(args.issued / "examples.jsonl.gz", "rt") as stream:
        events = [r for r in map(json.loads, stream) if r["action_loop"] <= limit]
    with gzip.open(args.observations / "observations.jsonl.gz", "rt") as stream:
        states = [s for s in map(json.loads, stream) if s["game_loop"] < limit]
    if [s["game_loop"] for s in states] != list(range(0, limit, args.stride)):
        raise ValueError("Quiet observation coverage has missing or duplicate frames")
    unresolved = [
        r["event"]["_gameloop"]
        for r in source["issued_command_audit"]["unresolved_events"]
    ]
    rows = list(occupancy_rows(states, events, args.stride, unresolved))
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(args.observations / "static.json", args.output / "static.json")
    with gzip.open(args.output / "examples.jsonl.gz", "wt") as stream:
        for row in rows:
            stream.write(json.dumps(row, separators=(",", ":")) + "\n")
    source.update(
        status="completed",
        rows=len(rows),
        prefix_seconds=args.seconds,
        source_dataset=str(args.issued.resolve()),
        examples=str((args.output / "examples.jsonl.gz").resolve()),
        dataset_scope="completed prefix from a terminal whole-game replay",
        observation_sampling="exact command states plus stride quiet states excluding event neighborhoods",
        observation_stride=args.stride,
        quiet_examples=sum(not r["commands"] for r in rows),
        command_examples=sum(len(r["commands"]) for r in rows),
        observations_dataset=str(args.observations.resolve()),
    )
    (args.output / "dataset.json").write_text(json.dumps(source, indent=2) + "\n")
    print(
        json.dumps(
            {k: source[k] for k in ["rows", "quiet_examples", "command_examples"]}
        )
    )


if __name__ == "__main__":
    main()
