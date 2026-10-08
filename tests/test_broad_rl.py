import tempfile
from pathlib import Path
import unittest
import numpy as np


class BroadRLTests(unittest.TestCase):
    def test_zero_residual_keeps_masked_human_distribution_and_exact_uniform_mixture(
        self,
    ):
        from src.learning.broad_rl import ResidualPPO

        policy = ResidualPPO(2, 3, "base", epsilon=0.2)
        q, _, _ = policy.distribution(
            np.zeros((1, 2)),
            np.array([[2.0, 99.0, 0.0]]),
            np.array([[True, False, True]]),
        )
        expected = np.exp([2.0, 0.0])
        expected = expected / expected.sum() * 0.8 + 0.1
        np.testing.assert_allclose(q[0, [0, 2]], expected)
        self.assertEqual(q[0, 1], 0)

    def test_mixture_ppo_gradient_matches_finite_differences(self):
        from src.learning.broad_rl import ResidualPPO

        policy = ResidualPPO(2, 3, "base", epsilon=0.2)
        x = np.array([[0.3, -0.2], [0.4, 0.7]])
        prior = np.array([[1.0, 0.0, -0.4], [0.2, -0.6, 1.0]])
        masks = np.array([[True, True, False], [True, True, True]])
        actions = np.array([1, 2])
        q, _, _ = policy.distribution(x, prior, masks)
        old = np.log(q[np.arange(2), actions])
        args = (
            x,
            prior,
            masks,
            actions,
            old,
            np.array([0.7, -0.3]),
            np.array([0.4, -0.2]),
        )
        loss, gradients = policy.loss_gradients(*args)
        self.assertTrue(np.isfinite(loss))
        for name, param in policy.parameters.items():
            for index in np.ndindex(param.shape):
                saved = param[index]
                h = 1e-5
                param[index] = saved + h
                a = policy.loss_gradients(*args)[0]
                param[index] = saved - h
                b = policy.loss_gradients(*args)[0]
                param[index] = saved
                self.assertAlmostEqual(
                    gradients[name][index], (a - b) / (2 * h), places=6
                )

    def test_elapsed_time_discount_and_episode_end_are_explicit(self):
        from src.learning.broad_rl import advantages

        discount = 0.99 ** (4 / 112)
        carry = 0.95 ** (4 / 112)
        a, r = advantages(np.array([0.0, 1.0]), np.array([0.0, 0.0]), np.array([4, 4]))
        np.testing.assert_allclose(a, [discount * carry, 1.0])
        np.testing.assert_allclose(r, a)

    def test_checkpoint_rejects_a_different_frozen_macro(self):
        from src.learning.broad_rl import ResidualPPO

        p = ResidualPPO(2, 3, "base")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.npz"
            p.save(path)
            q = ResidualPPO.load(path, "base")
            np.testing.assert_array_equal(q.parameters["actor"], p.parameters["actor"])
            with self.assertRaises(ValueError):
                ResidualPPO.load(path, "different")

    def test_update_increases_probability_of_rewarded_ability_without_unmasking_actions(
        self,
    ):
        from src.learning.broad_rl import ResidualPPO

        p = ResidualPPO(2, 3, "base")
        x = np.tile([1.0, 0.0], (16, 1))
        prior = np.zeros((16, 3))
        masks = np.tile([True, True, False], (16, 1))
        actions = np.tile([1, 0], 8)
        adv = np.tile([1.0, -1.0], 8)
        q, _, _ = p.distribution(x, prior, masks)
        p.update(
            (x, prior, masks, actions, np.log(q[np.arange(16), actions]), adv, adv),
            seed=1,
        )
        after, _, _ = p.distribution(x, prior, masks)
        self.assertGreater(after[0, 1], q[0, 1])
        self.assertTrue((after[:, 2] == 0).all())

    def test_clipped_positive_advantage_has_no_actor_gradient_at_uniform_entropy(self):
        from src.learning.broad_rl import ResidualPPO

        p = ResidualPPO(2, 2, "base")
        _, g = p.loss_gradients(
            np.array([[1.0, 0.0]]),
            np.zeros((1, 2)),
            np.ones((1, 2), dtype=bool),
            np.array([1]),
            np.log([0.25]),
            np.array([1.0]),
            np.array([0.0]),
        )
        np.testing.assert_allclose(g["actor"], 0, atol=1e-12)

    def test_rejected_and_wait_attempts_remain_in_episode_likelihood_accounting(self):
        from src.learning.broad_rl import episode_arrays

        records = [
            dict(
                state=np.array([1.0, 0.0]),
                prior=np.zeros(3),
                mask=np.ones(3, dtype=bool),
                action=a,
                log_prob=np.log(1 / 3),
                value=0.0,
                loop=i * 4,
                killed=0.0,
            )
            for i, a in enumerate([1, 0])
        ]
        arrays = episode_arrays(records, "Tie", 50.0, 8)
        np.testing.assert_array_equal(arrays["actions"], [1, 0])
        np.testing.assert_allclose(arrays["rewards"], [0.0, 0.5])
        np.testing.assert_array_equal(arrays["elapsed_loops"], [4, 4])

    def test_rollout_likelihood_tampering_and_greedy_sampling_are_rejected(self):
        import json
        from src.learning.broad_rl import ResidualPPO, episode_arrays
        from src.learning.broad_train import checked_rollout

        p = ResidualPPO(2, 3, "base")
        x = np.array([1.0, 0.0])
        prior = np.array([1.0, 0.0, -0.5])
        mask = np.array([True, True, False])
        q, _, _ = p.distribution(x[None, :], prior[None, :], mask[None, :])
        records = [
            dict(
                state=x,
                prior=prior,
                mask=mask,
                action=1,
                log_prob=float(np.log(q[0, 1])),
                value=0.0,
                loop=0,
                killed=0.0,
            )
        ]
        arrays = episode_arrays(records, "Tie", 0.0, 4)
        meta = {
            "base_sha256": "base",
            "residual_sha256": "snapshot",
            "sampling": "mixture",
            "epsilon": 0.1,
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rollout.npz"

            def write():
                np.savez_compressed(path, metadata=np.array(json.dumps(meta)), **arrays)

            write()
            checked_rollout(path, p, "snapshot")
            arrays["log_probs"][0] += 0.1
            write()
            with self.assertRaises(ValueError):
                checked_rollout(path, p, "snapshot")
            arrays["log_probs"][0] -= 0.1
            meta["sampling"] = "greedy"
            write()
            with self.assertRaises(ValueError):
                checked_rollout(path, p, "snapshot")
