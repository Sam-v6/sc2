"""Causal player-state reconstruction shared by supervised command components."""

import gzip
import json


def remember_command(command, state, loop):
    """Keep only actor/target roles known when this command was issued."""
    known = {u["tag"]: u for u in state.get("owned_memory", []) + state["units"]}
    target = known.get(command.get("target_unit"), {})
    return dict(
        command,
        game_loop=loop,
        actor_types=[
            known.get(tag, {}).get("unit_type", 0) for tag in command["units"]
        ],
        target_type=target.get("unit_type", 0),
        target_alliance=target.get("alliance", 0),
        target_position=command.get("target_point") or target.get("position", [])[:2],
    )


def teacher_states(directory, seconds=None):
    static = json.loads((directory / "static.json").read_text())
    size = static["game_info"]["start_raw"]["map_size"]
    memory = {}
    history = []
    with gzip.open(directory / "examples.jsonl.gz", "rt") as stream:
        for row in map(json.loads, stream):
            if seconds is not None and row["action_loop"] > seconds * 22.4:
                break
            state = dict(
                row["observation"],
                recent_commands=history[-32:],
                map_size=[size["x"], size["y"]],
            )
            own = {u["tag"]: u for u in state["units"] if u["alliance"] == 1}
            for tag, unit in own.items():
                memory[tag] = {
                    "tag": tag,
                    "unit_type": unit["unit_type"],
                    "alliance": 1,
                    "position": unit["position"],
                    "last_seen_loop": state["game_loop"],
                    "observed": False,
                }
            # Newer extraction maintains this every engine frame, including
            # deaths. Legacy files permit only conservative last-seen fallback.
            known = (
                {u["tag"]: u for u in state["owned_memory"]}
                if "owned_memory" in state
                else memory
            )
            if "owned_memory" in state:
                memory = {**known, **{tag: memory[tag] for tag in own}}
            state["owned_memory"] = [u for tag, u in known.items() if tag not in own]
            yield row, state
            history.extend(
                remember_command(c, state, row["action_loop"]) for c in row["commands"]
            )


def own_actors(state):
    return sorted(
        (u for u in state["units"] + state["owned_memory"] if u["alliance"] == 1),
        key=lambda u: u["tag"],
    )
