"""Strategy-head examples from scripted primitive traces."""
import gzip
import json

import numpy as np

from src.bots.terran_primitives import scripted_attack
from src.learning.strategy_policy import HEADS, encode_targets, strategy_features


def trace_examples(path, enemy_race, types):
    """Features and choice labels at each macro frame of one scripted game.

    Attack labels are recomputed with ``scripted_attack`` over consecutive macro
    frames; the live bot evaluates it every step, so this is an approximation.
    """
    xs, ys, attacking = [], {head: [] for head in HEADS}, False
    with gzip.open(path, 'rt') as f:
        for line in f:
            frame = json.loads(line)
            if not frame.get('observation'):
                continue
            state = frame['observation']
            xs.append(strategy_features(state, attacking, enemy_race, types))
            attacking = scripted_attack(state, attacking)
            for head, index in encode_targets(frame['targets'], attacking).items():
                ys[head].append(index)
    return np.stack(xs), {head: np.asarray(v, dtype=np.int64) for head, v in ys.items()}
