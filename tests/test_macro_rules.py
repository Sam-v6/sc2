import unittest

from src.bots.macro_rules import depot_limit, spend_float


def unit(kind, alliance=1, **fields):
    return dict(unit_type=kind, alliance=alliance, **fields)


def state(units, minerals=0, food_used=50, vespene=0):
    return dict(units=units, player=dict(minerals=minerals, food_used=food_used, vespene=vespene))


class DepotLimitTests(unittest.TestCase):
    def test_one_depot_early_and_more_with_ready_production(self):
        self.assertEqual(depot_limit(state([unit(18), unit(21, build_progress=.5)])), 1)
        self.assertEqual(depot_limit(state([unit(132), unit(132)] + [unit(21)] * 6 + [unit(27), unit(21, alliance=4)])), 4)


class SpendFloatTests(unittest.TestCase):
    targets = dict(barracks=6, workers=60, tanks=2, factories=1)

    def test_adds_barracks_for_unspent_minerals_on_two_bases(self):
        self.assertEqual(spend_float(self.targets, state([unit(18), unit(132)], minerals=1300))['barracks'], 9)
        self.assertEqual(spend_float(self.targets, state([unit(18), unit(132)], minerals=9000))['barracks'], 14)

    def test_adds_tanks_and_factories_for_banked_gas(self):
        bank = spend_float(self.targets, state([unit(18), unit(132)], vespene=800))
        self.assertEqual((bank['tanks'], bank['factories'], bank['barracks']), (6, 2, 6))
        self.assertEqual(spend_float(self.targets, state([unit(18), unit(132)], vespene=1400))['factories'], 3)

    def test_leaves_targets_on_one_base_low_bank_or_max_supply(self):
        one_base = state([unit(18), unit(132, build_progress=.3)], minerals=2000, vespene=2000)
        self.assertIs(spend_float(self.targets, one_base), self.targets)
        self.assertEqual(spend_float(self.targets, state([unit(18), unit(18)], minerals=600, vespene=400)), self.targets)
        self.assertIs(spend_float(self.targets, state([unit(18), unit(18)], minerals=3000, food_used=195)), self.targets)


if __name__ == '__main__':
    unittest.main()
