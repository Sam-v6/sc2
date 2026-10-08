"""Causal human event slots, retaining unknown commands and timing gaps."""


def history_rows(events, accepted):
    keys = [(e["_gameloop"], e["m_sequence"]) for e in events]
    if len(set(keys)) != len(keys) or any(a[0] > b[0] for a, b in zip(keys, keys[1:])):
        raise ValueError(
            "Original human events require unique, chronological identities"
        )
    commands = {(r["loop"], r["sequence"]): r["command"] for r in accepted}
    if len(commands) != len(accepted) or not commands.keys() <= set(keys):
        raise ValueError("Accepted command is not uniquely bound to an original event")
    history = []
    for index, key in enumerate(keys):
        command = commands.get(key)
        if command is None:
            history.append(dict(game_loop=key[0], unknown=True))
        else:
            command.to_proto()
            next_key = keys[index + 1] if index + 1 < len(keys) else None
            delay = next_key[0] - key[0] if next_key in commands else None
            yield dict(
                loop=key[0],
                sequence=key[1],
                command=command,
                recent_commands=history[-32:],
                next_action_delay=delay,
            )
            remembered = dict(command.as_dict(), game_loop=key[0], verified=True)
            if command.target_unit is not None:
                point = events[index]["m_data"]["TargetUnit"]["m_snapshotPoint"]
                remembered["target_position"] = [
                    point[axis] / 4096 for axis in ("x", "y")
                ]
            history.append(remembered)
        history = history[-32:]
