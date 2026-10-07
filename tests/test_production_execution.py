import unittest
from src.learning.production_execution import queued_work, eligible_actors


class ProductionExecutionTests(unittest.TestCase):
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
