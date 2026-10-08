import unittest

from src.learning.replay_strategy import human_strategy_labels


def unit(kind, x=10, y=10, **extra):
    return dict(alliance=1, unit_type=kind, position=[x, y, 0], build_progress=1.0, **extra)


def frame(loop, units):
    return dict(game_loop=loop, units=units, player=dict(minerals=0, vespene=0, food_used=0, food_cap=0))


class HumanStrategyLabelTests(unittest.TestCase):
    def test_targets_are_own_counts_one_horizon_later(self):
        early = frame(0, [unit(45)] * 12 + [unit(18)])
        later = frame(1344, [unit(45)] * 20 + [unit(18), unit(132), unit(21), unit(46), unit(27),
                              unit(20, assigned_harvesters=3), unit(33), unit(32), unit(22)])
        labels = human_strategy_labels([early, later], (0, 0), (100, 100), horizon=1344)
        self.assertEqual(labels[0][0], dict(workers=20, bases=2, barracks=2, factories=1, starports=0,
                                            engineering_bays=1, refineries=1, gas_workers=3, tanks=2))
        # The last frame has no future; it labels with its own counts.
        self.assertEqual(labels[1][0]['workers'], 20)

    def test_attack_when_most_army_supply_is_past_the_midpoint(self):
        home = frame(0, [unit(48, 10, 10)] * 6 + [unit(33, 10, 10)])
        away = frame(24, [unit(48, 80, 80)] * 6 + [unit(33, 10, 10)])
        split = frame(48, [unit(48, 80, 80)] * 2 + [unit(33, 10, 10)] * 2)
        empty = frame(72, [unit(45, 90, 90)])
        labels = human_strategy_labels([home, away, split, empty], (0, 0), (100, 100), horizon=1344)
        self.assertEqual([attack for _, attack in labels], [False, True, False, False])


if __name__ == '__main__':
    unittest.main()
