import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.learning.entity_policy import JointEntityPolicy
from tests import test_entity_policy


class EntityCutoffTests(unittest.TestCase):
    def setUp(self):
        fixture = test_entity_policy.EntityPolicyTests()
        fixture.setUp()
        self.inputs, self.label = fixture.inputs, fixture.label
        self.policy = JointEntityPolicy(
            fixture.policy.encoder, (0, 1, 8), seed=11, actor_cutoff=True
        )

    def test_scene_changes_group_size_without_human_cardinality(self):
        for parameter in self.policy.parameters.values():
            parameter[:] = 0
        self.policy.encoder.parameters["scene"][0, 0] = 1
        self.policy.heads["actor_cutoff"][0] = 1
        self.policy.heads["ability_bias"][3] = 100
        e = self.inputs["encoder"]
        negative = dict(self.inputs, encoder=(*e[:3], np.array([-1.0, 0.0]), *e[4:]))
        positive = dict(self.inputs, encoder=(*e[:3], np.array([1.0, 0.0]), *e[4:]))
        self.assertEqual(self.policy.predict(negative)["actors"], (0,))
        self.assertEqual(self.policy.predict(positive)["actors"], (0, 1))

    def test_zero_cutoff_preserves_legacy_scores_and_loss(self):
        legacy = JointEntityPolicy(self.policy.encoder, (0, 1, 8), seed=11)
        self.assertEqual(self.policy.predict(self.inputs), legacy.predict(self.inputs))
        new_loss, _ = self.policy.loss_and_gradients(self.inputs, self.label)
        old_loss, _ = legacy.loss_and_gradients(self.inputs, self.label)
        self.assertEqual(new_loss, old_loss)

    def test_group_size_is_unbounded_by_the_new_cutoff(self):
        for parameter in self.policy.parameters.values():
            parameter[:] = 0
        self.policy.encoder.parameters["context_bias"][0] = 1
        self.policy.heads["actor_cutoff"][0] = 1
        e = self.inputs["encoder"]
        changed = dict(
            self.inputs,
            encoder=(np.zeros((47, 3)), np.zeros(47, int), np.zeros(47, int), *e[3:]),
            actor_mask=np.ones(47, bool),
            target_mask=np.ones(47, bool),
        )
        self.assertEqual(self.policy.predict(changed)["actors"], tuple(range(47)))

    def test_cutoff_gradients_include_shared_context_and_ability(self):
        self.policy.refinement = True
        self.policy.heads["offset_cell"] = np.zeros((2, 2), np.float32)
        self.policy.heads["actor_cutoff"][:] = [0.3, -0.4, 0.2, 0.1]
        _, gradients = self.policy.loss_and_gradients(self.inputs, self.label)
        for name in ("actor_cutoff", "encoder.scene", "encoder.abilities", "actor"):
            parameter = self.policy.parameters[name]
            for index in np.ndindex(parameter.shape):
                if name == "encoder.abilities" and index[0] not in (1, 3, 4):
                    continue
                original = float(parameter[index])
                epsilon = 0.002
                parameter[index] = original + epsilon
                plus, _ = self.policy.loss_and_gradients(self.inputs, self.label)
                parameter[index] = original - epsilon
                minus, _ = self.policy.loss_and_gradients(self.inputs, self.label)
                parameter[index] = original
                self.assertAlmostEqual(
                    gradients[name][index], (plus - minus) / (2 * epsilon), delta=0.0003
                )
        self.assertGreater(np.linalg.norm(gradients["actor_cutoff"]), 0)

    def test_checkpoint_and_legacy_predictions_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.npz"
            self.policy.heads["actor_cutoff"][:] = 0.5
            expected = self.policy.predict(self.inputs)
            self.policy.save(path, {"teacher": "human"})
            loaded, metadata = JointEntityPolicy.load(path)
            self.assertTrue(loaded.actor_cutoff)
            self.assertEqual(loaded.predict(self.inputs), expected)
            self.assertEqual(metadata, {"teacher": "human"})
            legacy = JointEntityPolicy(self.policy.encoder, (0, 1, 8), seed=11)
            legacy.save(path, {})
            restored, _ = JointEntityPolicy.load(path)
            self.assertFalse(restored.actor_cutoff)
            self.assertEqual(restored.predict(self.inputs), legacy.predict(self.inputs))
