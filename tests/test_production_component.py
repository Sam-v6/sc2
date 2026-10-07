"""Current-state production components reuse the broad controller's encoder."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np


@unittest.skipUnless(importlib.util.find_spec("torch"), "optional CPU Torch absent")
class ProductionComponentTests(unittest.TestCase):
    def setUp(self):
        from tests.test_goal_first_policy import GoalFirstPolicyTests

        fixture = GoalFirstPolicyTests()
        fixture.setUp()
        self.fixture = fixture
        self.inputs = dict(fixture.inputs)
        encoder = list(self.inputs["encoder"])
        encoder[4] = np.empty(0, int)
        encoder[5] = np.empty((0, 2), np.float32)
        self.inputs["encoder"] = tuple(encoder)

    def test_shared_encoder_preserves_existing_raw_scores(self):
        policy = self.fixture.policy
        _, context = policy.encode_context(self.fixture.inputs)
        scores = policy._forward(self.fixture.inputs, self.fixture.label)[0]
        np.testing.assert_allclose(
            scores["ability"].detach().numpy()[1:],
            [
                0.6227203,
                -0.4511750,
                0.2188511,
                -0.7731737,
                0.1034702,
                0.2641689,
                -0.5314904,
                -0.4999896,
                0.5798798,
                -0.5048674,
                0.3974605,
            ],
            atol=1e-6,
        )
        np.testing.assert_array_equal(
            scores["ability"].detach().numpy()[1:],
            policy.ability(context).detach().numpy()[1:],
        )

    def test_gate_and_choice_gradients_reach_current_state_encoder(self):
        from src.learning.production_component import ProductionComponent

        for kind, target in (("timing", True), ("choice", 4)):
            policy = ProductionComponent((6, 2, 2, 8, 12, 2), kind, (2, 4), hidden=8)
            policy.loss(self.inputs, target).backward()
            for weight in (policy.head.weight, policy.encoder.entity.weight):
                self.assertGreater(float(weight.grad.abs().sum()), 0)
                self.assertTrue(np.isfinite(weight.grad.numpy()).all())

    def test_human_history_is_rejected_and_checkpoint_preserves_predictions(self):
        from src.learning.production_component import ProductionComponent

        for kind in ("timing", "choice"):
            policy = ProductionComponent((6, 2, 2, 8, 12, 2), kind, (2, 4), hidden=8)
            with self.assertRaises(ValueError):
                policy.predict(self.fixture.inputs)
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "component.npz"
                policy.save(path, {"source": "test"})
                loaded, metadata = ProductionComponent.load(path)
                self.assertEqual(metadata, {"source": "test"})
                self.assertEqual(
                    policy.predict(self.inputs), loaded.predict(self.inputs)
                )

    def test_choice_updates_cannot_change_frozen_timing_component(self):
        import torch
        from src.learning.production_component import ProductionComponent

        timing = ProductionComponent((6, 2, 2, 8, 12, 2), "timing", hidden=8)
        choice = ProductionComponent((6, 2, 2, 8, 12, 2), "choice", (2, 4), hidden=8)
        choice.encoder.load_state_dict(timing.encoder.state_dict())
        timing.requires_grad_(False)
        before = timing.predict(self.inputs)
        optimizer = torch.optim.Adam(choice.parameters(), lr=0.01)
        choice.loss(self.inputs, 4).backward()
        optimizer.step()
        self.assertEqual(before, timing.predict(self.inputs))
        self.assertTrue(all(p.grad is None for p in timing.parameters()))
