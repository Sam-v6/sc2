import unittest
from src.learning.production_execution import queued_work, eligible_actors


class ProductionExecutionTests(unittest.TestCase):
    def test_supply_full_excludes_training_but_preserves_build_and_research(self):
        from src.learning.production_execution import supply_feasible_choices
        data = dict(abilities=[dict(ability_id=595, friendly_name='Train Hellion'),
                               dict(ability_id=524, friendly_name='Train SCV'),
                               dict(ability_id=328, friendly_name='Build Factory')],
                    units=[dict(ability_id=595, food_required=2),
                           dict(ability_id=524, food_required=1)])
        scores = {595: .8, 524: .1, 328: .05}
        state = dict(player=dict(food_used=200, food_cap=200), units=[])
        self.assertEqual(supply_feasible_choices(scores, state, data), {328: .05})
        state['player']['food_used'] = 199
        self.assertEqual(supply_feasible_choices(scores, state, data), {524: .1, 328: .05})
        state['player']['food_used'] = 198
        self.assertEqual(supply_feasible_choices(scores, state, data), scores)

    def test_waiting_and_unacknowledged_train_commands_reserve_supply(self):
        from src.learning.production_execution import supply_feasible_choices
        data = dict(abilities=[dict(ability_id=595, friendly_name='Train Hellion'),
                               dict(ability_id=596, friendly_name='Train Hellion', remaps_to_ability_id=595)],
                    units=[dict(ability_id=595, food_required=2)])
        state = dict(player=dict(food_used=194, food_cap=200), units=[
            dict(alliance=1, orders=[dict(ability_id=595, progress=.5),
                                    dict(ability_id=596, progress=0)])])
        self.assertEqual(supply_feasible_choices({595: 1}, state, data, [596]), {595: 1})
        self.assertEqual(supply_feasible_choices({595: 1}, state, data, [596, 595]), {})

    def test_physically_rejected_factory_yields_until_its_recheck(self):
        from src.learning.production_execution import preferred_production_intent
        scores = {328: .8, 560: .1, 324: .02}
        self.assertEqual(preferred_production_intent(scores, {328: 224}, 8), 560)
        self.assertEqual(preferred_production_intent(scores, {328: 224}, 224), 328)
        self.assertIsNone(preferred_production_intent({328: .8}, {328: 224}, 8))

    def test_preference_does_not_filter_expensive_but_physically_available_intent(self):
        from src.learning.production_execution import preferred_production_intent
        scores = {328: .8, 324: .02}
        self.assertEqual(preferred_production_intent(scores, {}, 8), 328)
        self.assertIsNone(preferred_production_intent({}, {}, 8))

    def test_unit_target_builder_routes_approach_outside_the_blocking_geyser(self):
        from src.learning.production_execution import builder_approach_points
        from src.learning.gameplay import Command
        state = dict(units=[dict(tag=7, position=[26.5, 135.5], radius=1.5)])
        points = builder_approach_points(Command(320, (1,), target_unit=7), state)
        self.assertEqual(len(points), 8)
        self.assertNotIn((26.5, 135.5), points)
        self.assertIn((28.5, 135.5), points)
        self.assertEqual(builder_approach_points(Command(320, (1,), target_unit=8), state), [])
        self.assertEqual(builder_approach_points(Command(321, (1,),
                         target_point=(30.5, 120.5)), state), [(30.5, 120.5)])

    def test_unit_target_construction_has_an_observed_route_destination(self):
        from src.learning.production_execution import command_point
        from src.learning.gameplay import Command
        state = dict(units=[dict(tag=4337696769, position=[77.5, 145.5, 8])])
        self.assertEqual(command_point(Command(320, (4348706817,),
                         target_unit=4337696769), state), (77.5, 145.5))
        self.assertIsNone(command_point(Command(320, (4348706817,),
                          target_unit=999), state))
        self.assertEqual(command_point(Command(321, (4348706817,),
                         target_point=(30.5, 120.5)), state), (30.5, 120.5))

    def test_preferred_factory_waits_instead_of_spending_savings_on_bunker(self):
        from src.learning.production_execution import affordable_production_intent
        # Native 07 loop 5344: Factory is preferred but its 150 minerals are short.
        scores = {328: .7915937304496765, 324: .02503737434744835}
        prices = {328: (150, 100), 324: (100, 0)}
        self.assertIsNone(affordable_production_intent(scores, prices, 100, 654))
        self.assertEqual(affordable_production_intent(scores, prices, 150, 654), 328)
        self.assertIsNone(affordable_production_intent(scores, prices, 150, 99))

    def test_unknown_preferred_price_does_not_become_a_cheaper_fallback(self):
        from src.learning.production_execution import affordable_production_intent
        self.assertIsNone(affordable_production_intent({999: .8, 524: .2},
                          {524: (50, 0)}, 500, 500))
        self.assertIsNone(affordable_production_intent({}, {}, 500, 500))

    def test_pending_builders_keep_their_budget_until_start_is_verified(self):
        from src.learning.production_execution import unreserved_resources
        prices = {328: (150, 100), 324: (100, 0)}
        player = dict(minerals=200, vespene=180)
        self.assertEqual(unreserved_resources(player, [328], prices), (50, 80))
        self.assertEqual(unreserved_resources(player, [], prices), (200, 180))
        self.assertEqual(unreserved_resources(player, [328, 328], prices), (0, 0))
        self.assertEqual(player, dict(minerals=200, vespene=180))

    def test_bounded_training_queue_requires_native_availability_and_space(self):
        catalog = {560: dict(friendly_name='Train Marine')}
        actor = dict(tag=1, alliance=1, unit_type=21,
                     orders=[dict(ability_id=560, progress=.5)])
        state = dict(units=[actor])
        self.assertEqual(eligible_actors(state, 560, {1: [560]}, catalog, {}), [])
        self.assertEqual(eligible_actors(state, 560, {1: [560]}, catalog, {},
                                        max_train_orders=2), [actor])
        self.assertEqual(eligible_actors(state, 560, {1: []}, catalog, {},
                                        max_train_orders=2), [])
        actor['orders'].append(dict(ability_id=560, progress=0))
        self.assertEqual(eligible_actors(state, 560, {1: [560]}, catalog, {},
                                        max_train_orders=2), [])

    def test_training_queue_does_not_allow_other_busy_commands(self):
        actor = dict(tag=1, alliance=1, unit_type=21,
                     orders=[dict(ability_id=560, progress=.5)])
        for name in ('Build TechLab', 'Research Stimpack', 'Morph OrbitalCommand'):
            with self.subTest(name=name):
                self.assertEqual(eligible_actors(dict(units=[actor]), 999,
                                 {1: [999]}, {999: dict(friendly_name=name)}, {},
                                 max_train_orders=2), [])

    def test_resource_filter_keeps_exact_budget_and_unknown_prices(self):
        from src.learning.production_execution import resource_affordable_choices
        scores = {319: .6, 560: .2, 999: .1}
        prices = {319: (100, 0), 560: (50, 0)}
        self.assertEqual(resource_affordable_choices(scores, prices, 100, 0), scores)
        self.assertEqual(resource_affordable_choices(scores, prices, 99, 0),
                         {560: .2, 999: .1})
        self.assertEqual(scores, {319: .6, 560: .2, 999: .1})

    def test_resource_filter_checks_gas_and_does_not_invent_an_action(self):
        from src.learning.production_execution import resource_affordable_choices
        scores = {328: .9}
        prices = {328: (150, 100)}
        self.assertEqual(resource_affordable_choices(scores, prices, 150, 99), {})
        self.assertEqual(resource_affordable_choices(scores, prices, 149, 100), {})
        self.assertEqual(resource_affordable_choices(scores, prices, 150, 100), scores)

    def test_supply_warning_requires_a_retained_matching_training_order(self):
        from src.learning.production_execution import waiting_for_supply
        catalog = {595: dict(friendly_name='Train Hellion')}
        error = dict(result=13, ability_id=595, unit_tag=1)
        state = dict(units=[dict(tag=1, alliance=1,
                                orders=[dict(ability_id=595, progress=0)])])
        self.assertTrue(waiting_for_supply(error, state, catalog))
        state['units'][0]['orders'][0]['progress'] = .5
        self.assertFalse(waiting_for_supply(error, state, catalog))
        state['units'][0]['orders'] = []
        self.assertFalse(waiting_for_supply(error, state, catalog))
        state['units'][0]['orders'] = [dict(ability_id=595, progress=0)]
        error['result'] = 53
        self.assertFalse(waiting_for_supply(error, state, catalog))

    def test_smart_resume_worker_is_not_available_for_other_construction(self):
        state = dict(units=[dict(tag=1, alliance=1, unit_type=45,
                            orders=[dict(ability_id=1, target_unit_tag=2)]),
                           dict(tag=2, alliance=1, unit_type=21, build_progress=.5)])
        self.assertEqual(eligible_actors(state, 321, {1: [321]}, {}, {45: 'SCV'}), [])

    def test_prices_distinguish_morph_research_and_free_lift(self):
        from src.learning.production_execution import command_cost
        data = dict(abilities=[dict(ability_id=1516, friendly_name='Morph OrbitalCommand'),
                               dict(ability_id=452, friendly_name='Lift Barracks'),
                               dict(ability_id=2297, friendly_name='Research ArmorLevel1'),
                               dict(ability_id=864, friendly_name='Research ArmorLevel1')],
                    units=[dict(name='CommandCenter', mineral_cost=400),
                           dict(name='OrbitalCommand', ability_id=1516, mineral_cost=550),
                           dict(name='BarracksFlying', ability_id=452, mineral_cost=150)],
                    upgrades=[dict(ability_id=2297, mineral_cost=100, vespene_cost=100),
                              dict(name='PassiveUpgrade', mineral_cost=999)])
        self.assertEqual(command_cost(1516, data), (150, 0))
        self.assertEqual(command_cost(452, data), (0, 0))
        self.assertEqual(command_cost(864, data), (100, 100))

    def test_generic_addon_price_requires_native_alias_agreement(self):
        from src.learning.production_execution import command_cost
        data = dict(abilities=[dict(ability_id=3682, friendly_name='Build TechLab'),
                               dict(ability_id=421, friendly_name='Build TechLab Barracks', remaps_to_ability_id=3682),
                               dict(ability_id=454, friendly_name='Build TechLab Factory', remaps_to_ability_id=3682)],
                    units=[dict(ability_id=421, mineral_cost=50, vespene_cost=25),
                           dict(ability_id=454, mineral_cost=50, vespene_cost=25)], upgrades=[])
        self.assertEqual(command_cost(3682, data), (50, 25))
        data['units'][1]['mineral_cost'] = 75
        with self.assertRaisesRegex(ValueError, 'No unique production price'):
            command_cost(3682, data)

    def test_waiting_units_reserve_supply_across_producers(self):
        from src.learning.production_execution import queued_supply
        data = dict(abilities=[dict(ability_id=524, friendly_name='Train SCV'),
                               dict(ability_id=595, friendly_name='Train Hellion')],
                    units=[dict(ability_id=524, food_required=1),
                           dict(ability_id=595, food_required=2)])
        state = dict(units=[dict(alliance=1, orders=[
            dict(ability_id=524, progress=.3), dict(ability_id=524, progress=0)]),
            dict(alliance=1, orders=[dict(ability_id=595, progress=.75),
                 dict(ability_id=595, progress=.2), dict(ability_id=595, progress=0)]),
            dict(alliance=4, orders=[dict(ability_id=595, progress=0)])])
        self.assertEqual(queued_supply(state, data), 3)

    def test_cancel_last_uses_unique_current_native_queue_ability(self):
        from src.learning.production_execution import queried_command_ability
        catalog = {306: dict(remaps_to_ability_id=3671),
                   304: dict(remaps_to_ability_id=3671),
                   864: dict(remaps_to_ability_id=3700),
                   865: dict(remaps_to_ability_id=3700)}
        self.assertEqual(queried_command_ability(3671, [306], catalog), 306)
        self.assertIsNone(queried_command_ability(3671, [304, 306], catalog))
        self.assertIsNone(queried_command_ability(3671, [], catalog))
        self.assertIsNone(queried_command_ability(865, [864], catalog))

    def test_research_tiers_keep_specific_queue_identity(self):
        catalog = {864: dict(remaps_to_ability_id=3700),
                   865: dict(remaps_to_ability_id=3700)}
        goals = {f'upgrade:Armor{tier}': dict(ability=ability, unit_type=None,
                    descriptor=dict(friendly_name=f'Research ArmorLevel{tier}'))
                 for tier, ability in [(1, 864), (2, 865)]}
        state = dict(units=[dict(tag=1, alliance=1, unit_type=29,
                    orders=[dict(ability_id=864)])])
        queued, active = queued_work(state, goals, catalog, {29: 'Armory'})
        self.assertEqual(queued, {'upgrade:Armor1': 1})
        self.assertEqual(active, {(1, 'upgrade:Armor1')})
        state['units'][0]['orders'][0]['ability_id'] = 3700
        self.assertEqual(queued_work(state, goals, catalog, {29: 'Armory'}), ({}, set()))

    def test_specific_research_availability_does_not_unlock_other_tiers(self):
        catalog = {864: dict(remaps_to_ability_id=3700,
                            friendly_name='Research ArmorLevel1'),
                   865: dict(remaps_to_ability_id=3700,
                            friendly_name='Research ArmorLevel2')}
        state = dict(units=[dict(tag=1, alliance=1, unit_type=29, orders=[])])
        self.assertEqual(eligible_actors(state, 865, {1: [864]}, catalog, {}), [])
        self.assertEqual([u['tag'] for u in eligible_actors(
            state, 864, {1: [864]}, catalog, {})], [1])

    def test_started_building_excluded_but_queued_train_included(self):
        goals = {'unit:Barracks': dict(ability=321, unit_type=21,
                    descriptor=dict(friendly_name='Build Barracks')),
                 'unit:Marine': dict(ability=560, unit_type=48,
                    descriptor=dict(friendly_name='Train Marine'))}
        state = dict(units=[
            dict(tag=1, alliance=1, unit_type=45, position=[0, 0],
                 orders=[dict(ability_id=321, target_world_space_pos=dict(x=8, y=8))]),
            dict(tag=2, alliance=1, unit_type=21, position=[8, 8], build_progress=.5),
            dict(tag=3, alliance=1, unit_type=21, position=[20, 20],
                 orders=[dict(ability_id=560)])])
        queued, active = queued_work(state, goals, {}, {})
        self.assertEqual(queued, {'unit:Marine': 1})
        self.assertEqual(active, {(1, 'unit:Barracks'), (3, 'unit:Marine')})
        state['units'].pop(1)
        self.assertEqual(queued_work(state, goals, {}, {})[0],
                         {'unit:Barracks': 1, 'unit:Marine': 1})

    def test_addon_alias_resolved_by_producer(self):
        goals = {f'unit:{parent}TechLab': dict(ability=ability, unit_type=37,
                    descriptor=dict(friendly_name=f'Build TechLab {parent}'))
                 for parent, ability in [('Barracks', 421), ('Factory', 454)]}
        catalog = {421: dict(remaps_to_ability_id=3682),
                   454: dict(remaps_to_ability_id=3682)}
        state = dict(units=[dict(tag=1, alliance=1, unit_type=27,
                    position=[0, 0], orders=[dict(ability_id=3682)])])
        self.assertEqual(queued_work(state, goals, catalog, {27: 'Factory'})[0],
                         {'unit:FactoryTechLab': 1})

    def test_mining_worker_eligible_builder_busy_structure_excluded(self):
        state = dict(units=[
            dict(tag=1, alliance=1, unit_type=45, orders=[dict(ability_id=295)]),
            dict(tag=2, alliance=1, unit_type=45, orders=[dict(ability_id=321)]),
            dict(tag=3, alliance=1, unit_type=21, orders=[dict(ability_id=560)])])
        catalog = {321: dict(friendly_name='Build Barracks')}
        eligible = eligible_actors(state, 321, {1: {321}, 2: {321}, 3: {321}},
                                   catalog, {45: 'SCV', 21: 'Barracks'})
        self.assertEqual([u['tag'] for u in eligible], [1])

    def test_nearby_existing_building_is_not_the_requested_foundation(self):
        goals = {'unit:Barracks': dict(ability=321, unit_type=21,
                    descriptor=dict(friendly_name='Build Barracks'))}
        state = dict(units=[dict(tag=1, alliance=1, unit_type=45,
                 position=[0, 0], orders=[dict(ability_id=321,
                 target_world_space_pos=dict(x=8, y=8))]),
                 dict(tag=2, alliance=1, unit_type=21, position=[12, 8])])
        self.assertEqual(queued_work(state, goals, {}, {})[0], {'unit:Barracks': 1})

    def test_generic_addon_alias_cannot_choose_the_wrong_production_building(self):
        state = dict(units=[dict(tag=1, alliance=1, unit_type=28),
                            dict(tag=2, alliance=1, unit_type=27),
                            dict(tag=3, alliance=1, unit_type=21)])
        catalog = {454: dict(remaps_to_ability_id=3682,
                            friendly_name='Build TechLab Factory')}
        actors = eligible_actors(state, 454, {1: {3682}, 2: {3682}, 3: {3682}},
                                  catalog, {28: 'Starport', 27: 'Factory', 21: 'Barracks'})
        self.assertEqual([u['tag'] for u in actors], [2])

    def test_inactive_upgrade_pointer_resolves_to_unique_active_research(self):
        from src.learning.production_execution import goal_catalog
        data=dict(units=[],upgrades=[dict(name='TerranVehicleAndShipArmorsLevel1',
                                        upgrade_id=116,ability_id=2297)],abilities=[
            dict(ability_id=2297,available=False,
                 friendly_name='Research TerranVehicleAndShipPlatingLevel1'),
            dict(ability_id=864,available=True,remaps_to_ability_id=3700,
                 friendly_name='Research TerranVehicleAndShipPlatingLevel1'),
            dict(ability_id=3700,available=True,
                 friendly_name='Research TerranVehicleAndShipPlating')])
        name='upgrade:TerranVehicleAndShipArmorsLevel1'
        goals=goal_catalog(data,[name])
        self.assertEqual(goals[name]['ability'],864)
        catalog={a['ability_id']:a for a in data['abilities']}
        state=dict(units=[dict(tag=10,alliance=1,unit_type=29,orders=[])])
        self.assertEqual([u['tag'] for u in eligible_actors(state,goals[name]['ability'],
                         {10:[3700]},catalog,{29:'Armory'})],[10])
        data['abilities'].append(dict(data['abilities'][1],ability_id=999))
        with self.assertRaises(ValueError):
            goal_catalog(data,[name])
