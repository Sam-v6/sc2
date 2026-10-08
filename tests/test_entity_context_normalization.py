import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.learning.entity_encoder import JointEntityEncoder
from src.learning.entity_policy import JointEntityPolicy


class ContextNormalizationTests(unittest.TestCase):
    def inputs(self):
        return (
            np.array([[0.2, 0.5, -0.1], [0.7, -0.2, 0.4]]),
            np.array([2, 2]),
            np.array([3, 3]),
            np.array([0.1, -0.3]),
            np.array([1, 4, 3, 9]),
            np.array([[0, 0.1], [1, 0.2], [0, 0.3], [1, 0.4]]),
        )

    def encoder(self, **kwargs):
        return JointEntityEncoder(3, 2, 2, 8, 12, hidden=4, seed=7, **kwargs)

    def test_disabled_flag_preserves_initialization_outputs_and_gradients(self):
        default = self.encoder()
        disabled = self.encoder(context_layer_norm=False)
        for name, parameter in default.parameters.items():
            np.testing.assert_array_equal(parameter, disabled.parameters[name])
        c, e, cache = default.forward(*self.inputs())
        dc, de, other = disabled.forward(*self.inputs())
        np.testing.assert_array_equal(c, dc)
        np.testing.assert_array_equal(e, de)
        gradients = default.backward(cache, np.ones(4), np.ones((2, 4)))
        changed = disabled.backward(other, np.ones(4), np.ones((2, 4)))
        for name in gradients:
            np.testing.assert_array_equal(gradients[name], changed[name])

    def check_gradients(self, constant=False):
        model = self.encoder(context_layer_norm=True)
        model.parameters = {
            k: v.astype(np.float64) for k, v in model.parameters.items()
        }
        if constant:
            for name in ("scene", "pool", "history"):
                model.parameters[name][:] = 0.2
            model.parameters["context_bias"][:] = 0.3
        inputs = self.inputs()
        weight = np.array([0.3, -0.2, 0.7, -0.1])
        context, entities, cache = model.forward(*inputs)
        self.assertTrue(np.isfinite(context).all())
        gradients = model.backward(cache, weight, np.zeros_like(entities))
        for name, index in {
            "scene": (0, 2),
            "pool": (1, 0),
            "history": (112, 1),
            "context_bias": (1,),
            "entity": (0, 1),
            "history_roles": (1, 2),
            "abilities": (3, 0),
        }.items():
            with self.subTest(parameter=name, constant=constant):
                parameter = model.parameters[name]
                value = parameter[index]
                epsilon = 1e-7
                parameter[index] = value + epsilon
                plus = model.forward(*inputs)[0] @ weight
                parameter[index] = value - epsilon
                minus = model.forward(*inputs)[0] @ weight
                parameter[index] = value
                numeric = (plus - minus) / (2 * epsilon)
                np.testing.assert_allclose(
                    gradients[name][index], numeric, rtol=1e-5, atol=1e-6
                )

    def test_all_context_branches_have_correct_derivatives(self):
        self.check_gradients()

    def test_constant_projection_has_finite_correct_derivatives(self):
        self.check_gradients(constant=True)

    def test_fixed_normalization_removes_common_shift(self):
        model = self.encoder(context_layer_norm=True)
        before = model.forward(*self.inputs())[0]
        model.parameters["context_bias"] += 20
        after = model.forward(*self.inputs())[0]
        np.testing.assert_allclose(before, after, atol=2e-6)

    def test_checkpoint_preserves_opt_in_and_absent_flag_defaults_false(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.npz"
            for enabled in (True, False):
                policy = JointEntityPolicy(
                    self.encoder(context_layer_norm=enabled), [0, 1]
                )
                policy.save(path, {})
                loaded, _ = JointEntityPolicy.load(path)
                self.assertEqual(loaded.encoder.context_layer_norm, enabled)
                np.testing.assert_array_equal(
                    policy.encoder.forward(*self.inputs())[0],
                    loaded.encoder.forward(*self.inputs())[0],
                )
            with np.load(path, allow_pickle=False) as archive:
                data = {name: archive[name] for name in archive.files}
            import json

            configuration = json.loads(str(data["configuration"]))
            del configuration["context_layer_norm"]
            data["configuration"] = json.dumps(configuration)
            np.savez(path, **data)
            loaded, _ = JointEntityPolicy.load(path)
            self.assertFalse(loaded.encoder.context_layer_norm)
