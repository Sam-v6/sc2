import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.learning.entity_policy import JointEntityPolicy
from tests import test_entity_policy


class EntitySpatialPolicyTests(unittest.TestCase):
    def setUp(self):
        fixture = test_entity_policy.EntityPolicyTests()
        fixture.setUp()
        self.inputs = dict(
            fixture.inputs,
            point_features=np.column_stack(
                (fixture.inputs["points"], [[1, 0], [0, 1], [1, 1]])
            ),
        )
        self.label = fixture.label
        self.policy = JointEntityPolicy(
            fixture.policy.encoder, (0, 1, 8), seed=11, spatial_features=4
        )

    def test_zero_initialization_preserves_legacy_predictions(self):
        legacy = JointEntityPolicy(self.policy.encoder, (0, 1, 8), seed=11)
        self.assertEqual(self.policy.predict(self.inputs), legacy.predict(self.inputs))
        new, _ = self.policy.loss_and_gradients(self.inputs, self.label)
        old, _ = legacy.loss_and_gradients(self.inputs, self.label)
        self.assertEqual(new, old)

    def test_map_features_reach_nonspatial_ability_decisions(self):
        self.policy.heads["point_input"][2:] = [
            [0.2, 0.1, -0.1, 0.3],
            [0.1, -0.2, 0.2, 0.4],
        ]
        self.policy.heads["spatial_context"][:] = np.eye(4)
        original = self.policy.scores(self.inputs, ability=3, actors=(0,))
        changed = dict(self.inputs, point_features=self.inputs["point_features"].copy())
        changed["point_features"][:, 2:] = 0
        other = self.policy.scores(changed, ability=3, actors=(0,))
        self.assertGreater(np.linalg.norm(original["ability"] - other["ability"]), 1e-5)

    def test_spatial_gradients_include_global_and_point_paths(self):
        self.policy = JointEntityPolicy(
            self.policy.encoder,
            (0, 1, 8),
            seed=11,
            spatial_features=4,
            refinement=True,
            actor_cutoff=True,
        )
        self.inputs["point_radii"] = np.full((3, 2), 4.0)
        self.policy.heads["actor_cutoff"][:] = 0.1
        self.policy.heads["point_input"][2:] = 0.1
        self.policy.heads["spatial_context"][:] = np.eye(4) * 0.2
        for label in (
            self.label,
            dict(self.label, mode=2, point=1, offset=np.array([0.2, -0.3])),
        ):
            _, gradients = self.policy.loss_and_gradients(self.inputs, label)
            for name in (
                "point_input",
                "point_bias",
                "spatial_context",
                "encoder.scene",
                "actor_cutoff",
            ):
                parameter = self.policy.parameters[name]
                for index in np.ndindex(parameter.shape):
                    original = float(parameter[index])
                    epsilon = 0.002
                    parameter[index] = original + epsilon
                    plus, _ = self.policy.loss_and_gradients(self.inputs, label)
                    parameter[index] = original - epsilon
                    minus, _ = self.policy.loss_and_gradients(self.inputs, label)
                    parameter[index] = original
                    self.assertAlmostEqual(
                        gradients[name][index],
                        (plus - minus) / (2 * epsilon),
                        delta=0.0003,
                    )

    def test_checkpoint_keeps_spatial_predictions(self):
        self.policy.heads["point_bias"][:] = 0.3
        self.policy.heads["spatial_context"][:] = 0.2
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.npz"
            self.policy.save(path, {"spatial": "human"})
            loaded, metadata = JointEntityPolicy.load(path)
            self.assertEqual(loaded.spatial_features, 4)
            self.assertEqual(
                loaded.predict(self.inputs), self.policy.predict(self.inputs)
            )
            self.assertEqual(metadata, {"spatial": "human"})
