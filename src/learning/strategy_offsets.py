"""Policy search over interpretable adjustments to a strategy policy.

Per enemy race: an additive offset for every count target in each game phase,
plus army-supply attack thresholds (hold below ``attack[0]`` unless the policy
attacks; always attack at ``attack[1]``). Optimized with the cross-entropy method.
"""
import numpy as np

from src.learning.strategy_policy import HEADS

COUNT_HEADS = ('workers', 'bases', 'barracks', 'factories', 'starports', 'engineering_bays',
               'refineries', 'gas_workers', 'tanks')
PHASES = (240, 480)  # game-second boundaries: early, mid, late
RACES = ('Terran', 'Zerg', 'Protoss')
STD = dict(workers=4., bases=.7, barracks=1.5, factories=1., starports=.7, engineering_bays=.5,
           refineries=1., gas_workers=3., tanks=1.5)


def phase(seconds):
    return sum(seconds >= boundary for boundary in PHASES)


def apply_offsets(targets, attack, params, race, seconds, army_food):
    p = params.get(race)
    if p is None:
        return targets, attack
    offsets = p['offsets'][phase(seconds)]
    adjusted = dict(targets)
    for i, head in enumerate(COUNT_HEADS):
        choices = HEADS[head]
        adjusted[head] = int(min(max(round(targets[head] + offsets[i]), choices[0]), choices[-1]))
    hold, force = p['attack']
    return adjusted, bool((attack and army_food >= hold) or army_food >= force)


def fitness(result, seconds):
    """Wins dominate; faster wins and longer survival break ties."""
    if result == 'Victory':
        return 1 + .2 * (1 - seconds / 1200)
    if result == 'Tie':
        return .3
    return .2 * seconds / 1200 if result == 'Defeat' else 0


def initial_distribution():
    rows = len(PHASES) + 1
    mean = {r: dict(offsets=np.zeros((rows, len(COUNT_HEADS))), attack=np.array([0., 200.])) for r in RACES}
    std = {r: dict(offsets=np.tile([STD[h] for h in COUNT_HEADS], (rows, 1)), attack=np.array([8., 30.]))
           for r in RACES}
    return mean, std


def flatten(p):
    return np.concatenate([p['offsets'].ravel(), p['attack']])


def unflatten(flat):
    return dict(offsets=flat[:-2].reshape(len(PHASES) + 1, len(COUNT_HEADS)).copy(), attack=flat[-2:].copy())


def sample_params(mean, std, race, rng):
    flat = flatten(mean[race]) + rng.normal(size=flatten(std[race]).size) * flatten(std[race])
    params = {r: dict(offsets=m['offsets'].copy(), attack=m['attack'].copy()) for r, m in mean.items()}
    params[race] = unflatten(flat)
    return params, flat


def cem_update(samples, scores, elites, mean, std, floor):
    best = samples[np.argsort(-scores)[:elites]]
    return best.mean(0), np.maximum(best.std(0), floor)
