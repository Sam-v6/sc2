import importlib.util
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from tests import test_goal_first_policy as controller


@unittest.skipUnless(importlib.util.find_spec("torch"), "optional CPU Torch absent")
class GoalFirstTrainTests(unittest.TestCase):
    def setUp(self):
        from src.learning.goal_first_train import fit_goal_first, teaching_support

        fixture = controller.GoalFirstPolicyTests()
        fixture.setUp()
        self.policy, self.inputs, self.label = (
            fixture.policy,
            fixture.inputs,
            fixture.label,
        )
        self.examples = [(self.inputs, self.label)]
        self.support, self.fit = teaching_support, fit_goal_first

    def test_teaching_only_neutralization_preserves_teacher_scores_and_learnability(
        self,
    ):
        before = self.policy._forward(self.inputs, self.label)[0]
        support = self.support(self.policy, self.examples)
        self.assertFalse(support["entity"][4])
        self.assertFalse(support["types"][7])
        self.assertTrue(support["abilities"][3])
        self.policy.clear_unseen_inputs(support)
        after = self.policy._forward(self.inputs, self.label)[0]
        for name, value in before.items():
            if value is not None:
                np.testing.assert_array_equal(
                    value.detach().numpy(), after[name].detach().numpy()
                )
        self.assertTrue((self.policy.entity.weight[:, 4] == 0).all())
        self.assertTrue((self.policy.type_embedding.weight[7] == 0).all())
        e = list(self.inputs["encoder"])
        e[0] = e[0].copy()
        e[0][0, 4] = 1
        sum(
            self.policy.loss(dict(self.inputs, encoder=tuple(e)), self.label).values()
        ).backward()
        self.assertGreater(float(self.policy.entity.weight.grad[:, 4].abs().sum()), 0)

    def test_bounded_fit_and_immediate_stop(self):
        before = float(sum(self.policy.loss(self.inputs, self.label).values()).detach())
        report = self.fit(
            self.policy,
            self.examples,
            epochs=4,
            batch_size=1,
            rate=0.01,
            seconds=2,
            seed=3,
        )
        self.assertEqual(report["updates"], 4)
        self.assertEqual(report["presentations"], 4)
        self.assertLess(
            float(sum(self.policy.loss(self.inputs, self.label).values()).detach()),
            before,
        )
        weights = {
            k: v.detach().numpy().copy() for k, v in self.policy.state_dict().items()
        }
        self.policy.predict(self.inputs)
        for key, value in self.policy.state_dict().items():
            np.testing.assert_array_equal(weights[key], value.detach().numpy())
        report = self.fit(
            self.policy,
            self.examples,
            epochs=4,
            batch_size=1,
            rate=0.01,
            seconds=1e-12,
            seed=3,
        )
        self.assertEqual(report["status"], "wall_bound")
        self.assertEqual(report["updates"], 0)
        for key, value in self.policy.state_dict().items():
            np.testing.assert_array_equal(weights[key], value.detach().numpy())

    def test_interrupted_batch_does_not_apply_partial_gradients(self):
        weights = {
            k: v.detach().numpy().copy() for k, v in self.policy.state_dict().items()
        }
        ticks = iter((0.0, 0.0, 0.0, 2.0, 2.0))
        with patch(
            "src.learning.goal_first_train.time",
            SimpleNamespace(monotonic=lambda: next(ticks)),
        ):
            report = self.fit(
                self.policy,
                self.examples * 2,
                epochs=1,
                batch_size=2,
                rate=0.01,
                seconds=1,
                seed=3,
            )
        self.assertEqual(report["status"], "wall_bound")
        self.assertEqual(report["updates"], 0)
        self.assertEqual(report["presentations"], 0)
        for key, value in self.policy.state_dict().items():
            np.testing.assert_array_equal(weights[key], value.detach().numpy())
        self.assertTrue(all(p.grad is None for p in self.policy.parameters()))

    def test_prediction_history_replaces_human_entity_references(self):
        from src.learning.goal_first_train import prediction_history_examples
        from src.learning.entity_examples import state_inputs
        from src.learning.gameplay import Command
        from tests import test_entity_examples as examples

        fixture = examples.EntityExamplesTests()
        fixture.setUp()
        rows = []
        original = []
        for loop in (100, 101):
            state = json.loads(json.dumps(fixture.state))
            state["game_loop"] = loop
            state["recent_commands"] = [
                dict(ability=3, units=[fixture.tag], game_loop=99)
            ]
            x = state_inputs(state, 8, 12, missing_fields=True)
            original.append((x, None, Command(3, (fixture.tag,)), None))
            rows.append(
                (
                    dict(
                        observation=state,
                        action_loop=loop,
                        commands=[Command(3, (fixture.tag,)).as_dict()],
                    ),
                    state,
                )
            )

        class Predictor:
            def predict(self, x):
                return dict(
                    ability=4,
                    actors=(x["tags"].index(25),),
                    mode=0,
                    queue=False,
                    delay=1,
                )

        rebuilt, records = prediction_history_examples(
            Predictor(), original, rows, (8, 12, 0), {}
        )
        self.assertEqual(len(rebuilt[0][0]["encoder"][4]), 0)
        np.testing.assert_array_equal(rebuilt[1][0]["encoder"][4], [4])
        # Last event's actor bit names the predicted worker, not the human worker.
        x = rebuilt[1][0]
        self.assertEqual(x["encoder"][0][x["tags"].index(25), 92], 1)
        self.assertEqual(x["encoder"][0][x["tags"].index(fixture.tag), 92], 0)
        self.assertEqual(records[1]["prior_prediction_events"], 1)
        self.assertEqual([r["row"] for r in records], [0, 1])

    def test_final_example_crossing_deadline_is_discarded(self):
        weights = {
            k: v.detach().numpy().copy() for k, v in self.policy.state_dict().items()
        }
        ticks = iter((0.0, 0.0, 0.0, 2.0, 2.0))
        with patch(
            "src.learning.goal_first_train.time",
            SimpleNamespace(monotonic=lambda: next(ticks)),
        ):
            report = self.fit(
                self.policy,
                self.examples,
                epochs=1,
                batch_size=1,
                rate=0.01,
                seconds=1,
                seed=3,
            )
        self.assertEqual(report["status"], "wall_bound")
        self.assertEqual(report["updates"], 0)
        for key, value in self.policy.state_dict().items():
            np.testing.assert_array_equal(weights[key], value.detach().numpy())
