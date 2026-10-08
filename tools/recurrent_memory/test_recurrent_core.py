import unittest
import numpy as np
from src.rl.actor_critic import ActorCritic
from recurrent_core import RecurrentCore


class RecurrentTests(unittest.TestCase):
    def setUp(self):
        self.parent = ActorCritic(['a', 'b', 'c'], ['wait', 'build'], seed=9)
        self.core = RecurrentCore(self.parent, seed=331)
        self.states = np.random.default_rng(4).normal(size=(8, 3))
        self.actions = np.array([0, 1, 1, 0, 1, 0, 0, 1])

    def test_initial_outputs_preserve_parent_for_any_history(self):
        actual, values, _ = self.core.sequence(self.states, self.actions)
        logits, expected = self.parent.forward(self.states)
        np.testing.assert_allclose(actual, logits, atol=1e-15, rtol=1e-15)
        np.testing.assert_allclose(values, expected, atol=1e-15, rtol=1e-15)

    def test_chunked_sequence_preserves_full_episode_memory(self):
        self.core.actor[:] = .1
        self.core.value[:] = .1
        full, values, final = self.core.sequence(self.states, self.actions)
        first, v1, memory = self.core.sequence(self.states[:3], self.actions[:3])
        second, v2, resumed = self.core.sequence(self.states[3:], self.actions[3:], memory)
        np.testing.assert_array_equal(np.concatenate([first, second]), full)
        np.testing.assert_array_equal(np.concatenate([v1, v2]), values)
        np.testing.assert_array_equal(resumed[0], final[0])
        self.assertEqual(resumed[1], final[1])

    def test_same_current_observation_can_use_different_histories(self):
        self.core.actor[:] = .1
        _, _, memory = self.core.sequence(self.states[:3], self.actions[:3])
        current = self.states[3:4]
        remembered, _, _ = self.core.sequence(current, [0], memory)
        reset, _, _ = self.core.sequence(current, [0])
        self.assertGreater(np.max(np.abs(remembered-reset)), 1e-6)
        reset_again, _, _ = self.core.sequence(current, [0])
        np.testing.assert_array_equal(reset, reset_again)

    def test_numpy_cell_matches_torch_gru_gate_convention(self):
        import torch
        cell = torch.nn.GRUCell(64+len(self.parent.actions), 32).double()
        with torch.no_grad():
            for name in ['weight_ih', 'weight_hh', 'bias_ih', 'bias_hh']:
                getattr(cell, name).copy_(torch.tensor(getattr(self.core, name)))
        hidden = np.random.default_rng(3).normal(size=32)
        previous = 1
        encoded = np.tanh(self.states[0] @ self.parent.network[0]+self.parent.network[1])
        inputs = np.concatenate([encoded, np.eye(2)[previous]])
        expected = cell(torch.tensor(inputs), torch.tensor(hidden)).detach().numpy()
        actual, _, memory = self.core.step(self.states[0], (hidden, previous))
        np.testing.assert_allclose(memory, expected, atol=1e-14, rtol=1e-14)


if __name__ == '__main__':
    unittest.main()
