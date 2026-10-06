import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.learning.entity_encoder import JointEntityEncoder

try:
    from src.learning.entity_policy import JointEntityPolicy
except ImportError:
    JointEntityPolicy = None


class EntityPolicyTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(JointEntityPolicy, "joint command policy is missing")
        self.policy = JointEntityPolicy(
            JointEntityEncoder(3, 2, 2, 8, 12, hidden=4, seed=7),
            delays=(0, 1, 8),
            seed=11,
        )
        self.inputs = {
            "encoder": (
                np.array([[0.2, 0.5, -0.1], [0.7, -0.2, 0.4], [0.1, 0.3, 0.8]]),
                np.array([2, 2, 5]),
                np.array([3, 3, 0]),
                np.array([0.1, -0.3]),
                np.array([1, 4]),
                np.array([[0, 0.1], [1, 0.2]]),
            ),
            "actor_mask": np.array([True, True, False]),
            "target_mask": np.array([True, True, True]),
            "points": np.array([[0.1, 0.3], [0.6, 0.8], [0.8, 0.2]]),
        }
        self.label = dict(ability=3, actors=(0,), mode=1, queue=0, delay=2, target=2)

    def test_permutation_preserves_scene_and_permutes_actor_and_target_scores(self):
        first = self.policy.scores(self.inputs, ability=3, actors=(0,))
        permutation = np.array([2, 0, 1])
        changed = dict(self.inputs)
        e = self.inputs["encoder"]
        changed["encoder"] = tuple([e[i][permutation] for i in range(3)] + list(e[3:]))
        for key in ("actor_mask", "target_mask"):
            changed[key] = self.inputs[key][permutation]
        second = self.policy.scores(changed, ability=3, actors=(1,))
        for key in ("ability", "mode", "queue", "delay", "point", "offset"):
            np.testing.assert_allclose(first[key], second[key], atol=1e-7)
        for key in ("actor", "target"):
            np.testing.assert_allclose(first[key][permutation], second[key], atol=1e-7)

    def test_queue_and_target_labels_change_shared_encoder_gradients(self):
        _, initial = self.policy.loss_and_gradients(self.inputs, self.label)
        for change in ({"queue": 1}, {"target": 1}):
            _, gradients = self.policy.loss_and_gradients(
                self.inputs, dict(self.label, **change)
            )
            self.assertGreater(
                np.linalg.norm(gradients["encoder.entity"] - initial["encoder.entity"]),
                1e-6,
            )
            self.assertGreater(
                np.linalg.norm(
                    gradients["encoder.abilities"] - initial["encoder.abilities"]
                ),
                1e-6,
            )

    def test_unknown_timing_contributes_no_delay_gradient(self):
        _, gradients = self.policy.loss_and_gradients(
            self.inputs, dict(self.label, delay=None)
        )
        np.testing.assert_array_equal(gradients["delay"], np.zeros((4, 3)))
        np.testing.assert_array_equal(gradients["delay_bias"], np.zeros(3))

    def test_checkpoint_preserves_ordinary_predictions_and_metadata(self):
        expected = self.policy.predict(self.inputs)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.npz"
            self.policy.save(path, {"sources": ["human-game"]})
            loaded, metadata = JointEntityPolicy.load(path)
            self.assertEqual(metadata, {"sources": ["human-game"]})
            self.assertEqual(loaded.predict(self.inputs), expected)

    def test_labels_outside_fog_safe_actor_or_target_candidates_are_rejected(self):
        for change in ({"actors": (2,)}, {"target": 5}, {"ability": 0}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.policy.loss_and_gradients(self.inputs, dict(self.label, **change))

    def test_prediction_selects_only_eligible_actors_and_targets(self):
        self.policy.heads["mode_bias"][:] = [-100, 100, -100, -100]
        self.inputs["target_mask"] = np.array([False, False, True])
        prediction = self.policy.predict(self.inputs)
        self.assertTrue(prediction["actors"])
        self.assertTrue(set(prediction["actors"]) <= {0, 1})
        self.assertEqual(prediction["target"], 2)
        self.inputs["actor_mask"][:] = False
        self.assertIsNone(self.policy.predict(self.inputs))

    def test_all_command_losses_have_numerically_correct_joint_gradients(self):
        self.policy.encoder.parameters = {
            k: v.astype(float) for k, v in self.policy.encoder.parameters.items()
        }
        self.policy.heads = {k: v.astype(float) for k, v in self.policy.heads.items()}
        for mode in (0, 1, 2, 3):
            label = dict(
                self.label, mode=mode, target=2, point=1, offset=np.array([0.2, -0.3])
            )
            _, gradients = self.policy.loss_and_gradients(self.inputs, label)
            indices = {
                "ability": (1, 3),
                "actor": (1, 2),
                "group": (1, 2),
                "mode": (1, 2),
                "queue": (1, 0),
                "delay": (1, 2),
                "target": (1, 2),
                "point_input": (0, 1),
                "point_query": (1, 2),
                "offset": (1, 0),
                "encoder.entity": (0, 1),
                "encoder.types": (2, 1),
                "encoder.abilities": (3, 1),
                "encoder.scene": (0, 2),
                "encoder.history": (120, 2),
            }
            for name, index in indices.items():
                with self.subTest(mode=mode, parameter=name):
                    parameter = self.policy.parameters[name]
                    original = parameter[index]
                    parameter[index] = original + 1e-6
                    plus, _ = self.policy.loss_and_gradients(self.inputs, label)
                    parameter[index] = original - 1e-6
                    minus, _ = self.policy.loss_and_gradients(self.inputs, label)
                    parameter[index] = original
                    self.assertAlmostEqual(
                        gradients[name][index], (plus - minus) / 2e-6, places=7
                    )


if __name__ == "__main__":
    unittest.main()
