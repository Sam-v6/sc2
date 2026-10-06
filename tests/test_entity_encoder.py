import unittest

import numpy as np

try:
    from src.learning.entity_encoder import JointEntityEncoder
except ImportError:
    JointEntityEncoder = None


class EntityEncoderTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(JointEntityEncoder, "shared entity encoder is missing")
        self.model = JointEntityEncoder(3, 2, 2, 8, 12, hidden=4, seed=7)
        self.entities = np.array([[0.2, 0.5, -0.1], [0.7, -0.2, 0.4]])
        self.types = np.array([2, 2])
        self.orders = np.array([3, 3])
        self.scene = np.array([0.1, -0.3])
        self.history = np.array([1, 4, 3, 9])
        self.roles = np.array([[0, 0.1], [1, 0.2], [0, 0.3], [1, 0.4]])

    def forward(self, permutation=None):
        p = np.arange(2) if permutation is None else permutation
        return self.model.forward(
            self.entities[p],
            self.types[p],
            self.orders[p],
            self.scene,
            self.history,
            self.roles,
        )

    def test_entity_order_only_permutes_entity_embeddings(self):
        context, entities, _ = self.forward()
        changed, permuted, _ = self.forward(np.array([1, 0]))
        np.testing.assert_allclose(changed, context, atol=1e-7)
        np.testing.assert_allclose(permuted, entities[[1, 0]], atol=1e-7)

    def test_oldest_of_32_commands_affects_context(self):
        history = np.array([1] + [4] * 31)
        roles = np.tile([0.0, 0.1], (32, 1))
        context, _, _ = self.model.forward(
            self.entities, self.types, self.orders, self.scene, history, roles
        )
        history[0] = 10
        changed, _, _ = self.model.forward(
            self.entities, self.types, self.orders, self.scene, history, roles
        )
        self.assertGreater(np.linalg.norm(context - changed), 1e-5)

    def test_categorical_entity_rows_cannot_silently_broadcast(self):
        with self.assertRaises(ValueError):
            self.model.forward(
                self.entities,
                np.array([2]),
                self.orders,
                self.scene,
                self.history,
                self.roles,
            )

    def test_history_roles_require_one_row_per_command(self):
        with self.assertRaises(ValueError):
            self.model.forward(
                self.entities,
                self.types,
                self.orders,
                self.scene,
                self.history,
                self.roles[:1],
            )

    def test_empty_entities_and_history_still_have_finite_scene_context(self):
        context, entities, cache = self.model.forward(
            np.empty((0, 3)),
            np.array([], dtype=int),
            np.array([], dtype=int),
            self.scene,
            np.array([], dtype=int),
            np.empty((0, 2)),
        )
        self.assertEqual(entities.shape, (0, 4))
        self.assertTrue(np.isfinite(context).all())
        gradients = self.model.backward(cache, np.ones(4), np.empty((0, 4)))
        self.assertTrue(all(np.isfinite(g).all() for g in gradients.values()))
        self.assertGreater(np.linalg.norm(gradients["scene"]), 0)

    def check_gradients(self, context_weight, entity_weight):
        # Double precision isolates differentiation from float32 rounding.
        self.model.parameters = {
            k: v.astype(np.float64) for k, v in self.model.parameters.items()
        }
        context, entities, cache = self.forward()
        gradients = self.model.backward(cache, context_weight, entity_weight)
        for name, indices in {
            "entity": [(0, 1)],
            "types": [(2, 1)],
            "abilities": [(3, 0), (1, 2)],
            "scene": [(0, 2)],
            "pool": [(1, 0)],
            "history": [(112, 1)],
            "history_roles": [(1, 2)],
            "entity_bias": [(2,)],
            "context_bias": [(1,)],
            "history_bias": [(0,)],
        }.items():
            for index in indices:
                with self.subTest(parameter=name, index=index):
                    value = self.model.parameters[name][index]

                    def loss(delta):
                        self.model.parameters[name][index] = value + delta
                        c, e, _ = self.forward()
                        return c @ context_weight + (e * entity_weight).sum()

                    numerical = (loss(1e-6) - loss(-1e-6)) / 2e-6
                    self.model.parameters[name][index] = value
                    self.assertAlmostEqual(gradients[name][index], numerical, places=7)

    def test_context_losses_backpropagate_through_entities_and_full_history(self):
        self.check_gradients(np.array([0.3, -0.2, 0.7, -0.1]), np.zeros((2, 4)))

    def test_individual_entity_losses_train_shared_type_and_order_embeddings(self):
        self.check_gradients(
            np.zeros(4), np.array([[0.4, -0.1, 0.3, 0.2], [-0.2, 0.5, -0.3, 0.1]])
        )


if __name__ == "__main__":
    unittest.main()
