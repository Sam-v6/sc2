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

    def memory_policy(self):
        from src.learning.production_component import ProductionComponent

        return ProductionComponent(
            (6, 2, 2, 8, 12, 2),
            "choice",
            (2, 4),
            hidden=8,
            observation_memory=True,
        )

    def test_memory_initialization_and_missing_prefix_preserve_current_prediction(self):
        from src.learning.production_component import ProductionComponent
        import torch

        current = ProductionComponent((6, 2, 2, 8, 12, 2), "choice", (2, 4), hidden=8)
        memory = self.memory_policy()
        enriched = dict(
            self.inputs,
            observation_prefix=[(self.inputs, 45), None, (self.inputs, 336)],
        )
        np.testing.assert_array_equal(
            current.predict(self.inputs), memory.predict(enriched)
        )
        with torch.no_grad():
            memory.memory_projection.weight.fill_(0.5)
        self.assertEqual(
            memory.predict(self.inputs),
            memory.predict(dict(self.inputs, observation_prefix=[None] * 3)),
        )
        self.assertEqual(current.predict(self.inputs), memory.predict(self.inputs))

    def test_memory_gradients_and_checkpoint_include_past_state_contribution(self):
        import torch
        from src.learning.production_component import ProductionComponent

        memory = self.memory_policy()
        enriched = dict(
            self.inputs,
            observation_prefix=[
                (self.inputs, 45),
                (self.inputs, 112),
                (self.inputs, 336),
            ],
        )
        optimizer = torch.optim.Adam(memory.parameters(), lr=0.01)
        memory.loss(enriched, 4).backward()
        self.assertGreater(float(memory.memory_projection.weight.grad.abs().sum()), 0)
        optimizer.step()
        optimizer.zero_grad()
        memory.loss(enriched, 4).backward()
        self.assertGreater(
            float(memory.observation_gru.weight_ih_l0.grad.abs().sum()), 0
        )
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "memory.npz"
            memory.save(path, {"memory": True})
            restored, _ = ProductionComponent.load(path)
            self.assertEqual(memory.predict(enriched), restored.predict(enriched))
        self.assertNotEqual(memory.predict(enriched), memory.predict(self.inputs))

    def test_memory_rejects_command_history_and_invalid_ages(self):
        memory = self.memory_policy()
        for prefix in (
            [(self.fixture.inputs, 45), None, None],
            [(self.inputs, 0), None, None],
            [(self.inputs, 45), (self.inputs, 400), (self.inputs, 336)],
            [(self.inputs, float("nan")), None, None],
            [(self.inputs, 45)],
        ):
            with self.assertRaises(ValueError):
                memory.predict(dict(self.inputs, observation_prefix=prefix))

    def test_memory_uses_actual_age_and_missing_slot_mask(self):
        import torch

        memory = self.memory_policy()
        with torch.no_grad():
            memory.memory_projection.weight.copy_(torch.eye(8))
        young = dict(self.inputs, observation_prefix=[(self.inputs, 45), None, None])
        stale = dict(self.inputs, observation_prefix=[(self.inputs, 385), None, None])
        full = dict(
            self.inputs,
            observation_prefix=[
                (self.inputs, 45),
                (self.inputs, 112),
                (self.inputs, 336),
            ],
        )
        self.assertNotEqual(memory.predict(young), memory.predict(stale))
        self.assertNotEqual(memory.predict(young), memory.predict(full))
