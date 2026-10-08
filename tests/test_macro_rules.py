import unittest

from src.bots.macro_rules import depot_limit, rush_response, rush_seen, saturation, spend_float


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


class SaturationTests(unittest.TestCase):
    targets = dict(workers=64, gas_workers=12)

    def test_caps_workers_by_ready_bases(self):
        self.assertEqual(saturation(self.targets, state([unit(132), unit(18, build_progress=.5)]))['workers'], 28)
        self.assertEqual(saturation(self.targets, state([unit(132), unit(18)]))['workers'], 50)
        self.assertEqual(saturation(self.targets, state([unit(132)] * 3))['workers'], 64)

    def test_caps_gas_workers_only_when_gas_floats_and_minerals_do_not(self):
        bases = [unit(132)] * 3
        self.assertEqual(saturation(self.targets, state(bases, minerals=100, vespene=900))['gas_workers'], 6)
        self.assertEqual(saturation(self.targets, state(bases, minerals=500, vespene=900))['gas_workers'], 12)
        self.assertEqual(saturation(self.targets, state(bases, minerals=100, vespene=700))['gas_workers'], 12)


class RushTests(unittest.TestCase):
    targets = dict(bases=2, barracks=1, workers=23)

    def at(self, seconds, units):
        return dict(state(units), game_loop=seconds * 22.4)

    def test_rush_seen_from_early_marines_or_barracks(self):
        self.assertTrue(rush_seen(self.at(130, [unit(48, alliance=4)] * 4)))
        self.assertFalse(rush_seen(self.at(130, [unit(48, alliance=4)] * 3 + [unit(48)])))
        self.assertFalse(rush_seen(self.at(170, [unit(48, alliance=4)] * 6)))
        self.assertTrue(rush_seen(self.at(170, [unit(21, alliance=4)] * 3)))
        self.assertFalse(rush_seen(self.at(190, [unit(21, alliance=4)] * 3)))

    def test_rush_response_holds_one_base_and_three_barracks_until_300s(self):
        self.assertEqual(rush_response(self.targets, self.at(200, []), True), dict(bases=1, barracks=3, workers=23))
        self.assertIs(rush_response(self.targets, self.at(200, []), False), self.targets)
        self.assertIs(rush_response(self.targets, self.at(300, []), True), self.targets)


if __name__ == '__main__':
    unittest.main()
