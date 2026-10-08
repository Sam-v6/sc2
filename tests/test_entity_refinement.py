import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.learning.entity_policy import JointEntityPolicy
from tests import test_entity_policy


class EntityRefinementTests(unittest.TestCase):
    def setUp(self):
        fixture = test_entity_policy.EntityPolicyTests()
        fixture.setUp()
        self.inputs, self.label = fixture.inputs, fixture.label
        self.inputs["point_radii"] = np.full((3, 2), 4.0)
        self.policy = JointEntityPolicy(
            fixture.policy.encoder, (0, 1, 8), seed=11, refinement=True
        )

    def test_offsets_depend_on_explicitly_chosen_cell(self):
        first = self.policy.scores(self.inputs, ability=3, actors=(0,), point=0)[
            "offset"
        ]
        second = self.policy.scores(self.inputs, ability=3, actors=(0,), point=1)[
            "offset"
        ]
        self.assertGreater(np.linalg.norm(first - second), 1e-5)

    def test_ordinary_prediction_uses_its_own_cell_not_a_human_label(self):
        for parameter in self.policy.parameters.values():
            parameter[:] = 0
        self.policy.heads["ability_bias"][3] = 100
        self.policy.heads["mode_bias"][2] = 100
        self.policy.heads["offset_cell"][:] = np.eye(2)
        actual = self.policy.predict(self.inputs)
        self.assertEqual(actual["point"], 0)
        np.testing.assert_allclose(actual["offset"], np.tanh([0.1, 0.3]), atol=1e-7)
        oracle = self.policy.scores(self.inputs, ability=3, actors=(0,), point=1)
        np.testing.assert_allclose(oracle["offset"], np.tanh([0.6, 0.8]), atol=1e-7)

    def test_spatial_loss_and_gradient_are_in_physical_tiles(self):
        self.policy.heads["offset"][:] = 0
        self.policy.heads["offset_cell"][:] = 0
        self.policy.heads["offset_bias"][:] = 0
        label = dict(self.label, mode=2, point=1, offset=np.array([0.25, 0.5]))
        larger, gradients = self.policy.loss_and_gradients(self.inputs, label)
        smaller, _ = self.policy.loss_and_gradients(
            dict(self.inputs, point_radii=np.full((3, 2), 2.0)), label
        )
        self.assertAlmostEqual(larger - smaller, 1.875, places=7)
        np.testing.assert_allclose(gradients["offset_bias"], [-4, -8], atol=1e-7)

    def test_point_candidate_permutation_preserves_predicted_world_offset(self):
        first = self.policy.predict(self.inputs)
        self.policy.heads["mode_bias"][:] = [-100, -100, 100, -100]
        first = self.policy.predict(self.inputs)
        permutation = np.array([2, 0, 1])
        changed = dict(
            self.inputs,
            points=self.inputs["points"][permutation],
            point_radii=self.inputs["point_radii"][permutation],
        )
        second = self.policy.predict(changed)
        self.assertEqual(int(permutation[second["point"]]), first["point"])
        np.testing.assert_allclose(first["offset"], second["offset"], atol=1e-7)

    def test_legacy_and_refined_checkpoint_predictions_remain_equivalent(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "policy.npz"
            expected = self.policy.predict(self.inputs)
            self.policy.save(path, {"experiment": "refinement"})
            loaded, _ = JointEntityPolicy.load(path)
            self.assertTrue(loaded.refinement)
            self.assertEqual(loaded.predict(self.inputs), expected)
            fixture = test_entity_policy.EntityPolicyTests()
            fixture.setUp()
            legacy = fixture.policy
            legacy.save(path, {})
            with np.load(path, allow_pickle=False) as archive:
                arrays = {k: archive[k].copy() for k in archive.files}
            configuration = json.loads(str(arrays["configuration"]))
            configuration.pop("refinement", None)
            arrays["configuration"] = json.dumps(configuration)
            np.savez_compressed(path, **arrays)
            restored, _ = JointEntityPolicy.load(path)
            self.assertFalse(restored.refinement)
            self.assertEqual(
                restored.predict(fixture.inputs), legacy.predict(fixture.inputs)
            )

    def test_actor_ranking_adds_selected_set_cross_entropy_without_group_size_cap(self):
        baseline = JointEntityPolicy(self.policy.encoder, (0, 1, 8), seed=11)
        self.policy.heads["actor"][:] = 0
        baseline.heads["actor"][:] = 0
        old, _ = baseline.loss_and_gradients(self.inputs, self.label)
        new, _ = self.policy.loss_and_gradients(self.inputs, self.label)
        self.assertAlmostEqual(new - old, np.log(2), places=7)
        entire = dict(self.label, actors=(0, 1))
        old, _ = baseline.loss_and_gradients(self.inputs, entire)
        new, _ = self.policy.loss_and_gradients(self.inputs, entire)
        self.assertAlmostEqual(new - old, 0, places=7)

    def test_refined_joint_gradients_match_finite_differences_for_all_modes(self):
        self.policy.encoder.parameters = {
            k: v.astype(float) for k, v in self.policy.encoder.parameters.items()
        }
        self.policy.heads = {k: v.astype(float) for k, v in self.policy.heads.items()}
        indices = {
            "actor": (1, 2),
            "group": (1, 2),
            "offset": (1, 0),
            "offset_cell": (0, 1),
            "point_input": (0, 1),
            "point_query": (1, 2),
            "encoder.entity": (0, 1),
            "encoder.types": (2, 1),
            "encoder.abilities": (3, 1),
            "encoder.history": (120, 2),
        }
        for mode in (0, 1, 2, 3):
            label = dict(self.label, mode=mode, point=1, offset=np.array([0.2, -0.3]))
            _, gradients = self.policy.loss_and_gradients(self.inputs, label)
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

    def test_partial_groups_and_edge_cells_have_correct_joint_gradients(self):
        encoder = self.inputs["encoder"]
        self.inputs["encoder"] = (
            np.vstack((encoder[0], encoder[0] + 0.1)),
            np.array([2, 5, 2, 2, 5, 2]),
            np.array([3, 0, 3, 3, 0, 3]),
            *encoder[3:],
        )
        self.inputs["actor_mask"] = np.array([True, False, True, True, False, True])
        self.inputs["target_mask"] = np.ones(6, bool)
        self.policy.encoder.parameters = {
            k: v.astype(float) for k, v in self.policy.encoder.parameters.items()
        }
        self.policy.heads = {k: v.astype(float) for k, v in self.policy.heads.items()}
        for actors, radii in (
            ((0, 2), (1.5, 2)),
            ((0, 2, 3), (4, 0.5)),
            ((0, 2, 3, 5), (4, 4)),
        ):
            self.inputs["point_radii"][1] = radii
            label = dict(
                self.label, actors=actors, mode=2, point=1, offset=np.array([0.2, -0.3])
            )
            _, gradients = self.policy.loss_and_gradients(self.inputs, label)
            for name, index in {
                "actor": (1, 2),
                "group": (1, 2),
                "offset": (1, 0),
                "offset_cell": (0, 1),
                "point_input": (0, 1),
                "point_query": (1, 2),
                "encoder.entity": (0, 1),
                "encoder.types": (2, 1),
                "encoder.abilities": (3, 1),
            }.items():
                with self.subTest(actors=actors, radii=radii, parameter=name):
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
