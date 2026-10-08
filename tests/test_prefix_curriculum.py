import unittest
import numpy as np
from src.learning.imitation_train import equal_replay_weights


class PrefixCurriculumTests(unittest.TestCase):
    def test_each_whole_replay_has_equal_weight_without_dropping_commands(self):
        weights = np.ones(6)
        balanced = equal_replay_weights(weights, [(0, 2), (2, 6)])
        self.assertEqual(len(balanced), 6)
        self.assertAlmostEqual(balanced[:2].sum(), balanced[2:].sum())
        self.assertAlmostEqual(balanced.sum(), weights.sum())
        self.assertTrue((balanced > 0).all())
