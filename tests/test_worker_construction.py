import unittest

import numpy as np

from src.learning import actor_selection


class WorkerConstructionTests(unittest.TestCase):
    def setUp(self):
        self.worker = {
            "tag": 1,
            "alliance": 1,
            "unit_type": 45,
            "position": [10.0, 10.0, 0.0],
            "orders": [
                {"ability_id": 321, "target_world_space_pos": {"x": 13.0, "y": 14.0}}
            ],
        }
        self.foundation = {
            "tag": 2,
            "alliance": 1,
            "unit_type": 21,
            "position": [13.0, 14.0, 0.0],
            "build_progress": 0.25,
        }
        self.state = {
            "units": [self.worker],
            "owned_memory": [],
            "player": {},
            "game_loop": 100,
            "map_size": [100, 100],
        }
        self.products = {"321": [21], "320": [20]}

    def test_distinguishes_walking_to_target_from_visible_construction(self):
        # Losing this distinction would reproduce the native interruption.
        cue = actor_selection.worker_construction_features
        np.testing.assert_allclose(
            cue(self.state, self.worker, self.products), [1, 1, 0, 0, 5 / 32]
        )
        self.state["units"].append(self.foundation)
        np.testing.assert_allclose(
            cue(self.state, self.worker, self.products), [1, 1, 1, 0.25, 5 / 32]
        )

    def test_does_not_infer_foundations_from_enemy_snapshot_or_memory(self):
        cue = actor_selection.worker_construction_features
        self.state["owned_memory"] = [self.foundation]
        for changes in (
            {"alliance": 4},
            {"display_type": 2},
            {"observed": False},
            {"unit_type": 19},
            {"position": [30, 30, 0]},
        ):
            with self.subTest(changes=changes):
                self.state["units"] = [self.worker, dict(self.foundation, **changes)]
                np.testing.assert_allclose(
                    cue(self.state, self.worker, self.products), [1, 1, 0, 0, 5 / 32]
                )

    def test_gas_target_requires_observed_target_and_nonbuilders_are_zero(self):
        cue = actor_selection.worker_construction_features
        worker = dict(self.worker, orders=[{"ability_id": 320, "target_unit_tag": 3}])
        np.testing.assert_array_equal(
            cue(self.state, worker, self.products), [1, 0, 0, 0, 0]
        )
        self.state["units"] += [
            dict(self.foundation, tag=3, alliance=3, unit_type=342),
            dict(self.foundation, unit_type=20),
        ]
        np.testing.assert_allclose(
            cue(self.state, worker, self.products), [1, 1, 1, 0.25, 5 / 32]
        )
        for unit in (
            dict(worker, unit_type=21),
            dict(worker, orders=[]),
            dict(worker, orders=[{"ability_id": 295}]),
        ):
            np.testing.assert_array_equal(
                cue(self.state, unit, self.products), np.zeros(5)
            )

    def test_opt_in_preserves_legacy_features_and_group_cues(self):
        args = (self.state, self.worker, 0, [21, 45], 600, [10, 10], np.zeros(32))
        legacy = actor_selection.actor_features(*args)
        enhanced = actor_selection.actor_features(*args, build_products=self.products)
        np.testing.assert_array_equal(enhanced[:-5], legacy)
        np.testing.assert_allclose(enhanced[-5:], [1, 1, 0, 0, 5 / 32])
        self.state["units"].append(self.foundation)
        group_args = (
            self.state,
            [self.worker, self.foundation],
            [21, 45],
            600,
            [10, 10],
            np.zeros(32),
        )
        group = actor_selection.group_features(
            *group_args, build_products=self.products
        )
        np.testing.assert_allclose(group[-6:-1], [0.5, 0.5, 0.5, 0.125, 2.5 / 32])

    def test_catalogue_maps_only_terran_construction_products(self):
        data = {
            "abilities": [
                {"ability_id": 321, "friendly_name": "Build Barracks"},
                {"ability_id": 524, "friendly_name": "Train SCV"},
                {"ability_id": 880, "friendly_name": "Build Pylon"},
            ],
            "units": [
                {"unit_id": 21, "ability_id": 321, "race": 1},
                {"unit_id": 45, "ability_id": 524, "race": 1},
                {"unit_id": 60, "ability_id": 880, "race": 3},
            ],
        }
        self.assertEqual(actor_selection.construction_products(data), {"321": [21]})
