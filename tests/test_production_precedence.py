import unittest
from scipy.sparse import csr_matrix
from src.learning.production_precedence import next_commitments, precedence_target, pair_features


class PrecedenceTests(unittest.TestCase):
    def test_first_commitment_boundary_repeats_and_missing_are_distinct(self):
        events = [(9, 0, 'a'), (10, 2, 'b'), (12, 3, 'b'), (19, 4, 'a'), (20, 5, 'c')]
        first = next_commitments(events, 10, 10)
        self.assertEqual(first, {'b': (10, 2), 'a': (19, 4)})
        self.assertEqual(precedence_target(first, 'b', 'a'), 1)
        self.assertEqual(precedence_target(first, 'a', 'b'), 0)
        self.assertEqual(precedence_target(first, 'b', 'missing'), 1)
        self.assertIsNone(precedence_target(first, 'missing', 'other'))

    def test_same_loop_is_a_tie_despite_source_sequence(self):
        first = {'a': (10, 2), 'b': (10, 3)}
        self.assertIsNone(precedence_target(first, 'a', 'b'))

    def test_feature_pair_orientation_is_explicit_and_state_is_unchanged(self):
        state = csr_matrix([[2, 0, 3]])
        result = pair_features(state, 3, [(0, 2), (2, 0)])
        self.assertEqual(result.toarray().tolist(), [[2, 0, 3, 1, 0, 0, 0, 0, 1], [2, 0, 3, 0, 0, 1, 1, 0, 0]])
        self.assertEqual(state.toarray().tolist(), [[2, 0, 3]])
