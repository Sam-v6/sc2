import unittest
from src.learning.production_execution import queued_work, eligible_actors


class ProductionExecutionTests(unittest.TestCase):
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
