import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.learning.entity_policy import JointEntityPolicy
from tests import test_entity_policy


class EntityCountTests(unittest.TestCase):
    def setUp(self):
        fixture = test_entity_policy.EntityPolicyTests()
        fixture.setUp()
        self.inputs, self.label = fixture.inputs, fixture.label
        self.policy = JointEntityPolicy(
            fixture.policy.encoder, (0, 1, 8), seed=11, actor_count=True
        )

    def test_predicted_size_selects_ranked_eligible_units(self):
        scores = self.policy.scores(self.inputs, ability=3)
        best = int(np.argmax(scores["actor"][:2]))
        self.policy.heads["actor_count_bias"][:] = 0
        self.assertEqual(self.policy.predict(self.inputs, ability=3)["actors"], (best,))
        self.policy.heads["actor_count_bias"][:] = np.log(2)
        self.assertEqual(
            set(self.policy.predict(self.inputs, ability=3)["actors"]), {0, 1}
        )
        self.policy.heads["actor_count_bias"][:] = 1000
        self.assertEqual(
            set(self.policy.predict(self.inputs, ability=3)["actors"]), {0, 1}
        )
        self.policy.heads["actor_count_bias"][:] = -1000
        self.assertEqual(self.policy.predict(self.inputs, ability=3)["actors"], (best,))

    def test_large_groups_have_no_fixed_selection_cap(self):
        e = self.inputs["encoder"]
        changed = dict(
            self.inputs,
            encoder=(np.zeros((47, 3)), np.zeros(47, int), np.zeros(47, int), *e[3:]),
            actor_mask=np.ones(47, bool),
            target_mask=np.ones(47, bool),
        )
        self.policy.heads["actor_count_bias"][:] = np.log(47)
        self.assertEqual(set(self.policy.predict(changed)["actors"]), set(range(47)))

    def test_count_loss_trains_shared_context_and_ability_with_correct_gradients(self):
        self.policy.heads["actor_count"][:] = [0.3, -0.4, 0.2, 0.1]
        label = dict(self.label, actors=(0, 1))
        _, gradients = self.policy.loss_and_gradients(self.inputs, label)
        for name in (
            "actor_count",
            "actor_count_bias",
            "encoder.scene",
            "encoder.abilities",
        ):
            parameter = self.policy.parameters[name]
            for index in np.ndindex(parameter.shape):
                if name == "encoder.abilities" and index[0] not in (1, 3, 4):
                    continue
                original = float(parameter[index])
                parameter[index] = original + 0.002
                plus, _ = self.policy.loss_and_gradients(self.inputs, label)
                parameter[index] = original - 0.002
                minus, _ = self.policy.loss_and_gradients(self.inputs, label)
                parameter[index] = original
                self.assertAlmostEqual(
                    gradients[name][index], (plus - minus) / 0.004, delta=0.0003
                )
        self.assertGreater(np.linalg.norm(gradients["actor_count"]), 0)
        _, one = self.policy.loss_and_gradients(self.inputs, self.label)
        self.assertGreater(
            np.linalg.norm(one["actor_count"] - gradients["actor_count"]), 0
        )

    def test_checkpoint_preserves_group_predictions_and_legacy_mode(self):
        self.policy.heads["actor_count_bias"][:] = np.log(2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.npz"
            self.policy.save(path, {"teacher": "human"})
            loaded, metadata = JointEntityPolicy.load(path)
            self.assertTrue(loaded.actor_count)
            self.assertEqual(
                loaded.predict(self.inputs), self.policy.predict(self.inputs)
            )
            self.assertEqual(metadata, {"teacher": "human"})
            legacy = JointEntityPolicy(self.policy.encoder, (0, 1, 8), seed=11)
            legacy.save(path, {})
            loaded, _ = JointEntityPolicy.load(path)
            self.assertFalse(loaded.actor_count)
            self.assertEqual(loaded.predict(self.inputs), legacy.predict(self.inputs))
