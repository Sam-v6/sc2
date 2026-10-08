import unittest

import numpy as np

from src.learning.strategy_offsets import (
    COUNT_HEADS, PHASES, apply_offsets, cem_update, fitness, initial_distribution, sample_params)

TARGETS = dict(workers=30, bases=2, barracks=3, factories=1, starports=0, engineering_bays=0,
               refineries=2, gas_workers=6, tanks=2)


def params(**race_heads):
    p = initial_distribution()[0]
    for key, value in race_heads.items():
        race, phase, head = key.split('__')
        p[race]['offsets'][int(phase)][COUNT_HEADS.index(head)] = value
    return p


class StrategyOffsetTests(unittest.TestCase):
    def test_zero_offsets_leave_targets_and_attack_unchanged(self):
        self.assertEqual(apply_offsets(TARGETS, True, params(), 'Zerg', 100, 30), (TARGETS, True))

    def test_offsets_apply_by_race_and_phase_rounded_and_clipped(self):
        p = params(Terran__0__barracks=2.4, Terran__2__workers=-3.6, Zerg__0__barracks=5)
        early, _ = apply_offsets(TARGETS, False, p, 'Terran', PHASES[0] - 1, 0)
        late, _ = apply_offsets(TARGETS, False, p, 'Terran', PHASES[1] + 1, 0)
        self.assertEqual(early['barracks'], 5)
        self.assertEqual(early['workers'], 30)
        self.assertEqual(late['workers'], 26)
        low, _ = apply_offsets(dict(TARGETS, tanks=0), False, params(Protoss__0__tanks=-5), 'Protoss', 0, 0)
        self.assertEqual(low['tanks'], 0)

    def test_attack_thresholds_hold_or_force(self):
        p = params()
        p['Zerg']['attack'] = np.array([20., 60.])
        self.assertFalse(apply_offsets(TARGETS, True, p, 'Zerg', 0, 19)[1])
        self.assertTrue(apply_offsets(TARGETS, True, p, 'Zerg', 0, 20)[1])
        self.assertTrue(apply_offsets(TARGETS, False, p, 'Zerg', 0, 60)[1])
        self.assertFalse(apply_offsets(TARGETS, False, p, 'Zerg', 0, 59)[1])

    def test_fitness_prefers_fast_wins_and_long_survival(self):
        self.assertGreater(fitness('Victory', 400), fitness('Victory', 1000))
        self.assertGreater(fitness('Victory', 1200), fitness('Tie', 1200))
        self.assertGreater(fitness('Tie', 1200), fitness('Defeat', 1100))
        self.assertGreater(fitness('Defeat', 900), fitness('Defeat', 300))
        self.assertEqual(fitness(None, 0), 0)

    def test_cem_moves_mean_toward_elites_and_keeps_minimum_spread(self):
        mean, std = np.zeros(3), np.ones(3)
        samples = np.array([[1., 0, 0], [2., 0, 0], [-5., 0, 0], [-6., 0, 0]])
        new_mean, new_std = cem_update(samples, np.array([1., .9, 0, 0]), 2, mean, std, floor=.3)
        np.testing.assert_allclose(new_mean, [1.5, 0, 0])
        self.assertTrue((new_std >= .3).all())

    def test_sampled_params_round_trip_through_flat_vector(self):
        mean, std = initial_distribution()
        p, flat = sample_params(mean, std, 'Terran', np.random.default_rng(0))
        self.assertEqual(flat.size, (len(PHASES) + 1) * len(COUNT_HEADS) + 2)
        self.assertEqual(p['Terran']['offsets'].shape, (len(PHASES) + 1, len(COUNT_HEADS)))
        np.testing.assert_allclose(np.concatenate([p['Terran']['offsets'].ravel(), p['Terran']['attack']]), flat)


if __name__ == '__main__':
    unittest.main()
