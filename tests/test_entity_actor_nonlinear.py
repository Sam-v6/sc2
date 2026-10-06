import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.learning.entity_encoder import JointEntityEncoder
from src.learning.entity_policy import JointEntityPolicy
from tests import test_entity_actor_geometry as geometry


class NonlinearActorTests(unittest.TestCase):
    def setUp(self):
        fixture = geometry.ActorGeometryTests()
        fixture.setUp()
        self.inputs, self.label = fixture.inputs, fixture.label
        self.policy = JointEntityPolicy(
            JointEntityEncoder(3, 2, 2, 8, 12, hidden=4, seed=7),
            (0, 1, 8),
            seed=11,
            actor_geometry=True,
            actor_nonlinear=True,
            refinement=True,
        )
        self.baseline = fixture.policy

    def test_zero_residual_preserves_parameters_and_scores(self):
        for name, value in self.baseline.parameters.items():
            np.testing.assert_array_equal(value, self.policy.parameters[name])
        for name, value in self.baseline.scores(self.inputs, ability=3).items():
            np.testing.assert_array_equal(
                value, self.policy.scores(self.inputs, ability=3)[name]
            )

    def test_full_loss_residual_and_shared_gradients(self):
        self.policy.heads["actor_nonlinear_output"][:] = np.linspace(-0.2, 0.3, 32)
        _, gradients = self.policy.loss_and_gradients(self.inputs, self.label)
        for name, index in [
            ("actor_nonlinear_entity", (1, 2)),
            ("actor_nonlinear_entity", (6, 3)),
            ("actor_nonlinear_context", (2, 4)),
            ("actor_nonlinear_bias", (5,)),
            ("actor_nonlinear_output", (7,)),
            ("encoder.entity", (1, 2)),
            ("encoder.abilities", (3, 1)),
            ("encoder.pool", (2, 1)),
            ("actor", (1, 2)),
        ]:
            p = self.policy.parameters[name]
            original = float(p[index])
            step = 0.001
            p[index] = original + step
            high = self.policy.loss_and_gradients(self.inputs, self.label)[0]
            p[index] = original - step
            low = self.policy.loss_and_gradients(self.inputs, self.label)[0]
            p[index] = original
            self.assertAlmostEqual(
                gradients[name][index], (high - low) / (2 * step), delta=0.003
            )

    def test_context_can_move_interior_preference(self):
        x = dict(
            self.inputs,
            entity_positions=np.array([[0.0, 0.0], [32.0, 0.0], [64.0, 0.0]]),
            actor_mask=np.ones(3, bool),
        )
        p = self.policy.heads
        p["actor"][:] = 0
        for name in (
            "actor_nonlinear_entity",
            "actor_nonlinear_context",
            "actor_nonlinear_bias",
            "actor_nonlinear_output",
        ):
            p[name][:] = 0
        c3 = self.policy._forward(x, ability=3)[1]["conditioned"]
        c4 = self.policy._forward(x, ability=4)[1]["conditioned"]
        direction = -10 * (c4 - c3) / np.dot(c4 - c3, c4 - c3)
        p["actor_nonlinear_entity"][4, :2] = 10
        p["actor_nonlinear_context"][:, :2] = direction[:, None]
        p["actor_nonlinear_bias"][:2] = [
            5 - np.dot(c3, direction),
            -5 - np.dot(c3, direction),
        ]
        p["actor_nonlinear_output"][:2] = [1, -1]
        self.assertEqual(int(np.argmax(self.policy.scores(x, ability=3)["actor"])), 1)
        self.assertEqual(int(np.argmax(self.policy.scores(x, ability=4)["actor"])), 2)

    def test_permutation_and_checkpoint(self):
        self.policy.heads["actor_nonlinear_output"][:] = 0.2
        a = self.policy.scores(self.inputs, ability=3, actors=(0, 1))
        order = np.array([2, 0, 1])
        e = self.inputs["encoder"]
        x = dict(
            self.inputs,
            encoder=tuple([e[i][order] for i in range(3)] + list(e[3:])),
            entity_positions=self.inputs["entity_positions"][order],
            actor_mask=self.inputs["actor_mask"][order],
            target_mask=self.inputs["target_mask"][order],
        )
        np.testing.assert_allclose(
            a["actor"][order], self.policy.scores(x, ability=3, actors=(1, 2))["actor"]
        )
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "policy.npz"
            self.policy.save(path, {})
            loaded, _ = JointEntityPolicy.load(path)
            self.assertTrue(loaded.actor_nonlinear)
            np.testing.assert_array_equal(
                a["actor"],
                loaded.scores(self.inputs, ability=3, actors=(0, 1))["actor"],
            )
