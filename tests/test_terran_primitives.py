import unittest

from src.bots.terran_primitives import mining_commands, combat_command, scripted_targets, destination_reached, changes_order, scripted_attack
from src.learning.gameplay import Command


def unit(tag, kind, x=0, y=0, alliance=1, **fields):
    return dict(tag=tag, unit_type=kind, position=[x, y], alliance=alliance,
                display_type=1, orders=[], **({'cloak': 3, 'health': 45} | fields))


def economy(workers):
    return dict(units=[unit(100, 18, ideal_harvesters=4, build_progress=1),
                      unit(200, 341, x=5, alliance=3, mineral_contents=1000),
                      unit(201, 341, x=6, alliance=3, mineral_contents=1000),
                      unit(300, 20, x=4, y=4, build_progress=1, vespene_contents=2000)] + workers)


class MiningTests(unittest.TestCase):
    def test_idle_workers_get_distinct_saturated_mineral_slots(self):
        commands = mining_commands(economy([unit(i, 45) for i in range(1, 5)]), 0)
        self.assertEqual(len(commands), 4)
        self.assertEqual(sorted(c.target_unit for c in commands), [200, 200, 201, 201])

    def test_gas_budget_moves_excess_gas_workers_back_to_minerals(self):
        workers = [unit(i, 45) for i in range(1, 5)]
        for worker in workers:
            worker['orders'] = [dict(ability_id=295, target_unit_tag=300)]
        commands = mining_commands(economy(workers), 1)
        self.assertEqual(len(commands), 3)
        self.assertTrue(all(c.target_unit in (200, 201) for c in commands))

    def test_builders_and_reserved_workers_keep_their_tasks(self):
        builder = unit(1, 45)
        builder['orders'] = [dict(ability_id=319, target_world_space_pos=dict(x=12, y=12))]
        commands = mining_commands(economy([builder, unit(2, 45), unit(3, 45)]), 0, {2})
        self.assertEqual([c.units for c in commands], [(3,)])

    def test_resources_without_a_completed_base_are_not_assigned(self):
        state = economy([unit(1, 45)])
        state['units'][0]['build_progress'] = .5
        self.assertEqual(mining_commands(state, 3), [])

    def test_returning_worker_deposits_cargo_and_full_gas_gets_no_extra_worker(self):
        worker = unit(1, 45)
        worker['orders'] = [dict(ability_id=296, target_unit_tag=100)]
        state = economy([worker, unit(2, 45)])
        state['units'][3]['assigned_harvesters'] = 3
        commands = mining_commands(state, 3)
        self.assertEqual([c.units for c in commands], [(2,)])
        self.assertIn(commands[0].target_unit, (200, 201))


class ScriptedEconomyTests(unittest.TestCase):
    def test_losing_infantry_does_not_turn_remaining_army_into_unlimited_tanks(self):
        state = economy([unit(i, 45) for i in range(1, 35)])
        state['units'] += [unit(500+i, 48) for i in range(12)] + [unit(600+i, 33) for i in range(26)]
        state['player'] = dict(minerals=2000, vespene=500, food_cap=200, food_used=160)
        targets = scripted_targets(state)
        self.assertLess(targets.get('tanks', 100), 26)
        state['units'] = [u for u in state['units'] if u['unit_type'] != 33]
        self.assertGreater(scripted_targets(state).get('tanks', 0), 0)

    def test_starting_economy_keeps_growing_workers_and_builds_needed_supply(self):
        state = economy([unit(i, 45) for i in range(1, 15)])
        state['player'] = dict(minerals=100, vespene=0, food_cap=15, food_used=14)
        targets = scripted_targets(state)
        self.assertGreater(targets.get('workers', 0), 14)
        self.assertEqual(targets.get('supply'), 1)

    def test_excess_gas_and_spare_supply_do_not_keep_absorbing_workers_and_minerals(self):
        state = economy([unit(i, 45) for i in range(1, 25)])
        state['player'] = dict(minerals=75, vespene=1000, food_cap=100, food_used=40)
        targets = scripted_targets(state)
        self.assertEqual(targets.get('gas_workers'), 0)
        self.assertEqual(targets.get('supply'), 0)

    def test_second_completed_base_supports_larger_economy_and_production(self):
        state = economy([unit(i, 45) for i in range(1, 35)])
        state['units'] += [unit(400, 132, x=30, build_progress=1), unit(500, 21, build_progress=1)]
        state['player'] = dict(minerals=500, vespene=200, food_cap=70, food_used=50)
        targets = scripted_targets(state)
        self.assertGreater(targets.get('workers', 0), 34)
        self.assertGreater(targets.get('barracks', 0), 1)
        self.assertEqual(targets.get('factories'), 1)


TYPES = {48: dict(weapons=[dict(type=3, range=5)]),
         33: dict(weapons=[dict(type=1, range=7)]),
         32: dict(weapons=[dict(type=1, range=13)]),
         105: dict(weapons=[dict(type=1, range=.1)]),
         108: dict(weapons=[dict(type=2, range=5)])}


class CombatTests(unittest.TestCase):
    def test_support_units_do_not_keep_a_destroyed_ground_attack_running(self):
        state = dict(units=[unit(i, 54) for i in range(4)] + [unit(10+i, 35) for i in range(8)]
                     + [unit(30+i, 48) for i in range(10)] + [unit(50+i, 33) for i in range(2)])
        self.assertFalse(scripted_attack(state, True))
        state['units'] += [unit(100+i, 48) for i in range(30)]
        self.assertTrue(scripted_attack(state, False))

    def test_invulnerable_adept_shade_does_not_replace_a_real_target(self):
        shade = unit(10, 801, x=1, alliance=4)
        enemy = unit(11, 105, x=4, alliance=4)
        types = {**TYPES, 801: dict(name='AdeptPhaseShift', weapons=[])}
        command = combat_command(unit(1, 48), [shade, enemy], types, (20, 20), lambda p: True)
        self.assertEqual(command.target_unit, 11)

    def test_phoenix_lifted_actor_waits_until_it_can_receive_commands(self):
        marine = unit(1, 48)
        marine['buff_ids'] = [27, 5]
        self.assertIsNone(combat_command(marine, [unit(10, 108, x=2, alliance=4, is_flying=True)],
            TYPES, (20, 20), lambda p: True))
        marine['buff_ids'] = [27]
        self.assertIsNotNone(combat_command(marine, [], TYPES, (20, 20), lambda p: True))

    def test_dead_actor_does_not_issue_an_order(self):
        self.assertIsNone(combat_command(unit(1, 48, health=0), [], TYPES, (20, 20), lambda p: True))

    def test_sieged_tank_does_not_request_a_shot_beyond_stationary_attack_range(self):
        enemy = unit(10, 105, x=13.5, alliance=4, radius=1)
        command = combat_command(unit(1, 32, radius=1), [enemy], TYPES, (20, 20), lambda p: True)
        self.assertIsNone(command)

    def test_transforming_tank_keeps_its_order_until_the_transformation_finishes(self):
        tank = unit(1, 33)
        tank['orders'] = [dict(ability_id=390)]
        self.assertIsNone(combat_command(tank, [], TYPES, (20, 20), lambda p: True))

    def test_dead_target_is_not_selected_over_a_living_enemy(self):
        dead = unit(10, 105, x=1, alliance=4, health=0)
        alive = unit(11, 105, x=4, alliance=4)
        command = combat_command(unit(1, 48), [dead, alive], TYPES, (20, 20), lambda p: True)
        self.assertEqual(command.target_unit, 11)

    def test_reaper_grenade_does_not_distract_attacks_from_real_units(self):
        types = {**TYPES, 830: dict(name='KD8Charge', weapons=[])}
        grenade = unit(10, 830, x=1, alliance=4, health=1)
        enemy = unit(11, 105, x=4, alliance=4, health=35)
        command = combat_command(unit(1, 48), [grenade, enemy], types, (20, 20), lambda p: True)
        self.assertEqual(command.target_unit, 11)

    def test_undetected_cloak_is_not_a_direct_attack_target(self):
        enemy = unit(10, 108, x=3, alliance=4, is_flying=True, cloak=1)
        command = combat_command(unit(1, 48), [enemy], TYPES, (20, 20), lambda p: True)
        self.assertIsNone(command.target_unit)
        enemy['cloak'] = 2
        self.assertEqual(combat_command(unit(1, 48), [enemy], TYPES, (20, 20), lambda p: True).target_unit, 10)
        del enemy['cloak']
        self.assertIsNone(combat_command(unit(1, 48), [enemy], TYPES, (20, 20), lambda p: True).target_unit)

    def test_sieged_tank_shoots_a_reachable_enemy_beyond_minimum_range(self):
        close = unit(10, 105, x=1, alliance=4)
        distant = unit(11, 105, x=8, alliance=4)
        command = combat_command(unit(1, 32), [close, distant], TYPES, (20, 20), lambda p: True)
        self.assertEqual(command.target_unit, 11)

    def test_existing_attack_orders_continue_without_duplicate_commands(self):
        marine = unit(1, 48)
        marine['orders'] = [dict(ability_id=23, target_unit_tag=10)]
        self.assertFalse(changes_order(marine, Command(23, (1,), target_unit=10)))
        self.assertTrue(changes_order(marine, Command(23, (1,), target_unit=11)))
        marine['orders'] = [dict(ability_id=23, target_world_space_pos=dict(x=20, y=20))]
        self.assertFalse(changes_order(marine, Command(23, (1,), target_point=(20, 20))))
        self.assertTrue(changes_order(marine, Command(16, (1,), target_point=(20, 20))))

    def test_arrived_unit_can_wait_but_still_shoot_a_nearby_enemy(self):
        marine = unit(1, 48, x=20, y=20)
        self.assertFalse(changes_order(marine, Command(23, (1,), target_point=(20, 20))))
        self.assertTrue(changes_order(marine, Command(23, (1,), target_unit=10)))

    def test_stragglers_do_not_prevent_search_after_the_main_army_arrives(self):
        self.assertTrue(destination_reached([(0, 0)]*8 + [(100, 100)]*2, (0, 0)))
        self.assertFalse(destination_reached([(0, 0)] + [(100, 100)]*9, (0, 0)))

    def test_marine_shoots_air_but_tank_cannot(self):
        enemy = unit(10, 108, x=4, alliance=4, is_flying=True, health=50)
        marine = combat_command(unit(1, 48), [enemy], TYPES, (20, 20), lambda p: True)
        tank = combat_command(unit(2, 33), [enemy], TYPES, (20, 20), lambda p: True)
        self.assertIsNotNone(marine)
        self.assertIsNotNone(tank)
        self.assertEqual(marine.target_unit, 10)
        self.assertIsNone(tank.target_unit)

    def test_reloading_marine_kites_melee_on_walkable_ground(self):
        enemy = unit(10, 105, x=2, alliance=4)
        marine = unit(1, 48, weapon_cooldown=8)
        command = combat_command(marine, [enemy], TYPES, (20, 20), lambda p: True)
        self.assertIsNotNone(command)
        self.assertEqual(command.ability, 16)
        self.assertLess(command.target_point[0], 0)
        blocked = combat_command(marine, [enemy], TYPES, (20, 20), lambda p: False)
        self.assertEqual(blocked.ability, 23)

    def test_tank_sieges_for_visible_ground_and_unsieges_without_it(self):
        enemy = unit(10, 105, x=10, alliance=4)
        siege = combat_command(unit(1, 33), [enemy], TYPES, (20, 20), lambda p: True)
        unsiege = combat_command(unit(1, 32), [], TYPES, (20, 20), lambda p: True)
        self.assertIsNotNone(siege)
        self.assertIsNotNone(unsiege)
        self.assertEqual(siege.ability, 388)
        self.assertEqual(unsiege.ability, 390)

    def test_hidden_enemy_is_never_targeted(self):
        enemy = unit(10, 105, x=2, alliance=4)
        enemy['display_type'] = 2
        command = combat_command(unit(1, 48), [enemy], TYPES, (20, 20), lambda p: True)
        self.assertIsNotNone(command)
        self.assertIsNone(command.target_unit)
        self.assertEqual(command.target_point, (20, 20))
