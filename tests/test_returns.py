import unittest
import numpy as np
from src.rl.policy import Policy
from src.rl.returns import remember_episode


class ReturnTests(unittest.TestCase):
    def test_reward_reaches_earlier_action_and_stops_at_terminal(self):
        policy = Policy(['state'], ['wait', 'advance'])
        policy.gamma = .5
        policy.network[2][:] = 0
        policy.network[3][:] = [0, 1]
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

    def test_nongreedy_continuation_is_excluded_before_its_reward(self):
        policy = Policy(['state'], ['wait', 'advance'])
        policy.gamma = .5
        policy.network[2][:] = 0
        policy.network[3][:] = [0, 1]
        states = [np.array([i]) for i in range(4)]
        transitions = [(states[0], 1, 2, states[1], np.array([True, True]), False),
                       (states[1], 0, 100, states[2], np.array([True, True]), False),
                       (states[2], 1, 10, states[3], np.array([True, True]), True)]
        remember_episode(policy, transitions)
        first = policy.experience[0]
        self.assertEqual(first[2], 2)
        np.testing.assert_array_equal(first[3], states[1])
        self.assertFalse(first[5])
        self.assertEqual(first[-1], .5)

    def test_continuation_uses_the_state_legal_mask(self):
        policy = Policy(['state'], ['wait', 'advance'])
        policy.gamma = .5
        policy.network[2][:] = 0
        policy.network[3][:] = [0, 1]
        transitions = [(np.array([0]), 1, 2, np.array([1]), np.array([True, False]), False),
                       (np.array([1]), 0, 10, np.array([2]), np.array([True, True]), True)]
        remember_episode(policy, transitions)
        self.assertEqual(policy.experience[0][2], 7)
        self.assertTrue(policy.experience[0][5])
