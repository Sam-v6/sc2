import unittest
from src.learning.production_clearance import reservations, clear_site
from src.learning.production_clearance import resolve_production_placement
from src.learning.gameplay import Command
from s2clientprotocol import sc2api_pb2 as pb, query_pb2 as query


class ProductionClearanceTests(unittest.TestCase):
    def test_refinery_sites_include_completed_expansion_and_exclude_occupied_home(self):
        from src.learning.production_clearance import refinery_sites
        home = dict(tag=1, alliance=1, unit_type=18, position=[33.5, 138.5])
        expansion = dict(tag=2, alliance=1, unit_type=18, position=[31.5, 113.5])
        occupied = dict(tag=3, alliance=3, position=[26.5, 135.5], vespene_contents=1862)
        refinery = dict(tag=4, alliance=1, unit_type=20,
                        position=[26.5, 135.5], vespene_contents=1862)
        free = dict(tag=5, alliance=3, position=[28.5, 106.5], vespene_contents=2000)
        state = dict(units=[home, expansion, occupied, refinery, free])
        self.assertEqual(refinery_sites(state, {}), [free])
        for change in (dict(build_progress=.5), dict(alliance=4), dict(is_flying=True)):
            with self.subTest(change=change):
                state['units'][1] = dict(expansion, **change)
                self.assertEqual(refinery_sites(state, {}), [])

    def test_existing_producer_keeps_addon_pad_and_spawn_perimeter(self):
        state = dict(units=[dict(tag=1, alliance=1, unit_type=27, position=[10, 10])])
        reserved = reservations(state, {27: dict(footprint_radius=1.5)}, {})
        self.assertFalse(clear_site((12.5, 9.5), 1, reserved))
        self.assertFalse(clear_site((10, 13), 1, reserved))
        self.assertTrue(clear_site((10, 15), 1, reserved))

    def test_pending_builder_and_current_batch_footprints_are_reserved(self):
        state = dict(units=[dict(tag=1, alliance=1, unit_type=45, position=[0, 0],
                     orders=[dict(ability_id=319, target_world_space_pos=dict(x=20, y=20))])])
        reserved = reservations(state, {}, {319: dict(is_building=True, footprint_radius=1)})
        self.assertFalse(clear_site((20, 20), 1, reserved))
        self.assertTrue(clear_site((24, 20), 1, reserved))

    def test_structures_leave_a_two_tile_lane_for_large_ground_units(self):
        state = dict(units=[dict(tag=1, alliance=1, unit_type=27, position=[10, 10]),
                           dict(tag=2, alliance=1, unit_type=22, position=[20, 10])])
        units = {27: dict(attributes=[8], ability_id=328),
                 22: dict(attributes=[8], ability_id=322)}
        catalog = {328: dict(footprint_radius=1.5), 322: dict(footprint_radius=1.5)}
        reserved = reservations(state, units, catalog)
        self.assertFalse(clear_site((10, 14), 1, reserved))
        self.assertTrue(clear_site((10, 14.5), 1, reserved))
        self.assertFalse(clear_site((20, 14), 1, reserved))

    def test_lowered_depots_do_not_block_a_ground_lane(self):
        state = dict(units=[dict(tag=1, alliance=1, unit_type=47, position=[10, 10])])
        self.assertTrue(clear_site((10, 12), 1,
            reservations(state, {47: dict(attributes=[8])}, {})))

    def test_unstarted_refinery_reserves_its_geyser(self):
        from src.learning.production_clearance import claimed_geysers
        state = dict(units=[dict(tag=1, alliance=1, unit_type=45, position=[0, 0],
                     orders=[dict(ability_id=320, target_world_space_pos=dict(x=5, y=5))]),
                     dict(tag=7, alliance=3, position=[5, 5], vespene_contents=2000)])
        self.assertEqual(claimed_geysers(state, {320: dict(is_building=True)}), {7})

    def test_completed_refinery_claims_its_still_observed_neutral_geyser(self):
        from src.learning.production_clearance import claimed_geysers
        # Native 09 retains both neutral geyser and owned Refinery at this position.
        state = dict(units=[
            dict(tag=4323278849, alliance=3, unit_type=343,
                 position=[26.5, 135.5], vespene_contents=1862),
            dict(tag=4352114690, alliance=1, unit_type=20,
                 position=[26.5, 135.5], vespene_contents=1862),
            dict(tag=7, alliance=3, unit_type=343,
                 position=[40, 120], vespene_contents=2000),
        ])
        self.assertEqual(claimed_geysers(state, {}), {4323278849})


class BuilderPathTests(unittest.IsolatedAsyncioTestCase):
    async def test_addon_pad_occupied_by_marine_is_withheld_despite_terrain_success(self):
        class Client:
            async def _execute(self, **kwargs):
                return pb.Response(query=query.ResponseQuery(placements=[query.ResponseQueryBuildingPlacement(result=1)]))
        state = dict(units=[dict(tag=1, alliance=1, unit_type=21, position=[130.5, 42.5]),
                           dict(tag=2, alliance=1, unit_type=48, position=[133, 42], radius=.375)], map_size=[176, 184])
        catalog = {3683: dict(friendly_name='Build Reactor', is_building=True),
                   319: dict(friendly_name='Build SupplyDepot', is_building=True)}
        commands, trace = await resolve_production_placement(Client(), Command(3683, (1,)), catalog, state, 38, [])
        self.assertEqual(commands, [])
        self.assertEqual(trace[0]['blocking_units'], [2])
        self.assertEqual(trace[0]['clearance_points'], [(133, 42)])
        state['units'][1]['is_flying'] = True
        commands, _ = await resolve_production_placement(Client(), Command(3683, (1,)), catalog, state, 38, [])
        self.assertEqual(len(commands), 1)

    async def test_expansion_command_does_not_move_twenty_tiles_off_its_resource_site(self):
        class Client:
            async def _execute(self, **kwargs):
                request = kwargs['query']
                return pb.Response(query=query.ResponseQuery(
                    placements=[query.ResponseQueryBuildingPlacement(result=44 if
                        (p.target_pos.x, p.target_pos.y) == (52.5, 113.5) else 1)
                        for p in request.placements],
                    pathing=[query.ResponseQueryPathing(distance=20) for _ in request.pathing]))
        state = dict(units=[dict(tag=1, alliance=1, unit_type=45, position=[31, 114])], map_size=[176, 184])
        commands, _ = await resolve_production_placement(Client(),
            Command(318, (1,), target_point=(52.5, 113.5)),
            {318: dict(friendly_name='Build CommandCenter', is_building=True, footprint_radius=2.5),
             319: dict(friendly_name='Build SupplyDepot', is_building=True, footprint_radius=1)},
            state, 18, [])
        self.assertEqual(commands, [])

    async def test_queries_and_commands_use_the_same_engine_grid_centers(self):
        class Client:
            async def _execute(self, **kwargs):
                request = kwargs['query']
                return pb.Response(query=query.ResponseQuery(
                    placements=[query.ResponseQueryBuildingPlacement(result=1) for _ in request.placements],
                    pathing=[query.ResponseQueryPathing(distance=20) for _ in request.pathing]))
        state = dict(units=[dict(tag=1, alliance=1, unit_type=45, position=[40, 130])], map_size=[176, 184])
        for ability, kind, radius, requested, actual in (
            (319, 19, 1, (39, 127.5), (39, 128)),
            (321, 21, 1.5, (63, 133.5), (63.5, 133.5)),
        ):
            catalog = {319: dict(friendly_name='Build SupplyDepot', is_building=True, footprint_radius=1),
                       ability: dict(friendly_name='Build Barracks' if kind == 21 else 'Build SupplyDepot',
                                     is_building=True, footprint_radius=radius)}
            commands, _ = await resolve_production_placement(Client(), Command(ability, (1,), target_point=requested), catalog, state, kind, [])
            self.assertEqual(commands[0].target_point, actual)

    async def test_legal_but_unreachable_site_is_replaced_by_a_reachable_site(self):
        class Client:
            async def _execute(self, **kwargs):
                request = kwargs['query']
                return pb.Response(query=query.ResponseQuery(
                    placements=[query.ResponseQueryBuildingPlacement(result=1 if
                        (p.target_pos.x, p.target_pos.y) in ((10, 10), (11, 10)) else 41)
                        for p in request.placements],
                    pathing=[query.ResponseQueryPathing(distance=20 if p.end_pos.x == 11 else 0)
                             for p in request.pathing]))
        command = Command(319, (1,), target_point=(10, 10))
        state = dict(units=[dict(tag=1, alliance=1, unit_type=45, position=[0, 0])], map_size=[64, 64])
        commands, _ = await resolve_production_placement(Client(), command,
            {319: dict(friendly_name='Build SupplyDepot', is_building=True, footprint_radius=1)},
            state, 19, [])
        self.assertEqual(commands[0].target_point, (11, 10))

    async def test_engine_rejection_is_recorded_without_claiming_a_path_failure(self):
        class Client:
            async def _execute(self, **kwargs):
                request = kwargs['query']
                return pb.Response(query=query.ResponseQuery(placements=[
                    query.ResponseQueryBuildingPlacement(result=3) for _ in request.placements]))
        command = Command(319, (1,), target_point=(10, 10))
        state = dict(units=[dict(tag=1, alliance=1, unit_type=45, position=[0, 0])], map_size=[64, 64])
        commands, trace = await resolve_production_placement(Client(), command,
            {319: dict(friendly_name='Build SupplyDepot', is_building=True, footprint_radius=1)}, state, 19, [])
        self.assertFalse(commands)
        self.assertEqual(trace[0]['rejected'], 'native_placement')
        self.assertEqual(trace[0]['placement_results'], {3: trace[0]['checked']})
        self.assertEqual(trace[0]['pathing_checked'], 0)

    async def test_crowded_original_seed_falls_back_to_owned_base_but_not_expansion_goal(self):
        class Client:
            async def _execute(self, **kwargs):
                request = kwargs['query']
                return pb.Response(query=query.ResponseQuery(
                    placements=[query.ResponseQueryBuildingPlacement(result=1 if
                        (p.target_pos.x, p.target_pos.y) == (49,49) else 44)
                        for p in request.placements],
                    pathing=[query.ResponseQueryPathing(distance=20) for _ in request.pathing]))
        state = dict(units=[dict(tag=1,alliance=1,unit_type=45,position=[0,0]),
                     dict(tag=2,alliance=1,unit_type=18,position=[48,48],build_progress=1)],map_size=[64,64])
        catalog = {319:dict(friendly_name='Build SupplyDepot',is_building=True,footprint_radius=1)}
        command = Command(319,(1,),target_point=(10,10))
        commands, trace = await resolve_production_placement(Client(),command,catalog,state,19,[])
        self.assertEqual(commands[0].target_point,(49,49))
        self.assertEqual(trace[-1]['base'],2)
        commands, _ = await resolve_production_placement(Client(),command,catalog,state,18,[])
        self.assertFalse(commands)
        for change in [dict(alliance=4),dict(build_progress=.5),dict(is_flying=True)]:
            state['units'][1].update(alliance=1,build_progress=1,is_flying=False)
            state['units'][1].update(change)
            commands, _ = await resolve_production_placement(Client(),command,catalog,state,19,[])
            self.assertFalse(commands)
