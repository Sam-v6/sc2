import unittest
from src.learning.production_primitives import primitive_assistance, scripted_army_destination
from tests.test_terran_primitives import unit, TYPES

DATA = {**TYPES, 45: dict(name='SCV'), 48: dict(weapons=[dict(type=3, range=5)], attributes=[3], food_required=1),
        51: dict(weapons=[dict(type=1, range=6)], attributes=[3], food_required=2),
        35: dict(weapons=[dict(type=2, range=9)], food_required=2),
        54: dict(weapons=[], food_required=2), 19: dict(attributes=[8]),
        132: dict(attributes=[8]), 21: dict(name='Barracks', attributes=[8])}


def state(units):
    return dict(units=units, player=dict(minerals=200, vespene=0), upgrades=[], game_loop=24)


class ProductionPrimitiveTests(unittest.TestCase):
    def commands(self, st, selected=(), mining=True):
        return primitive_assistance(st, set(selected), DATA, {}, (30, 30), lambda p: True, mining)

    def test_selected_casters_and_returning_workers_are_not_overridden(self):
        returning = unit(1, 45)
        returning['orders'] = [dict(ability_id=296)]
        selected = unit(2, 45)
        patch = unit(10, 999, alliance=3, mineral_contents=1000)
        st = state([returning, selected, patch, unit(20, 132)])
        self.assertEqual(self.commands(st, [2]), [])

    def test_no_production_is_invented_and_support_claims_one_order_per_actor(self):
        st = state([unit(1, 132, energy=50), unit(2, 19),
                    unit(3, 54, energy=50, x=10), unit(4, 48, health=20, health_max=55, x=12),
                    unit(5, 999, alliance=3, mineral_contents=1000)])
        commands = self.commands(st, [4])
        self.assertEqual({c.ability for c in commands}, {171, 556, 386})
        actors = [c.units[0] for c in commands]
        self.assertEqual(len(actors), len(set(actors)))
        self.assertNotIn(4, actors)

    def test_fighter_follows_the_ground_force_without_an_air_target(self):
        commands = self.commands(state([unit(1, 35), unit(2, 51, x=5, y=5)]), mining=False)
        fighter = next(c for c in commands if c.units == (1,))
        self.assertEqual(fighter.target_point, (5, 5))

    def test_interrupted_building_gets_a_worker_without_mining_overwriting_it(self):
        st = state([unit(1, 45), unit(2, 21, x=4, build_progress=.5), unit(3, 132),
                    unit(4, 999, alliance=3, mineral_contents=1000)])
        commands = self.commands(st)
        worker = [c for c in commands if c.units == (1,)]
        self.assertEqual(len(worker), 1)
        self.assertEqual((worker[0].ability, worker[0].target_unit), (1, 2))

    def test_marauders_count_toward_attack_strength_but_air_support_does_not(self):
        st = state([unit(i, 51) for i in range(20)] + [unit(100+i, 35) for i in range(8)])
        _, attacking, _ = scripted_army_destination(st, DATA, (0, 0), (100, 100), (50, 50), [], False, 0)
        self.assertTrue(attacking)
        st['units'] = [unit(100+i, 35) for i in range(8)]
        _, attacking, _ = scripted_army_destination(st, DATA, (0, 0), (100, 100), (50, 50), [], True, 0)
        self.assertFalse(attacking)
