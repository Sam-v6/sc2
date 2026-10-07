import unittest
from src.learning.production_clearance import reservations, clear_site
from src.learning.production_clearance import resolve_production_placement
from src.learning.gameplay import Command
from s2clientprotocol import sc2api_pb2 as pb, query_pb2 as query


class ProductionClearanceTests(unittest.TestCase):
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


class BuilderPathTests(unittest.IsolatedAsyncioTestCase):
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
