import importlib.util
import unittest

import numpy as np

from tests import test_entity_actor_context_query as query


class ContextFitTests(unittest.TestCase):
    def setUp(self):
        from src.learning.entity_actor_fit import (
            actor_cache,
            context_query_weights,
            context_query_objective,
            fit_actor_context_query,
        )

        fixture = query.ActorContextQueryTests()
        fixture.setUp()
        self.policy = fixture.policy
        self.examples = [
            (fixture.inputs, fixture.label),
            (
                dict(fixture.inputs, actor_mask=np.ones(3, bool)),
                dict(fixture.label, actors=(1,)),
            ),
        ]
        self.cache = actor_cache(fixture.base, self.examples)
        self.weights = context_query_weights
        self.objective = context_query_objective
        self.fit = fit_actor_context_query

    def test_objective_policy_scores_and_gradient_parity(self):
        p = self.policy
        p.heads["actor_context_output"][:] = np.random.default_rng(6).normal(
            0, 0.1, (64, 9)
        )
        vector = self.weights(p)
        loss, gradient = self.objective(vector, self.cache)
        expected_loss = 0.0
        gradients = []
        for inputs, label in self.examples:
            scores = p.scores(inputs, ability=label["ability"], actors=label["actors"])
            eligible = np.flatnonzero(inputs["actor_mask"])
            a = scores["actor"][eligible]
            gold = np.isin(eligible, label["actors"])
            expected_loss += (
                np.mean(np.logaddexp(0, a) - gold * a)
                + np.log(np.exp(a - a.max()).sum())
                + a.max()
                - a[gold].mean()
                - np.log(gold.sum())
            )
            _, g = p.loss_and_gradients(inputs, label)
            linear = np.column_stack(
                (g["actor"], g["actor_geometry"], g["actor_cutoff"])
            )
            gradients.append(
                np.concatenate(
                    [
                        linear.ravel(),
                        *[
                            g[k].ravel()
                            for k in (
                                "actor_context_input",
                                "actor_context_bias",
                                "actor_context_output",
                            )
                        ],
                    ]
                )
            )
        self.assertAlmostEqual(loss, expected_loss / 2, places=6)
        np.testing.assert_allclose(
            gradient, np.mean(gradients, axis=0), atol=2e-6, rtol=2e-5
        )
        for index in [0, 5, 35, 36, 120, 291, len(vector) - 1]:
            high, low = vector.copy(), vector.copy()
            high[index] += 1e-5
            low[index] -= 1e-5
            self.assertAlmostEqual(
                gradient[index],
                (
                    self.objective(high, self.cache)[0]
                    - self.objective(low, self.cache)[0]
                )
                / 2e-5,
                delta=1e-7,
            )

    @unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy absent")
    def test_bounded_fit_preserves_other_parameters(self):
        before = {k: v.copy() for k, v in self.policy.parameters.items()}
        report = self.fit(self.policy, self.cache, iterations=8, seconds=2)
        self.assertLess(report["final_objective"], report["initial_objective"])
        self.assertLessEqual(report["iterations"], 8)
        self.assertTrue(np.any(self.policy.heads["actor_context_output"] != 0))
        for key, value in before.items():
            if key not in (
                "actor",
                "actor_geometry",
                "actor_cutoff",
                "actor_context_input",
                "actor_context_bias",
                "actor_context_output",
            ):
                np.testing.assert_array_equal(value, self.policy.parameters[key])
        snapshot = self.weights(self.policy)
        report = self.fit(self.policy, self.cache, iterations=8, seconds=1e-12)
        self.assertEqual(report["status"], "wall_bound")
        np.testing.assert_array_equal(snapshot, self.weights(self.policy))

    def test_invalid_vector_and_family_rejected(self):
        vector = self.weights(self.policy)
        vector[0] = np.nan
        with self.assertRaisesRegex(ValueError, "Invalid context query"):
            self.objective(vector, self.cache)
        with self.assertRaisesRegex(ValueError, "Invalid context query"):
            self.objective(vector[:-1], self.cache)
        self.policy.actor_context_query = False
        with self.assertRaisesRegex(ValueError, "bounded context-query"):
            self.fit(self.policy, self.cache, iterations=8, seconds=2)
