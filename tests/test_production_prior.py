import unittest
from src.learning.production_prior import prior_scores


class PriorTests(unittest.TestCase):
    def test_orientation_and_unknown_comparisons(self):
        prior = dict(names=['a', 'b', 'c'], teacher_prior={'0,1': [1, 3]})
        scores, unsupported, cycles = prior_scores(prior, ['b', 'a'])
        self.assertEqual(scores, {'b': .25, 'a': .75})
        self.assertEqual((unsupported, cycles), (0, 0))
        scores, unsupported, cycles = prior_scores(prior, ['a', 'c'])
        self.assertEqual(scores, {'a': .5, 'c': .5})
        self.assertEqual(unsupported, 1)

    def test_cycles_produce_scalar_scores_instead_of_invalid_comparator(self):
        prior = dict(names=['a', 'b', 'c'], teacher_prior={'0,1': [0, 2], '1,2': [0, 2], '0,2': [2, 0]})
        scores, unsupported, cycles = prior_scores(prior, ['a', 'b', 'c'])
        self.assertEqual(scores, {'a': .5, 'b': .5, 'c': .5})
        self.assertEqual((unsupported, cycles), (0, 1))
        self.assertEqual(prior_scores(prior, []), ({}, 0, 0))
