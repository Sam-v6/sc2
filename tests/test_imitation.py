import tempfile
from pathlib import Path
import unittest
import numpy as np

try:
    from src.learning.imitation import FactorPolicy, unit_features, action_labels
except ImportError:
    FactorPolicy = unit_features = action_labels = None


class ImitationTests(unittest.TestCase):
    def test_projected_training_preserves_dense_updates_and_novel_live_features(self):
        dense = FactorPolicy(100, 3, [], seed=9)
        projected = FactorPolicy(100, 3, [], seed=9)
        x = np.zeros((4, 100), dtype=np.float32)
        x[:, 3] = [1.0, 0.0, 1.0, 0.0]
        x[:, 8] = 2.0
        columns = np.array([3, 8])
        labels = {k: np.zeros(4, dtype=int) for k in dense.sizes}
        labels["ability"] = np.array([1, 2, 1, 2])
        labels["target_type"][:] = -1
        for _ in range(5):
            dense.learn(x, labels, np.zeros((4, 2), dtype=np.float32))
            projected.learn(
                x[:, columns],
                labels,
                np.zeros((4, 2), dtype=np.float32),
                feature_indices=columns,
            )
        for k in dense.parameters:
            np.testing.assert_allclose(
                dense.parameters[k], projected.parameters[k], atol=1e-6
            )
        novel = x.copy()
        novel[:, 90] = 1.0
        np.testing.assert_allclose(
            dense.predict(novel)["ability"],
            projected.predict(novel)["ability"],
            atol=1e-6,
        )

    def test_sparse_input_product_matches_dense_for_single_and_batched_observations(
        self,
    ):
        from src.learning.imitation import input_product

        rng = np.random.default_rng(11)
        x = np.zeros((7, 200), dtype=np.float32)
        x[:, [3, 9, 190]] = rng.normal(size=(7, 3))
        weights = rng.normal(size=(200, 32)).astype(np.float32)
        np.testing.assert_allclose(input_product(x, weights), x @ weights, atol=1e-6)
        np.testing.assert_allclose(
            input_product(x[0], weights), x[0] @ weights, atol=1e-6
        )
        np.testing.assert_allclose(input_product(np.zeros_like(x), weights), 0.0)

    def test_sparse_adam_keeps_decay_for_dormant_previously_trained_input_rows(self):
        policy = FactorPolicy(100, 3, [], seed=7)
        policy.m["input"][90] = 0.5
        policy.v["input"][90] = 0.25
        before = policy.parameters["input"][90].copy()
        x = np.zeros((2, 100), dtype=np.float32)
        x[:, 3] = 1.0
        labels = {k: np.zeros(2, dtype=int) for k in policy.sizes}
        labels["target_type"][:] = -1
        policy.learn(x, labels, np.zeros((2, 2), dtype=np.float32))
        self.assertTrue(np.all(policy.parameters["input"][90] < before))
        np.testing.assert_allclose(policy.m["input"][90], 0.45)
        np.testing.assert_allclose(policy.v["input"][90], 0.24975)

    def test_entity_inputs_retain_type_health_cooldown_and_economy(self):
        self.assertIsNotNone(unit_features)
        own = {
            "tag": 1,
            "unit_type": 48,
            "alliance": 1,
            "position": [10.0, 10.0, 0.0],
            "health": 45.0,
            "health_max": 45.0,
        }
        enemy = {
            "tag": 2,
            "unit_type": 105,
            "alliance": 4,
            "position": [12.0, 10.0, 0.0],
            "health": 80.0,
            "health_max": 145.0,
        }
        state = {"units": [own, enemy], "player": {"minerals": 100}, "game_loop": 100}
        types = [45, 48, 105]
        a = unit_features(state, own, types)
        b = unit_features(dict(state, units=[own, dict(enemy, health=1.0)]), own, types)
        self.assertFalse(np.array_equal(a, b))
        self.assertFalse(
            np.array_equal(
                a, unit_features(state, dict(own, weapon_cooldown=10.0), types)
            )
        )
        self.assertFalse(
            np.array_equal(
                a, unit_features(dict(state, player={"minerals": 500}), own, types)
            )
        )

    def test_labels_keep_raw_action_arguments_without_persistent_target_tags(self):
        self.assertIsNotNone(action_labels)
        unit = {"tag": 1, "position": [10.0, 10.0, 0.0]}
        target = {
            "tag": 2,
            "unit_type": 105,
            "alliance": 4,
            "position": [15.0, 20.0, 0.0],
        }
        cmd = {
            "ability": 23,
            "units": [1],
            "target_unit": 2,
            "target_point": None,
            "queue": True,
            "autocast": False,
        }
        labels, point = action_labels(
            cmd, {"units": [unit, target]}, unit, [45, 48, 105], 16
        )
        self.assertEqual(labels["ability"], 23)
        self.assertEqual(labels["mode"], 2)
        self.assertEqual(labels["target_type"], 3)
        self.assertEqual(labels["alliance"], 4)
        self.assertEqual(labels["queue"], 1)
        np.testing.assert_allclose(point, [5 / 128, 10 / 128])
        unknown = dict(cmd, target_unit=999)
        labels, _ = action_labels(unknown, {"units": [unit]}, unit, [45, 48, 105], 16)
        self.assertEqual(labels["ability"], 23)
        self.assertEqual(labels["target_type"], -1)

    def test_factor_learning_reduces_loss_and_checkpoint_reproduces_outputs(self):
        self.assertIsNotNone(FactorPolicy)
        policy = FactorPolicy(3, 3, [45, 48], seed=7)
        x = np.array(
            [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            dtype=np.float32,
        )
        y = {name: np.zeros(4, dtype=int) for name in policy.sizes}
        y["ability"] = np.array([1, 2, 1, 2])
        y["target_type"][:] = -1
        points = np.zeros((4, 2), dtype=np.float32)
        before = policy.loss(x, y, points)
        for _ in range(150):
            policy.learn(x, y, points, rate=0.01)
        self.assertLess(policy.loss(x, y, points), before * 0.25)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "policy.npz"
            policy.save(path, {"source": "test"})
            loaded = FactorPolicy.load(path)
            for name in policy.sizes:
                np.testing.assert_allclose(
                    policy.predict(x)[name], loaded.predict(x)[name]
                )

    def test_unknown_targets_do_not_create_false_point_regression_labels(self):
        unit = {"tag": 1, "position": [10.0, 10.0, 0.0]}
        command = {
            "ability": 23,
            "units": [1],
            "target_unit": 99,
            "target_point": None,
            "queue": False,
            "autocast": False,
        }
        labels, _ = action_labels(command, {"units": [unit]}, unit, [48], 16)
        self.assertEqual(labels.get("point_valid"), 0)

    def test_group_weighting_does_not_multiply_army_command_influence(self):
        policy = FactorPolicy(2, 3, [48], seed=7)
        x = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        y = {name: np.zeros(2, dtype=int) for name in policy.sizes}
        y["ability"] = np.array([1, 2])
        y["target_type"][:] = -1
        points = np.zeros((2, 2), dtype=np.float32)
        expected, gradients = policy.gradients(x, y, points)
        expanded = np.array([0, 0, 0, 1])
        actual, group_gradients = policy.gradients(
            x[expanded],
            {k: v[expanded] for k, v in y.items()},
            points[expanded],
            weights=np.array([1 / 3, 1 / 3, 1 / 3, 1.0]),
        )
        self.assertAlmostEqual(expected, actual, places=5)
        for name in gradients:
            np.testing.assert_allclose(
                gradients[name], group_gradients[name], atol=1e-6
            )

    def test_argument_heads_condition_on_command_without_leaking_into_command_choice(
        self,
    ):
        policy = FactorPolicy(3, 3, [45, 48], seed=7, autoregressive=True)
        policy.parameters["ability_embedding"][1] = 0.5
        policy.parameters["ability_embedding"][2] = -0.5
        x = np.ones((1, 3), dtype=np.float32)
        first = policy.predict(x, abilities=np.array([1]))
        second = policy.predict(x, abilities=np.array([2]))
        np.testing.assert_array_equal(first["ability"], second["ability"])
        self.assertFalse(np.array_equal(first["mode"], second["mode"]))
        y = {name: np.zeros(1, dtype=int) for name in policy.sizes}
        y["ability"][0] = 1
        y["target_type"][0] = -1
        points = np.zeros((1, 2), dtype=np.float32)
        _, grad = policy.gradients(x, y, points)
        epsilon = 0.001
        original = policy.parameters["ability_embedding"][1, 0].copy()
        policy.parameters["ability_embedding"][1, 0] = original + epsilon
        high = policy.loss(x, y, points)
        policy.parameters["ability_embedding"][1, 0] = original - epsilon
        low = policy.loss(x, y, points)
        policy.parameters["ability_embedding"][1, 0] = original
        self.assertAlmostEqual(
            float(grad["ability_embedding"][1, 0]),
            (high - low) / (2 * epsilon),
            places=3,
        )


class AbilityBalancingTests(unittest.TestCase):
    def test_rare_issued_commands_receive_more_weight_without_changing_group_totals(
        self,
    ):
        from src.learning.imitation_train import balance_abilities

        ability = np.array([1, 1, 1, 319])
        weights = balance_abilities(ability, np.ones(4))
        self.assertAlmostEqual(weights.sum(), 4.0)
        self.assertGreater(weights[3], weights[0])
        self.assertAlmostEqual(weights[3] / weights[0], np.sqrt(3))


class SpatialLossTests(unittest.TestCase):
    def test_spatial_loss_uses_bounded_gradients_and_matches_finite_difference(self):
        policy = FactorPolicy(2, 3, [45, 48], seed=7, point_dimensions=5)
        x = np.zeros((1, 2), dtype=np.float32)
        labels = {k: np.zeros(1, dtype=int) for k in policy.sizes}
        labels["mode"][0] = 1
        labels["point_valid"] = np.ones(1, dtype=int)
        policy.parameters["point_bias"][0] = 1.0
        points = np.zeros((1, 5), dtype=np.float32)
        _, grad = policy.gradients(x, labels, points)
        original = policy.parameters["point_bias"][0].copy()
        eps = 0.001
        policy.parameters["point_bias"][0] = original + eps
        high = policy.loss(x, labels, points)
        policy.parameters["point_bias"][0] = original - eps
        low = policy.loss(x, labels, points)
        policy.parameters["point_bias"][0] = original
        self.assertAlmostEqual(float(grad["point_bias"][0]), 5.0, places=5)
        self.assertAlmostEqual(
            float(grad["point_bias"][0]), (high - low) / (2 * eps), places=3
        )
