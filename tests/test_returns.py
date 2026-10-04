import unittest
import numpy as np
from src.rl.policy import Policy
from src.rl.returns import remember_episode


class ReturnTests(unittest.TestCase):
    def test_reward_reaches_earlier_action_and_stops_at_terminal(self):
        policy = Policy(['state'], ['wait', 'advance'])
        policy.gamma = .5
        transitions = [(np.array([i]), 1, r, np.array([i+1]), np.array([True, True]), i == 2)
                       for i, r in enumerate((1, 2, 100))]
        remember_episode(policy, transitions, steps=2)
        first, second, last = policy.experience
        self.assertEqual(first[2], 2)
        self.assertEqual(first[-1], .25)
        self.assertFalse(first[5])
        self.assertEqual(second[2], 52)
        self.assertTrue(second[5])
        self.assertEqual(last[2], 100)

    def test_cutoff_uses_real_shorter_horizon_and_bootstraps(self):
        policy = Policy(['state'], ['wait', 'advance'])
        policy.gamma = .5
        remember_episode(policy, [(np.array([0]), 1, 10, np.array([1]), np.array([True, True]), False)], steps=32)
        self.assertFalse(policy.experience[0][5])
        self.assertEqual(policy.experience[0][-1], .5)
