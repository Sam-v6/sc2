import unittest
import numpy as np
from scipy.sparse import csr_matrix
from scipy.special import expit
from src.learning.production_utility import utility_objective


class UtilityTests(unittest.TestCase):
    def fixture(self):
        x = csr_matrix([[1.0, 2.0], [0.0, -1.0]])
        row, left, right = np.array([0, 1, 0]), np.array([0, 2, 1]), np.array([1, 0, 2])
        y, sample_weight = np.array([1.0, 0.0, 1.0]), np.array([0.2, 0.3, 0.5])
        parameters = np.arange(9, dtype=float).reshape(3, 3) / 20
        return parameters, x, row, left, right, y, sample_weight

    def test_sparse_gathered_objective_matches_expanded_pairs(self):
        p, x, row, left, right, y, weight = self.fixture()
        loss, grad = utility_objective(
            p.ravel(), x, row, left, right, y, weight, 0.01, 3
        )
        expanded = np.c_[x.toarray(), np.ones(2)][row]
        logits = np.array(
            [v @ (p[:, a] - p[:, b]) for v, a, b in zip(expanded, left, right)]
        )
        expected_loss = (
            weight * (np.logaddexp(0, logits) - y * logits)
        ).sum() + 0.01 * np.square(p[:-1]).sum() / 2
        expected_gradient = np.zeros_like(p)
        for v, a, b, t, w, z in zip(expanded, left, right, y, weight, logits):
            residual = w * (expit(z) - t)
            expected_gradient[:, a] += v * residual
            expected_gradient[:, b] -= v * residual
        expected_gradient[:-1] += 0.01 * p[:-1]
        self.assertAlmostEqual(loss, expected_loss)
        np.testing.assert_allclose(grad.reshape(p.shape), expected_gradient, atol=1e-12)

    def test_gradient_matches_finite_differences(self):
        p, *args = self.fixture()
        flat = p.ravel()
        _, analytic = utility_objective(flat, *args, 0.01, 3)
        numerical = []
        for i in range(len(flat)):
            plus, minus = flat.copy(), flat.copy()
            plus[i] += 1e-6
            minus[i] -= 1e-6
            numerical.append(
                (
                    utility_objective(plus, *args, 0.01, 3)[0]
                    - utility_objective(minus, *args, 0.01, 3)[0]
                )
                / 2e-6
            )
        np.testing.assert_allclose(analytic, numerical, atol=1e-8)

    def test_common_bias_changes_neither_pair_loss_nor_gradient(self):
        p, *args = self.fixture()
        shifted = p.copy()
        shifted[-1] += 7
        a = utility_objective(p.ravel(), *args, 0.01, 3)
        b = utility_objective(shifted.ravel(), *args, 0.01, 3)
        self.assertAlmostEqual(a[0], b[0])
        np.testing.assert_allclose(a[1], b[1], atol=1e-12)

    def test_mirrored_pairs_have_the_same_normalized_objective(self):
        p, x, row, left, right, y, weight = self.fixture()
        a = utility_objective(p.ravel(), x, row, left, right, y, weight, 0.01, 3)
        b = utility_objective(
            p.ravel(),
            x,
            np.r_[row, row],
            np.r_[left, right],
            np.r_[right, left],
            np.r_[y, 1 - y],
            np.r_[weight, weight] / 2,
            0.01,
            3,
        )
        self.assertAlmostEqual(a[0], b[0])
        np.testing.assert_allclose(a[1], b[1], atol=1e-12)
