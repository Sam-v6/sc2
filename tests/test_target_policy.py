import tempfile
import unittest
from pathlib import Path
import numpy as np


class TargetPolicyTests(unittest.TestCase):
    def test_grouped_gradient_matches_finite_differences(self):
        from src.learning.target_selection import TargetPolicy

        policy = TargetPolicy(3, 2, [], seed=8)
        x = np.array([[1., 0., 2.], [0., 1., 1.], [1., 1., 0.], [2., 0., 1.], [0., 2., 1.]])
        labels = {"ranges": [(0, 2), (2, 5)], "target": [1, 0]}
        weights = np.array([1., 3.])
        loss, gradients = policy.gradients(x, labels, None, weights)
        self.assertTrue(np.isfinite(loss))
        for name, index in (("input", (0, 1)), ("bias", (2,)), ("ability", (1, 0)), ("ability_bias", (1,))):
            parameter = policy.parameters[name]
            original = parameter[index].copy()
            parameter[index] = original + .001
            upper = policy.gradients(x, labels, None, weights)[0]
            parameter[index] = original - .001
            lower = policy.gradients(x, labels, None, weights)[0]
            parameter[index] = original
            self.assertAlmostEqual(gradients[name][index], (upper-lower)/.002, delta=2e-4)
        for name in ("point", "mode", "delay", "target_type", "alliance", "queue"):
            self.assertFalse(np.any(gradients[name]))

    def test_learns_one_target_per_variable_group_and_persists(self):
        from src.learning.target_selection import TargetPolicy, select_target

        policy = TargetPolicy(2, 2, [], seed=9)
        x = np.array([[0., 1.], [1., 0.], [.2, .2], [1., 0.], [0., 1.]], np.float32)
        labels = {"ranges": [(0, 2), (2, 5)], "target": [0, 2]}
        first = policy.gradients(x, labels, None)[0]
        for _ in range(60):
            policy.learn(x, labels, None, rate=.02)
        self.assertLess(policy.gradients(x, labels, None)[0], first*.1)
        units = [{"tag": 10}, {"tag": 20}, {"tag": 30}]
        self.assertEqual(select_target(policy, x[2:], units), 30)
        self.assertEqual(select_target(policy, x[2:][::-1], units[::-1]), 30)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"targets.npz"
            policy.save(path, {"scope": "synthetic target test"})
            restored = TargetPolicy.load(path)
            np.testing.assert_array_equal(policy.predict(x)["ability"], restored.predict(x)["ability"])
            self.assertEqual(restored.updates, policy.updates)

    def test_single_candidate_has_zero_loss_and_sparse_columns_match(self):
        from src.learning.target_selection import TargetPolicy

        policy = TargetPolicy(4, 2, [], seed=10)
        x = np.array([[1., 0., 2., 0.], [2., 0., 0., 0.], [0., 0., 1., 0.]])
        labels = {"ranges": [(0, 1), (1, 3)], "target": [0, 1]}
        full_loss, full = policy.gradients(x, labels, None)
        sparse_loss, sparse = policy.gradients(x[:, [0, 2]], labels, None, feature_indices=[0, 2])
        self.assertEqual(full_loss, sparse_loss)
        for name in full:
            np.testing.assert_array_equal(full[name], sparse[name])
        loss, gradients = policy.gradients(x[:1], {"ranges": [(0, 1)], "target": [0]}, None)
        self.assertEqual(loss, 0.)
        self.assertTrue(all(not np.any(g) for g in gradients.values()))
