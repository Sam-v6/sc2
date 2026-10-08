import unittest
import numpy as np


class TargetSelectionTests(unittest.TestCase):
    def state(self):
        return {
            "map_size": [100, 100],
            "recent_commands": [],
            "units": [
                {"tag": 1, "unit_type": 48, "alliance": 1, "position": [10, 10]},
                {"tag": 2, "unit_type": 105, "alliance": 4, "position": [15, 10]},
                {"tag": 3, "unit_type": 341, "alliance": 3, "position": [20, 10]},
                {
                    "tag": 4,
                    "unit_type": 105,
                    "alliance": 4,
                    "position": [25, 10],
                    "observed": False,
                },
            ],
            "owned_memory": [
                {
                    "tag": 5,
                    "unit_type": 48,
                    "alliance": 1,
                    "position": [30, 10],
                    "observed": False,
                }
            ],
        }

    def test_candidate_identity_and_no_hidden_targets(self):
        from src.learning.target_selection import target_features

        state = self.state()
        units, rows = target_features(
            state, [state["units"][0]], 23, [48, 105, 341], 30, [10, 10]
        )
        self.assertEqual([u["tag"] for u in units], [1, 2, 3])
        self.assertEqual(len(rows), 3)
        self.assertTrue(np.isfinite(rows).all())
        # Ability identity must be explicit, independently of a frozen macro.
        _, alternate = target_features(
            state, [state["units"][0]], 16, [48, 105, 341], 30, [10, 10]
        )
        self.assertFalse(np.array_equal(rows, alternate))

    def test_geometry_and_scores_do_not_depend_on_tags_or_list_order(self):
        from src.learning.target_selection import target_features, select_target

        state = self.state()
        group = [state["units"][0]]
        units, rows = target_features(state, group, 23, [48, 105, 341], 30, [10, 10])
        state["units"] = list(reversed(state["units"]))
        for unit in state["units"]:
            unit["tag"] += 100
        reversed_units, reversed_rows = target_features(
            state, group, 23, [48, 105, 341], 30, [10, 10]
        )
        np.testing.assert_allclose(rows, reversed_rows[::-1])

        class Scorer:
            def predict(self, x):
                return {"ability": np.array([[0, 1], [0, 5], [0, 2]])}

        self.assertEqual(select_target(Scorer(), reversed_rows, reversed_units), 102)
