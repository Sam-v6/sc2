"""Native states precede future issuance; quiet labels need complete coverage."""

import unittest

from src.learning.production_gate import native_gate_windows


class NativeProductionGateTests(unittest.TestCase):
    def test_native_future_boundary_excludes_current_includes_horizon(self):
        labels = native_gate_windows([0, 44, 88], [(0, 1), (44, 2)], [], 100)
        self.assertEqual([r["act"] for r in labels], [True, False, None])
        self.assertEqual(labels[0]["production_keys"], [[44, 2]])
        self.assertEqual(labels[1]["production_keys"], [])

    def test_verified_production_proves_positive_despite_earlier_unknown(self):
        labels = native_gate_windows([0, 44, 88], [(30, 2)], [(10, 1), (70, 3)], 132)
        self.assertEqual([r["act"] for r in labels], [True, None, False])
        self.assertEqual(labels[0]["unknown_keys"], [[10, 1]])
        self.assertEqual(labels[1]["unknown_keys"], [[70, 3]])

    def test_source_end_wait_is_censored_but_verified_positive_is_retained(self):
        self.assertIsNone(native_gate_windows([0], [], [], 20)[0]["act"])
        self.assertTrue(native_gate_windows([0], [(15, 1)], [], 20)[0]["act"])
        self.assertFalse(native_gate_windows([0], [], [], 44)[0]["act"])

    def test_sparse_snapshots_fail_instead_of_interpolating(self):
        with self.assertRaises(ValueError):
            native_gate_windows([0, 88], [], [], 132)

    def test_invalid_chronology_conflict_or_unsupported_state_fails(self):
        for loops, production, unknown, end in (
            ([44, 0], [], [], 88),
            ([0, 0], [], [], 44),
            ([0], [(20, 2), (10, 1)], [], 44),
            ([0], [(20, 2)], [(20, 2)], 44),
            ([44], [], [], 43),
            ([0], [(45, 1)], [], 44),
        ):
            with self.assertRaises(ValueError):
                native_gate_windows(loops, production, unknown, end)
        self.assertEqual(native_gate_windows([], [], [], 0), [])
