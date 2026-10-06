import unittest

import numpy as np


class EntityTypeStatusTests(unittest.TestCase):
    def inputs(self):
        raw = np.zeros((5, 188))
        raw[:, 94:124] = 1
        raw[:, 2] = 1
        raw[:3, 5] = 1
        raw[4, 2] = 0
        raw[4, 3] = raw[4, 5] = 1
        raw[:3, 11] = [1, 0.5, 1]
        raw[:3, 19] = [0, 0.4, 0.2]
        raw[:3, 20] = [0, 0.75, 0.25]
        raw[3, 7:30] = 999
        return {
            "encoder": (
                raw,
                np.array([2, 2, 3, 2, 2]),
                np.zeros(5),
                np.zeros(26),
                np.array([]),
                np.zeros((0, 9)),
            )
        }

    def test_known_progress_idle_and_counts_by_type(self):
        from src.learning.entity_type_status import unit_type_status

        result = unit_type_status(self.inputs(), 5).reshape(5, 10)
        np.testing.assert_allclose(
            result[2],
            [np.log1p(2) / 5, np.log1p(1) / 5, 0.75, 1, 0.2, 1, 0.375, 1, 0.5, 0.5],
        )
        np.testing.assert_allclose(
            result[3], [np.log1p(1) / 5, 0, 1, 1, 0.2, 1, 0.25, 1, 0, 0]
        )
        np.testing.assert_array_equal(result[[0, 1, 4]], 0)

    def test_masks_memory_permutation_and_history_do_not_invent_state(self):
        from src.learning.entity_type_status import unit_type_status

        inputs = self.inputs()
        raw = inputs["encoder"][0]
        raw[1, 94 + 11] = 0
        raw[:2, 94 + 19] = 0
        raw[1, 94 + 20] = 0
        expected = unit_type_status(inputs, 5).reshape(5, 10)
        self.assertEqual(expected[2, 2], 1)
        self.assertEqual(expected[2, 3], 0.5)
        self.assertEqual(expected[2, 8], 0)
        raw[1, [11, 19, 20]] = 999
        raw[:, 30:94] = 999
        raw[:, 124:] = 999
        raw[3, 7:30] = -999
        raw[4, 7:30] = -999
        np.testing.assert_array_equal(unit_type_status(inputs, 5), expected.ravel())
        order = [4, 2, 0, 3, 1]
        encoder = inputs["encoder"]
        shuffled = dict(
            inputs,
            encoder=tuple(
                [np.asarray(x)[order] for x in encoder[:3]] + list(encoder[3:])
            ),
        )
        np.testing.assert_array_equal(unit_type_status(shuffled, 5), expected.ravel())
