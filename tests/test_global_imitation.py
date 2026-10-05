import unittest
import numpy as np

try:
    from src.learning.global_imitation import (
        global_features,
        global_labels,
        select_group,
    )
except ImportError:
    global_features = global_labels = select_group = None


class GlobalImitationTests(unittest.TestCase):
    def state(self):
        return {
            "game_loop": 100,
            "player": {"minerals": 100},
            "units": [
                {
                    "tag": 1,
                    "alliance": 1,
                    "unit_type": 18,
                    "position": [10.0, 10.0, 0.0],
                },
                {
                    "tag": 2,
                    "alliance": 1,
                    "unit_type": 45,
                    "position": [12.0, 10.0, 0.0],
                },
                {
                    "tag": 3,
                    "alliance": 1,
                    "unit_type": 45,
                    "position": [30.0, 30.0, 0.0],
                },
            ],
        }

    def test_global_history_and_distant_visible_enemy_change_inputs(self):
        self.assertIsNotNone(global_features)
        state = self.state()
        types = [18, 45, 105]
        first, origin = global_features(state, types, 600)
        changed = dict(
            state, recent_commands=[{"ability": 524, "units": [1], "game_loop": 90}]
        )
        self.assertFalse(np.array_equal(first, global_features(changed, types, 600)[0]))
        changed = dict(
            state,
            units=state["units"]
            + [
                {
                    "tag": 4,
                    "unit_type": 105,
                    "alliance": 4,
                    "position": [100.0, 100.0, 0.0],
                    "health": 145.0,
                }
            ],
        )
        self.assertFalse(np.array_equal(first, global_features(changed, types, 600)[0]))
        np.testing.assert_allclose(origin, [10.0, 10.0])

    def test_group_selection_learns_unit_type_count_and_location_without_stored_tags(
        self,
    ):
        self.assertIsNotNone(select_group)
        state = self.state()
        types = [18, 45, 105]
        command = {
            "ability": 319,
            "units": [2],
            "target_point": [14.0, 14.0],
            "target_unit": None,
            "queue": False,
            "autocast": False,
        }
        labels, points = global_labels(command, state, types, [10.0, 10.0], 16)
        self.assertEqual(labels["actor_type"], 2)
        self.assertEqual(len(points), 5)
        output = {
            "actor_type": np.array([[0.0, 0.0, 10.0, 0.0]]),
            "point": np.array([points]),
        }
        group = select_group(
            state, output, {1: {524}, 2: {319}, 3: {319}}, 319, types, [10.0, 10.0]
        )
        self.assertEqual([u["tag"] for u in group], [2])
        command["units"] = [2, 3]
        _, points = global_labels(command, state, types, [10.0, 10.0], 16)
        output["point"] = np.array([points])
        self.assertEqual(
            {
                u["tag"]
                for u in select_group(
                    state, output, {2: {319}, 3: {319}}, 319, types, [10.0, 10.0]
                )
            },
            {2, 3},
        )


class CoordinateFrameTests(unittest.TestCase):
    def test_mirrored_spawns_share_features_and_action_coordinates(self):
        from src.learning.global_imitation import global_labels

        types = [18, 45, 105]
        own = {"tag": 1, "unit_type": 18, "alliance": 1, "position": [20.0, 20.0, 0.0]}
        worker = {
            "tag": 2,
            "unit_type": 45,
            "alliance": 1,
            "position": [22.0, 20.0, 0.0],
        }
        enemy = {
            "tag": 3,
            "unit_type": 105,
            "alliance": 4,
            "position": [30.0, 30.0, 0.0],
        }
        state = {
            "units": [own, worker, enemy],
            "player": {},
            "game_loop": 10,
            "map_size": [100.0, 100.0],
        }
        mirrored = dict(
            state,
            units=[
                dict(u, position=[100 - u["position"][0], 100 - u["position"][1], 0.0])
                for u in state["units"]
            ],
        )
        first, origin = global_features(state, types, 600, canonical=True)
        second, mirror_origin = global_features(mirrored, types, 600, canonical=True)
        np.testing.assert_allclose(first, second)
        command = {
            "ability": 319,
            "units": [2],
            "target_point": [25.0, 25.0],
            "target_unit": None,
            "queue": False,
            "autocast": False,
        }
        _, point = global_labels(command, state, types, origin, 16, canonical=True)
        _, mirror_point = global_labels(
            dict(command, target_point=[75.0, 75.0]),
            mirrored,
            types,
            mirror_origin,
            16,
            canonical=True,
        )
        np.testing.assert_allclose(point, mirror_point)
