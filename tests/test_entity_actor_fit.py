import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np

from tests import test_entity_actor_geometry as geometry


class ActorFitTests(unittest.TestCase):
    def setUp(self):
        from src.learning.entity_actor_fit import (
            actor_cache,
            actor_objective,
            actor_weights,
            fit_actor_heads,
        )

        self.cache, self.objective = actor_cache, actor_objective
        self.weights, self.fit = actor_weights, fit_actor_heads
        fixture = geometry.ActorGeometryTests()
        fixture.setUp()
        self.policy, self.inputs, self.label = (
            fixture.policy,
            fixture.inputs,
            fixture.label,
        )
        self.policy.actor_cutoff = True
        self.policy.heads["actor_cutoff"] = np.zeros(4, np.float32)

    def test_factored_scores_and_full_command_actor_gradients(self):
        changed = dict(self.label, actors=(1,))
        examples = [(self.inputs, self.label), (self.inputs, changed)]
        c = self.cache(self.policy, examples)
        w = self.weights(self.policy)
        value, gradient = self.objective(w, c)
        losses = []
        gradients = []
        for x, y in examples:
            scores, _ = self.policy._forward(
                x, ability=y["ability"], actors=y["actors"]
            )
            eligible = np.flatnonzero(x["actor_mask"])
            g = np.isin(eligible, y["actors"]).astype(float)
            a = scores["actor"][eligible]
            losses.append(
                np.mean(np.logaddexp(0, a) - g * a)
                + np.log(np.exp(a - a.max()).sum())
                + a.max()
                - a[g.astype(bool)].mean()
                - np.log(g.sum())
            )
            _, grad = self.policy.loss_and_gradients(x, y)
            gradients.append(
                np.column_stack(
                    (grad["actor"], grad["actor_geometry"], grad["actor_cutoff"])
                )
            )
        self.assertAlmostEqual(value, float(np.mean(losses)), places=6)
        np.testing.assert_allclose(gradient, np.mean(gradients, axis=0), atol=1e-6)
        for index in [(0, 0), (1, 4), (2, 8)]:
            high = w.copy()
            low = w.copy()
            high[index] += 0.001
            low[index] -= 0.001
            numeric = (self.objective(high, c)[0] - self.objective(low, c)[0]) / 0.002
            self.assertAlmostEqual(gradient[index], numeric, places=6)

    def test_unequal_groups_match_dense_objective(self):
        x = dict(self.inputs, actor_mask=np.ones(3, bool))
        c = self.cache(
            self.policy,
            [(self.inputs, self.label), (x, dict(self.label, actors=(1, 2)))],
        )
        w = self.weights(self.policy)
        z = np.einsum("nh,nf->nhf", c["contexts"][c["owners"]], c["features"]).reshape(
            len(c["gold"]), -1
        )
        logits = z @ w.ravel()
        gradient = np.zeros(w.size)
        value = 0.0
        for start, end in zip(c["starts"], [*c["starts"][1:], len(logits)]):
            a = logits[start:end]
            g = c["gold"][start:end]
            exp = np.exp(a - a.max())
            p = exp / exp.sum()
            value += (
                np.mean(np.logaddexp(0, a) - g * a)
                + np.log(exp.sum())
                + a.max()
                - a[g.astype(bool)].mean()
                - np.log(g.sum())
            )
            d = (np.exp(-np.logaddexp(0, -a)) - g) / len(g) + p - g / g.sum()
            gradient += z[start:end].T @ d
        actual, grad = self.objective(w, c)
        self.assertAlmostEqual(actual, value / 2, places=10)
        np.testing.assert_allclose(grad.ravel(), gradient / 2, atol=1e-10)

    @unittest.skipUnless(importlib.util.find_spec("scipy"), "Optional SciPy absent")
    def test_fit_preserves_other_heads_and_rejects_nonfinite_weights(self):
        c = self.cache(self.policy, [(self.inputs, self.label)])
        initial = self.objective(self.weights(self.policy), c)[0]
        before = {k: v.copy() for k, v in self.policy.parameters.items()}
        report = self.fit(self.policy, c, optimizer="lbfgs", iterations=30, seconds=5)
        self.assertLess(report["final_objective"], initial)
        for k, v in before.items():
            if k not in ("actor", "actor_geometry", "actor_cutoff"):
                np.testing.assert_array_equal(v, self.policy.parameters[k])
        w = self.weights(self.policy)
        w[0, 0] = np.nan
        with self.assertRaises(ValueError):
            self.objective(w, c)

    def test_unsupported_score_family_and_empty_cache_rejected(self):
        with self.assertRaises(ValueError):
            self.cache(self.policy, [])
        self.policy.actor_nonlinear = True
        with self.assertRaises(ValueError):
            self.cache(self.policy, [(self.inputs, self.label)])

    def test_adam_checkpoint_and_immediate_wall_bound(self):
        c = self.cache(self.policy, [(self.inputs, self.label)])
        before = {k: v.copy() for k, v in self.policy.parameters.items()}
        report = self.fit(self.policy, c, optimizer="adam", iterations=3, seconds=1e-12)
        self.assertEqual(report["status"], "wall_bound")
        self.assertEqual(report["iterations"], 0)
        for k, v in before.items():
            np.testing.assert_array_equal(v, self.policy.parameters[k])
        report = self.fit(self.policy, c, optimizer="adam", iterations=3, seconds=5)
        self.assertEqual(report["iterations"], 3)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.npz"
            self.policy.save(path, {})
            loaded, _ = type(self.policy).load(path)
            self.assertEqual(
                self.policy.predict(self.inputs), loaded.predict(self.inputs)
            )
