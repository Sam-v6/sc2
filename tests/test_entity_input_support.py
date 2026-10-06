import unittest

import numpy as np

from src.learning.entity_encoder import JointEntityEncoder


class InputSupportTests(unittest.TestCase):
    def setUp(self):
        self.encoder = JointEntityEncoder(3, 2, 2, 8, 12, hidden=4, seed=7)
        self.inputs = (
            np.array([[0.2, 0.5, 0.0], [0.7, 0.2, 0.0]]),
            np.array([2, 2]),
            np.array([3, 3]),
            np.array([0.1, 0.0]),
            np.array([1, 4]),
            np.array([[0.0, 0.1], [0.0, 0.2]]),
        )
        self.support = {
            "entity": np.array([True, True, False]),
            "scene": np.array([True, False]),
            "history_roles": np.array([False, True]),
        }

    def test_known_scores_preserved_and_untaught_values_cannot_add_random_effects(self):
        original = self.encoder.forward(*self.inputs)[:2]
        unseen = list(self.inputs)
        unseen[0] = self.inputs[0].copy()
        unseen[0][:, 2] = 3
        unseen[3] = np.array([0.1, 2.0])
        unseen[5] = self.inputs[5].copy()
        unseen[5][:, 0] = 4
        self.assertGreater(
            np.linalg.norm(self.encoder.forward(*unseen)[0] - original[0]), 1e-5
        )
        self.encoder.clear_unseen_inputs(self.support)
        supported = self.encoder.forward(*self.inputs)[:2]
        expanded = self.encoder.forward(*unseen)[:2]
        for before, after, new in zip(original, supported, expanded, strict=True):
            np.testing.assert_array_equal(before, after)
            np.testing.assert_array_equal(after, new)

    def test_new_inputs_remain_trainable(self):
        self.encoder.clear_unseen_inputs(self.support)
        future = list(self.inputs)
        future[0] = self.inputs[0].copy()
        future[0][:, 2] = 1
        future[3] = np.array([0.1, 1.0])
        future[5] = self.inputs[5].copy()
        future[5][:, 0] = 1
        context, entities, cache = self.encoder.forward(*future)
        gradients = self.encoder.backward(
            cache, np.ones_like(context), np.ones_like(entities)
        )
        for name, mask in self.support.items():
            self.assertGreater(np.linalg.norm(gradients[name][~mask]), 1e-6)

    def test_mismatched_support_rejected_before_parameters_change(self):
        before = {k: v.copy() for k, v in self.encoder.parameters.items()}
        with self.assertRaisesRegex(ValueError, "support"):
            self.encoder.clear_unseen_inputs(
                dict(self.support, history_roles=np.ones(3, bool))
            )
        for name in before:
            np.testing.assert_array_equal(before[name], self.encoder.parameters[name])
