"""Label-only human outcome timing and conditional prediction decoding."""

import numpy as np


def first_delays(outcomes, loop, horizon_loops):
    delays = {}
    for time, name in outcomes:
        if loop <= time < loop + horizon_loops:
            delays[name] = min(delays.get(name, horizon_loops), time - loop)
    return delays


def conditional_times(presence, time_mass, horizon_seconds):
    """Decode E[time*presence]/P(presence); zero support stays explicitly unknown."""
    presence, time_mass = np.broadcast_arrays(presence, time_mass)
    if (not np.isfinite(presence).all() or not np.isfinite(time_mass).all()
            or (presence < 0).any() or (presence > 1).any()
            or (time_mass < 0).any() or (time_mass > presence + 1e-12).any()):
        raise ValueError('Expected probabilities and bounded normalized time mass')
    known = presence > 0
    seconds = np.divide(time_mass, presence, out=np.zeros_like(time_mass, dtype=float),
                        where=known) * horizon_seconds
    return seconds, known
