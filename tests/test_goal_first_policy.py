import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np

from tests import test_entity_actor_geometry as geometry


@unittest.skipUnless(importlib.util.find_spec("torch"), "optional CPU Torch absent")
class GoalFirstPolicyTests(unittest.TestCase):
    def setUp(self):
        from src.learning.goal_first_policy import GoalFirstPolicy

        fixture = geometry.ActorGeometryTests()
        fixture.setUp()
        self.inputs, self.label = fixture.inputs, fixture.label
        e = list(self.inputs["encoder"])
        entities = np.zeros((3, 6), np.float32)
        entities[:, :2] = self.inputs["entity_positions"] / 100
        entities[:2, 2] = 1
        entities[2, 3] = 1
        entities[:, 5] = 1
        e[0] = entities
        self.inputs["encoder"] = tuple(e)
        self.policy = GoalFirstPolicy((6, 2, 2, 8, 12, 2), (0, 1, 8), hidden=8, seed=51)

    def test_joint_loss_gradients_and_target_conditioning(self):
        losses = self.policy.loss(self.inputs, self.label)
        sum(losses.values()).backward()
        for name in (
            "entity.weight",
            "point.weight",
            "history.weight_ih_l0",
            "actor.weight",
            "ability.weight",
            "target_point.weight",
        ):
            parameter = dict(self.policy.named_parameters())[name]
            self.assertTrue(np.isfinite(parameter.grad.numpy()).all())
            self.assertGreater(float(parameter.grad.abs().sum()), 0)
        a = self.policy._forward(self.inputs, self.label)[0]["actor"].detach().numpy()
        b = (
            self.policy._forward(self.inputs, dict(self.label, point=0))[0]["actor"]
            .detach()
            .numpy()
        )
        self.assertFalse(np.allclose(a, b))

    def test_permutation_checkpoint_and_history_order(self):
        from src.learning.goal_first_policy import GoalFirstPolicy

        a = self.policy._forward(self.inputs, self.label)[0]
        order = np.array([2, 0, 1])
        e = self.inputs["encoder"]
        x = dict(
            self.inputs,
            encoder=tuple([e[i][order] for i in range(3)] + list(e[3:])),
            actor_mask=self.inputs["actor_mask"][order],
            target_mask=self.inputs["target_mask"][order],
            entity_positions=self.inputs["entity_positions"][order],
        )
        b = self.policy._forward(x, dict(self.label, actors=(1, 2)))[0]
        np.testing.assert_allclose(
            a["actor"].detach().numpy()[order], b["actor"].detach().numpy(), atol=1e-6
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.npz"
            self.policy.save(path, {"phase": "human_imitation"})
            loaded, meta = GoalFirstPolicy.load(path)
            self.assertEqual(meta["phase"], "human_imitation")
            self.assertEqual(
                self.policy.predict(self.inputs), loaded.predict(self.inputs)
            )
        e = list(self.inputs["encoder"])
        e[4] = e[4][::-1].copy()
        e[5] = e[5][::-1].copy()
        reversed_scores = self.policy._forward(
            dict(self.inputs, encoder=tuple(e)), self.label
        )[0]
        self.assertFalse(
            np.allclose(
                a["ability"].detach().numpy(),
                reversed_scores["ability"].detach().numpy(),
            )
        )

    def test_empty_actor_and_history_masks(self):
        self.assertIsNone(
            self.policy.predict(dict(self.inputs, actor_mask=np.zeros(3, bool)))
        )
        e = list(self.inputs["encoder"])
        e[4] = np.empty(0, int)
        e[5] = np.empty((0, 2), np.float32)
        prediction = self.policy.predict(
            dict(self.inputs, encoder=tuple(e), target_mask=np.zeros(3, bool))
        )
        self.assertNotEqual(prediction["mode"], 1)
        self.assertTrue(prediction["actors"])

    def test_named_oracles_do_not_supply_target(self):
        prediction = self.policy.predict(self.inputs, ability=3, actors=(0, 1))
        self.assertEqual(prediction["ability"], 3)
        self.assertEqual(prediction["actors"], (0, 1))
        ordinary_target = self.policy.predict(self.inputs, ability=3)
        self.assertEqual(prediction["mode"], ordinary_target["mode"])
        self.assertEqual(prediction.get("point"), ordinary_target.get("point"))
        self.assertEqual(prediction.get("target"), ordinary_target.get("target"))
