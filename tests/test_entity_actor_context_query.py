import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.learning.entity_policy import JointEntityPolicy
from tests import test_entity_actor_geometry as geometry


class ActorContextQueryTests(unittest.TestCase):
    def setUp(self):
        fixture = geometry.ActorGeometryTests()
        fixture.setUp()
        self.inputs, self.label = fixture.inputs, fixture.label
        self.base = fixture.policy
        self.base.actor_cutoff = True
        self.base.heads["actor_cutoff"] = np.zeros(4, np.float32)
        self.policy = JointEntityPolicy(
            self.base.encoder,
            (0, 1, 8),
            seed=11,
            refinement=True,
            actor_geometry=True,
            actor_cutoff=True,
            actor_context_query=True,
        )

    def test_zero_residual_preserves_baseline(self):
        for name, value in self.base.parameters.items():
            np.testing.assert_array_equal(value, self.policy.parameters[name])
        for name, value in self.base.scores(
            self.inputs, ability=3, actors=(0, 1)
        ).items():
            np.testing.assert_array_equal(
                value, self.policy.scores(self.inputs, ability=3, actors=(0, 1))[name]
            )

    def test_head_and_shared_gradients(self):
        rng = np.random.default_rng(75)
        self.policy.heads["actor_context_output"][:] = rng.normal(0, 0.1, (64, 9))
        _, gradients = self.policy.loss_and_gradients(self.inputs, self.label)
        for name, index in [
            ("actor_context_input", (1, 5)),
            ("actor_context_bias", (3,)),
            ("actor_context_output", (7, 2)),
            ("actor_context_output", (8, 6)),
            ("actor_context_output", (9, 8)),
            ("encoder.entity", (1, 2)),
            ("encoder.pool", (2, 1)),
            ("encoder.abilities", (3, 1)),
        ]:
            parameter = self.policy.parameters[name]
            original = float(parameter[index])
            parameter[index] = original + 0.001
            high = self.policy.loss_and_gradients(self.inputs, self.label)[0]
            parameter[index] = original - 0.001
            low = self.policy.loss_and_gradients(self.inputs, self.label)[0]
            parameter[index] = original
            self.assertAlmostEqual(
                gradients[name][index], (high - low) / 0.002, delta=0.003
            )

    def test_permutation_and_checkpoint(self):
        self.policy.heads["actor_context_output"][:] = 0.1
        scores = self.policy.scores(self.inputs, ability=3, actors=(0, 1))
        order = np.array([2, 0, 1])
        e = self.inputs["encoder"]
        permuted = dict(
            self.inputs,
            encoder=tuple([e[i][order] for i in range(3)] + list(e[3:])),
            entity_positions=self.inputs["entity_positions"][order],
            actor_mask=self.inputs["actor_mask"][order],
            target_mask=self.inputs["target_mask"][order],
        )
        changed = self.policy.scores(permuted, ability=3, actors=(1, 2))
        np.testing.assert_allclose(scores["actor"][order], changed["actor"], atol=1e-6)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.npz"
            self.policy.save(path, {})
            loaded, _ = JointEntityPolicy.load(path)
            self.assertTrue(loaded.actor_context_query)
            for name, value in scores.items():
                np.testing.assert_array_equal(
                    value, loaded.scores(self.inputs, ability=3, actors=(0, 1))[name]
                )
            self.base.save(path, {})
            loaded, _ = JointEntityPolicy.load(path)
            self.assertFalse(loaded.actor_context_query)

    def test_requires_geometry_and_cutoff(self):
        with self.assertRaisesRegex(ValueError, "geometry and cutoff"):
            JointEntityPolicy(self.base.encoder, (0, 1, 8), actor_context_query=True)

    def test_linear_fitter_rejects_context_query(self):
        from src.learning.entity_actor_fit import actor_cache, fit_actor_heads

        cache = actor_cache(self.base, [(self.inputs, self.label)])
        with self.assertRaisesRegex(ValueError, "linear"):
            fit_actor_heads(
                self.policy, cache, optimizer="adam", iterations=1, seconds=1
            )
