import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.learning.entity_encoder import JointEntityEncoder
from src.learning.entity_policy import JointEntityPolicy


class RelativePointTests(unittest.TestCase):
    def setUp(self):
        self.policy = JointEntityPolicy(
            JointEntityEncoder(3, 2, 2, 8, 12, hidden=4, seed=7),
            (0, 1, 8),
            seed=11,
            actor_relative_points=True,
        )
        self.inputs = {
            "encoder": (
                np.array([[0.2, 0.5, 0.1], [0.7, 0.2, 0.4], [0.1, 0.3, 0.8]]),
                np.array([2, 2, 5]),
                np.array([3, 3, 0]),
                np.array([0.1, 0.3]),
                np.array([1, 4]),
                np.array([[0, 0.1], [1, 0.2]]),
            ),
            "actor_mask": np.array([True, True, False]),
            "target_mask": np.ones(3, bool),
            "points": np.array([[0.1, 0.3], [0.6, 0.8], [0.8, 0.2]]),
            "world_points": np.array([[10.0, 30.0], [60.0, 80.0], [80.0, 20.0]]),
            "entity_positions": np.array([[20.0, 50.0], [70.0, 20.0], [10.0, 30.0]]),
        }
        self.label = dict(
            ability=3,
            actors=(0, 1),
            mode=2,
            queue=0,
            delay=2,
            point=1,
            offset=np.array([0.2, -0.3]),
        )
        self.policy.heads["point_relative"][:] = np.arange(16).reshape(4, 4) / 20

    def test_relative_geometry_translation_and_actor_centroid(self):
        _, a = self.policy._forward(self.inputs, ability=3, actors=(0, 1))
        shifted = dict(
            self.inputs,
            world_points=self.inputs["world_points"] + np.array([50.0, -10.0]),
            entity_positions=self.inputs["entity_positions"] + np.array([50.0, -10.0]),
        )
        _, b = self.policy._forward(shifted, ability=3, actors=(0, 1))
        delta = (self.inputs["world_points"] - np.array([45.0, 35.0])) / 32
        np.testing.assert_allclose(
            a["point_relative"], np.concatenate((delta, delta**2), axis=1)
        )
        np.testing.assert_allclose(a["point_relative"], b["point_relative"])

    def test_residual_and_shared_gradients(self):
        _, gradients = self.policy.loss_and_gradients(self.inputs, self.label)
        for name, index in [
            ("point_relative", (2, 1)),
            ("group", (1, 2)),
            ("encoder.entity", (1, 2)),
            ("encoder.abilities", (3, 1)),
        ]:
            parameter = self.policy.parameters[name]
            parameter[:] = parameter.astype(float)
            step = 0.001
            original = float(parameter[index])
            parameter[index] = original + step
            high = self.policy.loss_and_gradients(self.inputs, self.label)[0]
            parameter[index] = original - step
            low = self.policy.loss_and_gradients(self.inputs, self.label)[0]
            parameter[index] = original
            self.assertAlmostEqual(
                gradients[name][index], (high - low) / (2 * step), delta=0.003
            )

    def test_zero_initialization_preserves_all_default_scores(self):
        legacy = JointEntityPolicy(
            JointEntityEncoder(3, 2, 2, 8, 12, hidden=4, seed=7), (0, 1, 8), seed=11
        )
        self.policy.heads["point_relative"][:] = 0
        a = legacy.scores(self.inputs, ability=3, actors=(0, 1))
        b = self.policy.scores(self.inputs, ability=3, actors=(0, 1))
        for name in a:
            np.testing.assert_array_equal(a[name], b[name])

    def test_permutation_and_checkpoint(self):
        a = self.policy.scores(self.inputs, ability=3, actors=(0, 1))
        permutation = np.array([2, 0, 1])
        e = self.inputs["encoder"]
        changed = dict(
            self.inputs,
            encoder=tuple([e[i][permutation] for i in range(3)] + list(e[3:])),
            entity_positions=self.inputs["entity_positions"][permutation],
            actor_mask=self.inputs["actor_mask"][permutation],
            target_mask=self.inputs["target_mask"][permutation],
        )
        b = self.policy.scores(changed, ability=3, actors=(1, 2))
        np.testing.assert_allclose(a["point"], b["point"])
        order = np.array([2, 0, 1])
        changed = dict(
            self.inputs,
            points=self.inputs["points"][order],
            world_points=self.inputs["world_points"][order],
        )
        np.testing.assert_allclose(
            a["point"][order],
            self.policy.scores(changed, ability=3, actors=(0, 1))["point"],
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.npz"
            self.policy.save(path, {})
            loaded, _ = JointEntityPolicy.load(path)
            self.assertTrue(loaded.actor_relative_points)
            np.testing.assert_array_equal(
                a["point"],
                loaded.scores(self.inputs, ability=3, actors=(0, 1))["point"],
            )

    def test_empty_candidates(self):
        inputs = dict(
            self.inputs, points=np.empty((0, 2)), world_points=np.empty((0, 2))
        )
        scores = self.policy.scores(inputs, ability=3, actors=(0, 1))
        self.assertEqual(scores["point"].shape, (0,))
