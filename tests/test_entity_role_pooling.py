import tempfile
from pathlib import Path
import unittest

import numpy as np

from src.learning.entity_encoder import JointEntityEncoder
from src.learning.entity_policy import JointEntityPolicy


class EntityRolePoolingTests(unittest.TestCase):
    def model(self):
        return JointEntityEncoder(6, 2, 2, 8, 12, hidden=4, seed=9, role_pooling=True)

    def inputs(self):
        return (
            np.array(
                [
                    [0.2, 0.3, 1, 0, 0, 1],
                    [0.7, 0.4, 0, 1, 0, 1],
                    [0.5, 0.2, 0, 0, 1, 1],
                    [0.1, 0.6, 0, 1, 0, 0],
                ],
                float,
            ),
            np.array([2, 3, 4, 3]),
            np.array([1, 1, 1, 0]),
            np.array([0.1, 0.2]),
            np.array([3, 4]),
            np.array([[0.2, 0.1], [0.3, 0.4]]),
        )

    def test_neutral_replication_cannot_dilute_the_owned_unit_summary(self):
        model = self.model()
        for p in model.parameters.values():
            p[:] = 0
        model.parameters["types"][2] = [0.2, 0.3, 0.4, 0.5]
        model.parameters["types"][4] = [-0.2, -0.3, -0.4, -0.5]
        model.parameters["pool"][:4] = np.eye(4)
        args = self.inputs()
        first = model.forward(*args)[0]
        repeated = list(args)
        repeated[0] = np.concatenate((args[0], np.repeat(args[0][2:3], 20, axis=0)))
        repeated[1] = np.concatenate((args[1], np.repeat(args[1][2:3], 20)))
        repeated[2] = np.concatenate((args[2], np.repeat(args[2][2:3], 20)))
        np.testing.assert_allclose(model.forward(*repeated)[0], first, atol=1e-7)
        # Counts are independently accessible, even when their mean is unchanged.
        model.parameters["pool"][2 * 5 + 4, 0] = 1
        self.assertNotEqual(model.forward(*args)[0][0], model.forward(*repeated)[0][0])

    def test_grouped_backward_matches_finite_differences(self):
        model = self.model()
        model.parameters = {k: v.astype(float) for k, v in model.parameters.items()}
        args = self.inputs()
        context, entities, cache = model.forward(*args)
        context_weight = np.array([0.2, -0.3, 0.4, 0.5])
        entity_weight = np.full_like(entities, 0.1)
        gradients = model.backward(cache, context_weight, entity_weight)
        for name, index in (
            ("entity", (0, 1)),
            ("pool", (4, 0)),
            ("pool", (17, 2)),
            ("types", (3, 1)),
            ("abilities", (1, 2)),
            ("history", (123, 0)),
        ):
            old = model.parameters[name][index]

            def loss(delta):
                model.parameters[name][index] = old + delta
                c, e, _ = model.forward(*args)
                return c @ context_weight + (e * entity_weight).sum()

            numerical = (loss(1e-6) - loss(-1e-6)) / 2e-6
            model.parameters[name][index] = old
            self.assertAlmostEqual(gradients[name][index], numerical, places=7)

    def test_checkpoint_roundtrip_and_entity_permutation_preserve_predictions(self):
        model = self.model()
        args = self.inputs()
        context, entities, _ = model.forward(*args)
        order = np.array([3, 1, 0, 2])
        permuted = (args[0][order], args[1][order], args[2][order], *args[3:])
        c, e, _ = model.forward(*permuted)
        np.testing.assert_allclose(c, context, atol=1e-7)
        np.testing.assert_allclose(e, entities[order], atol=1e-7)
        policy = JointEntityPolicy(model, (0, 1, 8))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "policy.npz"
            policy.save(path, {})
            loaded, _ = JointEntityPolicy.load(path)
        self.assertTrue(loaded.encoder.role_pooling)
        np.testing.assert_array_equal(loaded.encoder.forward(*args)[0], context)

    def test_float32_inputs_keep_float32_pool_and_context(self):
        model = self.model()
        args = list(self.inputs())
        for i in (0, 3, 5):
            args[i] = args[i].astype(np.float32)
        context, _, cache = model.forward(*args)
        self.assertEqual(context.dtype, np.float32)
        self.assertEqual(cache["pool_weights"].dtype, np.float32)

    def test_empty_groups_and_empty_entities_are_finite(self):
        model = self.model()
        args = list(self.inputs())
        args[0] = np.empty((0, 6))
        args[1] = args[2] = np.array([], int)
        context, entities, cache = model.forward(*args)
        self.assertTrue(np.isfinite(context).all())
        gradients = model.backward(cache, np.ones(4), entities)
        self.assertTrue(all(np.isfinite(v).all() for v in gradients.values()))
