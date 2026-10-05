import unittest
import numpy as np
from src.learning.actor_selection import select_actors, actor_features, group_features


class ActorSelectionTests(unittest.TestCase):
    def test_arguments_see_the_actual_selected_mixed_group(self):
        units = [
            {"tag": 1, "alliance": 1, "unit_type": 18, "position": [20.0, 20.0, 0.0]},
            {"tag": 2, "alliance": 1, "unit_type": 45, "position": [25.0, 20.0, 0.0]},
        ]
        state = {
            "units": units,
            "owned_memory": [],
            "game_loop": 0,
            "player": {},
            "map_size": [100.0, 100.0],
        }
        cc = group_features(state, units[:1], [18, 45], 600, [20.0, 20.0], np.zeros(32))
        mixed = group_features(state, units, [18, 45], 600, [20.0, 20.0], np.zeros(32))
        scv = group_features(
            state, units[1:], [18, 45], 600, [20.0, 20.0], np.zeros(32)
        )
        self.assertFalse(np.array_equal(cc, scv))
        np.testing.assert_allclose(mixed[:-1], (cc[:-1] + scv[:-1]) / 2)
        self.assertGreater(mixed[-1], cc[-1])

    def test_membership_selects_arbitrary_mixed_groups_with_engine_legality(self):
        actors = [
            {"tag": 1, "unit_type": 18},
            {"tag": 2, "unit_type": 45},
            {"tag": 3, "unit_type": 45},
        ]
        logits = np.array([[0.0, 4.0], [0.0, 4.0], [4.0, 0.0]])
        group = select_actors(actors, logits, {1: {1}, 2: {1}, 3: {1}}, 1)
        self.assertEqual([u["tag"] for u in group], [1, 2])
        group = select_actors(actors, logits, {1: set(), 2: {1}, 3: {1}}, 1)
        self.assertEqual([u["tag"] for u in group], [2])

    def test_empty_membership_falls_back_to_best_current_legal_actor(self):
        actors = [{"tag": 1}, {"tag": 2}]
        logits = np.array([[4.0, 0.0], [2.0, 0.0]])
        self.assertEqual(
            select_actors(actors, logits, {1: {23}, 2: {23}}, 23), [actors[1]]
        )
        self.assertEqual(select_actors(actors, logits, {}, 23), [])

    def test_actor_features_preserve_ongoing_order_ability_and_causal_index(self):
        units = [
            {"tag": 1, "alliance": 1, "unit_type": 18, "position": [20.0, 20.0, 0.0]},
            {"tag": 2, "alliance": 1, "unit_type": 45, "position": [25.0, 20.0, 0.0]},
        ]
        state = {
            "units": units,
            "game_loop": 10,
            "player": {},
            "map_size": [100.0, 100.0],
        }
        first = actor_features(
            state, units[1], 1, [18, 45], 600, [20.0, 20.0], np.zeros(32)
        )
        other = actor_features(
            state,
            dict(units[1], orders=[{"ability_id": 319}]),
            1,
            [18, 45],
            600,
            [20.0, 20.0],
            np.zeros(32),
        )
        self.assertFalse(np.array_equal(first, other))
        self.assertFalse(
            np.array_equal(
                first,
                actor_features(
                    state, units[1], 2, [18, 45], 600, [20.0, 20.0], np.zeros(32)
                ),
            )
        )
