import unittest

import numpy as np
from scipy.sparse import csr_matrix, hstack

from src.learning.production_probe import fit_forecast, predict_forecast


class ProductionProbeTests(unittest.TestCase):
    def test_native_classes_timing_and_numerical_solution(self):
        x = csr_matrix([[0.0, 1.0], [1.0, 0.0], [0.0, 1.0], [1.0, 0.0]])
        model = fit_forecast(
            x,
            np.array([319, 524, 319, 524]),
            np.array([0.0, 2.0, 0.0, 2.0]),
            regularization=0.001,
        )
        abilities, seconds = predict_forecast(model, x)
        np.testing.assert_array_equal(abilities, [319, 524, 319, 524])
        np.testing.assert_allclose(seconds, [0.0, 2.0, 0.0, 2.0], atol=0.01)
        self.assertLess(model["relative_residual"], 1e-10)

    def test_unseen_feature_columns_do_not_change_predictions(self):
        x = csr_matrix([[0.0, 1.0, 0.0], [1.0, 0.0, 0.0]])
        model = fit_forecast(
            x, np.array([319, 524]), np.array([0.0, 2.0]), regularization=0.1
        )
        a, t = predict_forecast(model, x)
        changed = hstack([x[:, :2], csr_matrix([[100.0], [-100.0]])]).tocsr()
        b, u = predict_forecast(model, changed)
        np.testing.assert_array_equal(a, b)
        np.testing.assert_allclose(t, u)
