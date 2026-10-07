import unittest
import numpy as np
from src.learning.production_timing import first_delays, conditional_times


class ProductionTimingTests(unittest.TestCase):
    def test_label_boundary_and_first_outcome_per_family(self):
        events = [(9, 'unit:SCV'), (10, 'unit:Marine'), (15, 'unit:SCV'),
                  (18, 'unit:SCV'), (20, 'unit:Barracks')]
        self.assertEqual(first_delays(events, 10, 10), {'unit:Marine': 0, 'unit:SCV': 5})

    def test_conditional_time_is_not_the_unconditional_mass(self):
        seconds, known = conditional_times(np.array([.25, 1., 0.]),
                                           np.array([.125, .2, 0.]), 45)
        np.testing.assert_allclose(seconds, [22.5, 9, 0])
        np.testing.assert_array_equal(known, [True, True, False])

    def test_invalid_moments_are_rejected(self):
        with self.assertRaises(ValueError):
            conditional_times(np.array([.1]), np.array([.2]), 45)

    def test_float_roundoff_is_clipped_but_unsupported_timing_stays_unknown(self):
        seconds, known = conditional_times(np.array([1 + 4e-15, 1e-15]),
                                           np.array([.5, 0.]), 45)
        np.testing.assert_allclose(seconds, [22.5, 0])
        np.testing.assert_array_equal(known, [True, False])
