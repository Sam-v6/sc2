"""Current-state timing targets cannot cross uncertain human command intervals."""

import unittest
from src.learning.production_decisions import decision_windows


class ProductionDecisionTests(unittest.TestCase):
    def test_real_observation_cadence_has_positive_wait_and_end_censoring(self):
        rows = decision_windows(
            [0, 5, 43, 44, 70, 88, 132], [(20, 2, 319), (88, 3, 524)], []
        )
        self.assertEqual(
            [(r["loop"], r["observation_index"]) for r in rows],
            [(0, 0), (44, 3), (88, 5), (132, 6)],
        )
        self.assertEqual(
            [(r["act"], r["ability"]) for r in rows],
            [(True, 319), (False, None), (True, 524), (None, None)],
        )
        self.assertEqual(rows[-1]["censored"], "source_end")
        self.assertEqual(rows[0]["target_key"], [20, 2])
        self.assertEqual(
            set(rows[0]),
            {"loop", "observation_index", "act", "ability", "target_key", "censored"},
        )

    def test_unknown_before_first_macro_censors_but_later_unknown_does_not(self):
        rows = decision_windows(
            [0, 44, 88, 132], [(20, 2, 319), (88, 3, 524)], [(10, 1), (66, 2), (100, 4)]
        )
        self.assertEqual([r["act"] for r in rows], [None, None, True, None])
        self.assertEqual(
            [r["censored"] for r in rows],
            ["unknown_event", "unknown_event", None, "source_end"],
        )

    def test_same_loop_source_sequence_and_exclusive_horizon(self):
        rows = decision_windows([0, 44, 88], [(44, 2, 319), (44, 4, 524)], [(44, 3)])
        self.assertEqual([r["act"] for r in rows], [False, True, None])
        self.assertEqual(rows[1]["target_key"], [44, 2])
        masked = decision_windows([0, 44, 88], [(44, 2, 319)], [(44, 1)])
        self.assertIsNone(masked[1]["act"])

    def test_sparse_source_observations_are_not_interpolated(self):
        rows = decision_windows([17, 70, 140, 200], [(150, 2, 321)], [])
        self.assertEqual([r["loop"] for r in rows], [17, 70, 140, 200])
        self.assertEqual([r["act"] for r in rows], [False, False, True, None])

    def test_invalid_chronology_and_unknown_production_conflicts_fail(self):
        for loops in ([0, 0, 44], [44, 0]):
            with self.assertRaises(ValueError):
                decision_windows(loops, [], [])
        with self.assertRaises(ValueError):
            decision_windows([0, 44], [(20, 3, 319), (20, 2, 524)], [])
        with self.assertRaises(ValueError):
            decision_windows([0, 44], [(20, 3, 319)], [(20, 3)])
        self.assertEqual(decision_windows([], [], []), [])
