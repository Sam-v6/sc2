"""Causal human act/wait targets at real observation times, with no future inputs."""

from bisect import bisect_left

DECISION_LOOPS = 44


def decision_windows(observation_loops, production_events, unknown_keys):
    """Select actual observations at least44loops apart; do not interpolate.

    Events are (loop, sequence, ability). Observation at L precedes that loop's
    command effects. A positive label uses the first event in [L,L+44), provided
    no unknown command precedes it. Wait requires that entire interval be known.
    Source-end and unknown intervals are censored, not labeled as waiting.
    Returned future event keys are label provenance, never sensory features.
    """
    loops = list(map(int, observation_loops))
    keys = [(int(loop), int(sequence)) for loop, sequence, _ in production_events]
    if any(a >= b for a, b in zip(loops, loops[1:])) or any(
        a >= b for a, b in zip(keys, keys[1:])
    ):
        raise ValueError("Require strictly increasing observations and event keys")
    unknowns = sorted(set(map(tuple, unknown_keys)))
    if set(keys).intersection(unknowns):
        raise ValueError("Production cannot also be an unknown event")
    if not loops:
        return []
    windows = []
    next_loop = loops[0]
    for index, loop in enumerate(loops):
        if loop < next_loop:
            continue
        next_loop = loop + DECISION_LOOPS
        end = loop + DECISION_LOOPS
        event_index = bisect_left(keys, (loop, -1))
        event = (
            production_events[event_index]
            if event_index < len(keys) and keys[event_index][0] < end
            else None
        )
        barrier = tuple(event[:2]) if event else (end, -1)
        unknown_index = bisect_left(unknowns, (loop, -1))
        reason = None
        if unknown_index < len(unknowns) and unknowns[unknown_index] < barrier:
            reason = "unknown_event"
        elif event is None and end > loops[-1]:
            reason = "source_end"
        windows.append(
            dict(
                loop=loop,
                observation_index=index,
                act=None if reason else event is not None,
                ability=int(event[2]) if not reason and event else None,
                target_key=list(event[:2]) if not reason and event else None,
                censored=reason,
            )
        )
    return windows
