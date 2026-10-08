"""Audit engine command repeats against original human command events.

The complete native reconstruction is retained. Only uniquely matched SCmdEvent
commands become decision labels; unresolved events remain explicit audit entries.
"""

import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import shutil

import mpyq
from src.learning.demonstrations import label_timing
from src.learning.replay_extract import load_protocol


def target_matches(command, event):
    # Verified with the saved native fixture's otherwise identical queued and
    # unqueued Move commands (SCmdEvent flags differ by exactly mask 2).
    if command["queue"] != bool(event["m_cmdFlags"] & 2):
        return False
    data = event["m_data"]
    if "None" in data:
        return command["target_point"] is None and command["target_unit"] is None
    if "TargetPoint" in data:
        point = data["TargetPoint"]
        return command["target_point"] is not None and all(
            abs(command["target_point"][i] - point[axis] / 4096.0) < 1e-5
            for i, axis in enumerate(("x", "y"))
        )
    if "TargetUnit" in data:
        return (
            command["target_unit"] is not None
            and (command["target_unit"] & 0xFFFFFFFF) == data["TargetUnit"]["m_tag"]
        )
    return False


def issued_rows(rows, events, user_id):
    by_loop = defaultdict(list)
    for event in events:
        if (
            event["_event"].endswith(".SCmdEvent")
            and event["_userid"]["m_userId"] == user_id
        ):
            by_loop[event["_gameloop"]].append(event)
    selected = []
    audit = {
        "issued_events": sum(map(len, by_loop.values())),
        "matched_issued_commands": 0,
        "excluded_engine_commands": 0,
        "unresolved_events": [],
    }
    for row in rows:
        events = by_loop.pop(row["action_loop"], [])
        commands = row["commands"]
        accepted = []
        if len(events) == len(commands) and all(
            target_matches(c, e) for c, e in zip(commands, events)
        ):
            accepted = commands
        else:
            remaining = list(commands)
            for event in events:
                candidates = [c for c in remaining if target_matches(c, event)]
                if len(candidates) == 1:
                    accepted.append(candidates[0])
                    remaining.remove(candidates[0])
                else:
                    audit["unresolved_events"].append(
                        {"event": event, "candidate_count": len(candidates)}
                    )
        audit["matched_issued_commands"] += len(accepted)
        audit["excluded_engine_commands"] += len(commands) - len(accepted)
        if accepted:
            selected.append(dict(row, commands=accepted))
    for events in by_loop.values():
        audit["unresolved_events"].extend(
            {"event": e, "candidate_count": 0} for e in events
        )
    labeled = list(label_timing(selected))
    unresolved_loops = {item["event"]["_gameloop"] for item in audit["unresolved_events"]}
    audit["masked_timing_rows"] = 0
    for row in labeled:
        gap = row["next_action_delay"]
        if gap is not None and any(
            row["action_loop"] < loop < row["action_loop"] + gap
            for loop in unresolved_loops
        ):
            row["next_action_delay"] = None
            audit["masked_timing_rows"] += 1
    return labeled, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = json.loads((args.dataset / "dataset.json").read_text())
    if (
        hashlib.sha256(Path(receipt["replay"]).read_bytes()).hexdigest()
        != receipt["sha256"]
    ):
        raise ValueError("Replay content differs from extraction receipt")
    archive = mpyq.MPQArchive(receipt["replay"])
    protocol = load_protocol(int(receipt["metadata"]["BaseBuild"][4:]))
    init = protocol.decode_replay_initdata(archive.read_file("replay.initData"))
    player = receipt["player"]["player_info"]["player_id"]
    slots = init["m_syncLobbyState"]["m_lobbyState"]["m_slots"]
    users = [
        s["m_userId"]
        for s in slots
        if s["m_workingSetSlotId"] == player - 1 and s["m_userId"] is not None
    ]
    if len(users) != 1:
        raise ValueError("Cannot uniquely map observed player to replay user")
    events = protocol.decode_replay_game_events(archive.read_file("replay.game.events"))
    with gzip.open(args.dataset / "examples.jsonl.gz", "rt") as stream:
        rows, audit = issued_rows(map(json.loads, stream), events, users[0])
    if not rows:
        raise ValueError("No uniquely aligned human decisions")
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(args.dataset / "static.json", args.output / "static.json")
    with gzip.open(args.output / "examples.jsonl.gz", "wt") as stream:
        for row in rows:
            stream.write(json.dumps(row, separators=(",", ":")) + "\n")
    receipt.update(
        rows=len(rows),
        source_dataset=str(args.dataset.resolve()),
        examples=str((args.output / "examples.jsonl.gz").resolve()),
        command_labels="uniquely aligned human SCmdEvent; engine repeats excluded",
        queue_identity="SCmdEvent flag mask 2; verified native queued-move fixture",
        issued_command_audit=audit,
    )
    (args.output / "dataset.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(audit), flush=True)


if __name__ == "__main__":
    main()
