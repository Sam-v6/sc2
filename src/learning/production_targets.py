"""Future human production labels; never add future information to observations."""

from bisect import bisect_left, bisect_right


def production_targets(rows, production_abilities, unresolved_keys):
    """Label the next retained production event, censoring intervening unknowns.

    Same-loop command sequence is significant. These are supervision targets,
    not inputs or instructions to execute the future command immediately.
    """
    keys = [(r["action_loop"], r["source_sequence"]) for r in rows]
    if any(left >= right for left, right in zip(keys, keys[1:])):
        raise ValueError("Rows must have strictly increasing event keys")
    if any(len(row["commands"]) != 1 for row in rows):
        raise ValueError("Expected one issued command per retained event")
    unknowns = sorted(set(unresolved_keys))
    if set(keys).intersection(unknowns):
        raise ValueError("An event cannot be both retained and unresolved")
    events = [
        (key, row["commands"][0]["ability"])
        for key, row in zip(keys, rows)
        if row["commands"][0]["ability"] in production_abilities
    ]
    event_keys = [event[0] for event in events]
    targets = []
    for key in keys:
        index = bisect_left(event_keys, key)
        if index == len(events):
            targets.append(None)
            continue
        target_key, ability = events[index]
        unknown_index = bisect_right(unknowns, key)
        if unknown_index < len(unknowns) and unknowns[unknown_index] < target_key:
            targets.append(None)
            continue
        targets.append(
            dict(
                ability=ability,
                delay_loops=target_key[0] - key[0],
                target_key=list(target_key),
            )
        )
    return targets
