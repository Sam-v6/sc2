import unittest
from src.learning.production_clearance import reservations, clear_site


class ProductionClearanceTests(unittest.TestCase):
    def test_existing_producer_keeps_addon_pad_and_spawn_perimeter(self):
        state = dict(units=[dict(tag=1, alliance=1, unit_type=27, position=[10, 10])])
        reserved = reservations(state, {27: dict(footprint_radius=1.5)}, {})
        self.assertFalse(clear_site((12.5, 9.5), 1, reserved))
        self.assertFalse(clear_site((10, 13), 1, reserved))
        self.assertTrue(clear_site((10, 14), 1, reserved))

    def test_pending_builder_and_current_batch_footprints_are_reserved(self):
        state = dict(units=[dict(tag=1, alliance=1, unit_type=45, position=[0, 0],
                     orders=[dict(ability_id=319, target_world_space_pos=dict(x=20, y=20))])])
        reserved = reservations(state, {}, {319: dict(is_building=True, footprint_radius=1)})
        self.assertFalse(clear_site((20, 20), 1, reserved))
        self.assertTrue(clear_site((22, 20), 1, reserved))

    def test_unstarted_refinery_reserves_its_geyser(self):
        from src.learning.production_clearance import claimed_geysers
        state = dict(units=[dict(tag=1, alliance=1, unit_type=45, position=[0, 0],
                     orders=[dict(ability_id=320, target_world_space_pos=dict(x=5, y=5))]),
                     dict(tag=7, alliance=3, position=[5, 5], vespene_contents=2000)])
        self.assertEqual(claimed_geysers(state, {320: dict(is_building=True)}), {7})
