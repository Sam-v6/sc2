"""Strategy-head labels from a human player's own future state in a replay.

Count targets are the player's own counts ``horizon`` loops later (what they
actually built toward); attack is whether most army supply is past the midpoint
between the two start locations now.
"""
import math
from bisect import bisect_left
from collections import Counter

COUNTS = dict(workers=(45,), bases=(18, 132, 130, 36, 134), barracks=(21, 46), factories=(27, 43),
              starports=(28, 44), engineering_bays=(22,), refineries=(20,), tanks=(33, 32))
ARMY_SUPPLY = {48: 1, 51: 2, 49: 1, 50: 2, 53: 2, 484: 2, 498: 2, 500: 2, 692: 3, 33: 3, 32: 3,
               52: 6, 691: 6, 35: 2, 34: 2, 54: 2, 689: 3, 734: 3, 56: 2, 55: 3, 57: 6}


def counts(state):
    own = Counter(u['unit_type'] for u in state['units'] if u['alliance'] == 1)
    targets = {head: sum(own[t] for t in types) for head, types in COUNTS.items()}
    targets['gas_workers'] = sum(u.get('assigned_harvesters', 0) for u in state['units']
                                 if u['alliance'] == 1 and u['unit_type'] == 20)
    return targets


def attacking(state, own_start, enemy_start):
    total = midpoint = 0
    span = math.dist(own_start, enemy_start)
    for u in state['units']:
        supply = ARMY_SUPPLY.get(u['unit_type'], 0) if u['alliance'] == 1 else 0
        total += supply
        if supply and math.dist(own_start, u['position'][:2]) > span / 2:
            midpoint += supply
    return total > 0 and midpoint > total / 2


def human_strategy_labels(frames, own_start, enemy_start, horizon):
    loops = [f['game_loop'] for f in frames]
    labels = []
    for f in frames:
        future = frames[min(bisect_left(loops, f['game_loop'] + horizon), len(frames) - 1)]
        labels.append((counts(future), attacking(f, own_start, enemy_start)))
    return labels
