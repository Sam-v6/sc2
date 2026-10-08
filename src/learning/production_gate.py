"""Timing-only targets for complete native human replay reconstruction."""

from bisect import bisect_right

from src.learning.production_decisions import DECISION_LOOPS


def native_gate_windows(observation_loops, production_keys, unknown_keys, source_end):
    """Label original human issuance in (L,L+44] from current native state L.

    Callers must prove consecutive native extraction through source_end and
    classify every original human command. Unknowns can hide production. A known
    production proves a positive despite unknowns; waiting requires a complete,
    resolved horizon. Event keys are label provenance, never observation fields.
    This does not predict first-command identity or count engine manager repeats.
    """
    loops = list(map(int, observation_loops))
    production = list(map(tuple, production_keys))
    unknown = list(map(tuple, unknown_keys))
    if any(b - a != DECISION_LOOPS for a, b in zip(loops, loops[1:])):
        raise ValueError("Require actual snapshots at the fixed native cadence")
    for keys in (production, unknown):
        if any(a >= b for a, b in zip(keys, keys[1:])):
            raise ValueError("Require strictly increasing source event keys")
        if any(key[0] < 0 or key[0] > source_end for key in keys):
            raise ValueError("Source event falls outside the reconstructed replay")
    if source_end < 0 or any(loop < 0 or loop > source_end for loop in loops):
        raise ValueError("Observation falls outside the reconstructed replay")
    if set(production).intersection(unknown):
        raise ValueError("Production cannot also be unknown")
    labels = []
    for loop in loops:
        end = loop + DECISION_LOOPS
        future = []
        for keys in (production, unknown):
            # Infinite sequence includes every event at a boundary loop.
            start = bisect_right(keys, (loop, float("inf")))
            stop = bisect_right(keys, (end, float("inf")))
            future.append([list(key) for key in keys[start:stop]])
        positive, uncertain = future
        act = True if positive else None if uncertain or end > source_end else False
        labels.append(
            dict(
                loop=loop,
                act=act,
                production_keys=positive,
                unknown_keys=uncertain,
            )
        )
    return labels
