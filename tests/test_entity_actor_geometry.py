import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.learning.entity_encoder import JointEntityEncoder
from src.learning.entity_policy import JointEntityPolicy
from tests import test_entity_relative_points as relative


class ActorGeometryTests(unittest.TestCase):
    def setUp(self):
        fixture = relative.RelativePointTests()
        fixture.setUp()
        self.inputs, self.label = fixture.inputs, fixture.label
        self.inputs["point_radii"] = np.full((3, 2), 5.0, dtype=np.float32)
        self.policy = JointEntityPolicy(
            JointEntityEncoder(3, 2, 2, 8, 12, hidden=4, seed=7),
            (0, 1, 8),
            seed=11,
            actor_geometry=True,
            refinement=True,
        )

    def test_zero_initialization_default_parity(self):
        legacy = JointEntityPolicy(
            JointEntityEncoder(3, 2, 2, 8, 12, hidden=4, seed=7),
            (0, 1, 8),
            seed=11,
            refinement=True,
        )
        for name, parameter in legacy.parameters.items():
            np.testing.assert_array_equal(parameter, self.policy.parameters[name])
        for name, value in legacy.scores(self.inputs, ability=3, actors=(0, 1)).items():
            np.testing.assert_array_equal(
                value, self.policy.scores(self.inputs, ability=3, actors=(0, 1))[name]
            )

    def test_geometry_is_relative_and_actor_scores_permute(self):
        self.policy.heads["actor_geometry"][:] = np.arange(16).reshape(4, 4) / 20
        a, cache = self.policy._forward(self.inputs, ability=3, actors=(0, 1))
        delta = (self.inputs["entity_positions"] - np.array([45.0, 35.0])) / 32
        np.testing.assert_allclose(
            cache["actor_geometry"], np.concatenate((delta, delta**2), axis=1)
        )
        shifted = dict(
            self.inputs,
            entity_positions=self.inputs["entity_positions"] + [123.0, -45.0],
        )
        _, changed = self.policy._forward(shifted, ability=3, actors=(0, 1))
        np.testing.assert_array_equal(
            cache["actor_geometry"], changed["actor_geometry"]
        )
        order = np.array([2, 0, 1])
        e = self.inputs["encoder"]
        permuted = dict(
            self.inputs,
            encoder=tuple([e[i][order] for i in range(3)] + list(e[3:])),
            entity_positions=self.inputs["entity_positions"][order],
            actor_mask=self.inputs["actor_mask"][order],
            target_mask=self.inputs["target_mask"][order],
        )
        b = self.policy.scores(permuted, ability=3, actors=(1, 2))
        np.testing.assert_allclose(a["actor"][order], b["actor"])

    def test_residual_and_shared_gradients(self):
        self.policy.heads["actor_geometry"][:] = np.arange(16).reshape(4, 4) / 40
        _, gradients = self.policy.loss_and_gradients(self.inputs, self.label)
        for name, index in [
            ("actor_geometry", (1, 2)),
            ("actor_geometry", (3, 0)),
            ("encoder.abilities", (3, 1)),
            ("encoder.entity", (1, 2)),
            ("encoder.pool", (2, 1)),
        ]:
            parameter = self.policy.parameters[name]
            original = float(parameter[index])
            step = 0.001
            parameter[index] = original + step
            high = self.policy.loss_and_gradients(self.inputs, self.label)[0]
            parameter[index] = original - step
            low = self.policy.loss_and_gradients(self.inputs, self.label)[0]
            parameter[index] = original
            self.assertAlmostEqual(
                gradients[name][index], (high - low) / (2 * step), delta=0.003
            )

    def test_geometry_can_prefer_an_interior_unit(self):
        inputs = dict(
            self.inputs,
            entity_positions=np.array([[0.0, 0.0], [32.0, 0.0], [64.0, 0.0]]),
            actor_mask=np.ones(3, bool),
        )
        self.policy.heads["actor"][:] = 0
        _, cache = self.policy._forward(inputs, ability=3, actors=(1,))
        context = cache["conditioned"]
        self.policy.heads["actor_geometry"][:] = np.outer(
            context / np.dot(context, context), [0.0, 0.0, -1.0, -1.0]
        )
        scores = self.policy.scores(inputs, ability=3, actors=(1,))
        self.assertEqual(int(np.argmax(scores["actor"])), 1)

    def test_checkpoint_flag_and_scores(self):
        self.policy.heads["actor_geometry"][:] = 0.25
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.npz"
            self.policy.save(path, {})
            loaded, _ = JointEntityPolicy.load(path)
            self.assertTrue(loaded.actor_geometry)
            np.testing.assert_array_equal(
                self.policy.scores(self.inputs, ability=3, actors=(0, 1))["actor"],
                loaded.scores(self.inputs, ability=3, actors=(0, 1))["actor"],
            )
