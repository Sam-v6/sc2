"""Learned strategy head for the scripted Terran primitives.

The policy replaces only ``scripted_targets`` (minus reactive supply) and
``scripted_attack``; worker, construction, production and combat execution stay
scripted and attributable. Features use own units, the fog-safe enemy memory
and currently visible enemies only.
"""
from collections import Counter
from pathlib import Path

import numpy as np

# Each head is a categorical choice over these values.
HEADS = {
    'workers': tuple(range(12, 81)),
    'bases': tuple(range(1, 6)),
    'barracks': tuple(range(1, 11)),
    'factories': tuple(range(0, 5)),
    'starports': tuple(range(0, 4)),
    'engineering_bays': tuple(range(0, 3)),
    'refineries': tuple(range(0, 9)),
    'gas_workers': tuple(range(0, 25)),
    'tanks': tuple(range(0, 13)),
    'attack': (False, True),
}
OWN_TYPES = (45, 18, 132, 130, 19, 47, 20, 21, 27, 28, 22, 5, 6, 37, 38, 39, 40, 41, 42,
             48, 33, 32, 54, 35)
RACES = ('Terran', 'Zerg', 'Protoss')
WORKERS = (45, 104, 84)
STRUCTURE = 8
RECENT = 22.4 * 60


def strategy_features(state, attacking, enemy_race, types):
    """Fixed-length player-visible summary for strategic decisions."""
    loop = state['game_loop']
    player = state['player']
    own = [u for u in state['units'] if u['alliance'] == 1]
    total = Counter(u['unit_type'] for u in own)
    ready = Counter(u['unit_type'] for u in own if u.get('build_progress', 1) == 1)
    values = [loop / 22.4 / 600, player['minerals'] / 1000, player['vespene'] / 1000,
              player['food_used'] / 200, player['food_cap'] / 200, float(attacking)]
    values += [race == enemy_race for race in RACES]
    values += [np.log1p(ready[t]) for t in OWN_TYPES] + [np.log1p(total[t] - ready[t]) for t in OWN_TYPES]
    values += [total[t] / 50 for t in OWN_TYPES]
    enemy = {'workers': 0., 'structures': 0., 'army_value': 0., 'army_food': 0.,
             'recent_army_value': 0., 'recent_structures': 0.}
    for memory in state.get('memory', []):
        data = types.get(memory['unit_type'], {})
        seen = memory['last_seen_loop']  # None: fog snapshot never directly seen
        recent = seen is not None and loop - seen <= RECENT
        if memory['unit_type'] in WORKERS:
            enemy['workers'] += 1
        elif STRUCTURE in data.get('attributes', ()):
            enemy['structures'] += 1
            enemy['recent_structures'] += recent
        else:
            value = data.get('mineral_cost', 0) + data.get('vespene_cost', 0)
            enemy['army_value'] += value
            enemy['army_food'] += data.get('food_required', 0)
            enemy['recent_army_value'] += value * recent
    visible = [u for u in state['units'] if u['alliance'] == 4 and u.get('display_type', 1) == 1]
    air = sum(1 for u in visible if u.get('is_flying') and types.get(u['unit_type'], {}).get('weapons'))
    values += [np.log1p(enemy['workers']), np.log1p(enemy['structures']), np.log1p(enemy['recent_structures']),
               enemy['army_value'] / 5000, enemy['recent_army_value'] / 5000, enemy['army_food'] / 100,
               np.log1p(len(visible)), np.log1p(air)]
    return np.asarray(values, dtype=np.float32)


def encode_targets(targets, attack):
    """Choice index per head, clipping values outside the head's range."""
    indices = {}
    for head, choices in HEADS.items():
        value = attack if head == 'attack' else targets[head]
        if head != 'attack':
            value = min(max(value, choices[0]), choices[-1])
        indices[head] = choices.index(value)
    return indices


def decode_targets(indices):
    values = {head: HEADS[head][i] for head, i in indices.items()}
    attack = bool(values.pop('attack'))
    return values, attack


class StrategyPolicy:
    """One tanh hidden layer shared by a linear categorical output per head."""

    def __init__(self, params):
        self.params = {k: np.asarray(v, dtype=np.float32) for k, v in params.items()}

    @classmethod
    def initialize(cls, inputs, hidden=64, rng=None):
        rng = rng or np.random.default_rng()
        params = dict(w1=rng.normal(0, 1 / np.sqrt(inputs), (inputs, hidden)), b1=np.zeros(hidden))
        for head, choices in HEADS.items():
            params[f'{head}_w'] = rng.normal(0, .01, (hidden, len(choices)))
            params[f'{head}_b'] = np.zeros(len(choices))
        return cls(params)

    @classmethod
    def load(cls, path):
        with np.load(Path(path)) as data:
            return cls(dict(data))

    def save(self, path):
        np.savez(Path(path), **self.params)

    def logits(self, x):
        h = np.tanh(x @ self.params['w1'] + self.params['b1'])
        return {head: h @ self.params[f'{head}_w'] + self.params[f'{head}_b'] for head in HEADS}

    def act(self, x):
        return decode_targets({head: int(np.argmax(z)) for head, z in self.logits(x).items()})

    def sample(self, x, rng):
        indices = {}
        for head, z in self.logits(x).items():
            p = np.exp(z - z.max())
            indices[head] = int(rng.choice(len(p), p=p / p.sum()))
        return (*decode_targets(indices), indices)
