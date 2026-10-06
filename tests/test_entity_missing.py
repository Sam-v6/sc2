import copy
import unittest

import numpy as np

from src.learning.entity_examples import state_inputs


class MissingFieldInputsTests(unittest.TestCase):
    def setUp(self):
        self.state = dict(
            game_loop=12,
            map_size=[200, 184],
            player=dict(minerals=50, food_used=0),
            units=[
                dict(
                    tag=1,
                    unit_type=2,
                    alliance=1,
                    position=[10, 20, 0],
                    energy=0,
                    orders=[],
                )
            ],
            memory=[dict(tag=2, unit_type=3, position=[30, 40, 0], last_seen_loop=10)],
            upgrades=[],
            recent_commands=[],
        )

    def encode(self, state):
        return state_inputs(state, 8, 12, missing_fields=True)["encoder"]

    def test_unknown_energy_differs_from_observed_zero_without_reading_its_value(self):
        known = self.encode(self.state)
        partial = copy.deepcopy(self.state)
        partial["unknown_fields"] = dict(
            units=["energy"],
            player=["food_used"],
            world=["command_history", "upgrades"],
        )
        partial["units"][0]["energy"] = 999
        unknown = self.encode(partial)
        self.assertEqual(known[0][0, 10], 0)
        self.assertEqual(unknown[0][0, 10], 0)
        self.assertEqual(known[0][0, 94 + 10], 1)
        self.assertEqual(unknown[0][0, 94 + 10], 0)
        self.assertEqual(known[3][13 + 6], 1)
        self.assertEqual(unknown[3][13 + 6], 0)
        partial["units"][0]["energy"] = float("nan")
        np.testing.assert_array_equal(self.encode(partial)[0], unknown[0])

    def test_memory_dynamic_values_are_unknown_and_native_legacy_is_unchanged(self):
        legacy = state_inputs(self.state, 8, 12)["encoder"]
        masked = self.encode(self.state)
        np.testing.assert_array_equal(masked[0][0, :94], legacy[0][0])
        self.assertEqual(masked[0][1, 24], 0)
        np.testing.assert_array_equal(
            state_inputs(self.state, 8, 12)["encoder"][0], legacy[0]
        )
        np.testing.assert_array_equal(masked[3][:13], legacy[3])
        self.assertEqual(masked[0][1, 94 + 7], 0)
        self.assertEqual(masked[0][1, 94], 1)
        self.assertEqual(masked[0].shape, (2, 188))
        self.assertEqual(masked[3].shape, (26,))

    def test_truncated_order_count_and_point_precision_are_not_claimed_exact(self):
        partial = copy.deepcopy(self.state)
        partial["unknown_fields"] = dict(
            units=[
                "orders_beyond_four",
                "order_target_point_precision",
                "order_target_presence_at_origin",
            ]
        )
        partial["units"][0]["orders"] = [
            dict(ability_id=3, progress=0, target_world_space_pos=dict(x=5, y=6))
        ] * 4
        encoded = self.encode(partial)[0][0]
        self.assertEqual(encoded[94 + 19], 0)
        self.assertEqual(encoded[94 + 21], 0)
        self.assertEqual(encoded[21], 0)
        self.assertEqual(encoded[94 + 24], 1)

    def test_unknown_history_cannot_be_used_as_verified_command_references(self):
        partial = copy.deepcopy(self.state)
        partial["unknown_fields"] = dict(world=["command_history"])
        partial["recent_commands"] = [dict(game_loop=10, ability=3, units=[1])]
        with self.assertRaisesRegex(ValueError, "history"):
            self.encode(partial)

    def test_event_slots_keep_gaps_without_using_unknown_action_details(self):
        partial = copy.deepcopy(self.state)
        partial["unknown_fields"] = dict(world=["command_history"])
        partial["history_quality"] = "event_slots"
        partial["recent_commands"] = [
            dict(game_loop=8, ability=3, units=[1], verified=True),
            dict(
                game_loop=10,
                ability=11,
                units=[1],
                target_point=[999, 999],
                queue=True,
                unknown=True,
            ),
        ]
        encoded = self.encode(partial)
        np.testing.assert_array_equal(encoded[4], [3, 0])
        np.testing.assert_array_equal(encoded[5][1, :8], np.zeros(8))
        self.assertAlmostEqual(encoded[5][1, 8], 2 / 1344)
        self.assertEqual(encoded[0][0, 94 + 30], 1)  # Known empty padding.
        self.assertEqual(encoded[0][0, 30 + 30 * 2], 1)
        self.assertEqual(encoded[0][0, 94 + 30 + 30 * 2], 1)
        self.assertEqual(encoded[0][0, 30 + 31 * 2], 0)
        self.assertEqual(encoded[0][0, 94 + 30 + 31 * 2], 0)
        partial["recent_commands"][0].pop("verified")
        with self.assertRaisesRegex(ValueError, "verified"):
            self.encode(partial)
