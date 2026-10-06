import contextlib
import gzip
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from src.learning.entity_encoder import JointEntityEncoder
from src.learning.entity_policy import JointEntityPolicy


@unittest.skipUnless(
    importlib.util.find_spec("torch"), "Optional CPU PyTorch runtime absent"
)
class TorchEncoderTests(unittest.TestCase):
    def setUp(self):
        from src.learning.entity_torch_encoder import TorchEntityEncoder

        self.kind = TorchEntityEncoder
        self.arguments = (
            np.array(
                [
                    [0.2, 0.4, 1.0, 0.0, 0.0, 1.0],
                    [0.4, 0.5, 0.0, 1.0, 0.0, 1.0],
                    [0.7, 0.3, 0.0, 0.0, 1.0, 1.0],
                ],
                np.float32,
            ),
            np.array([2, 3, 4]),
            np.array([1, 0, 2]),
            np.array([0.1, 0.5, 0.6], np.float32),
            np.array([1, 2]),
            np.array([[0.1, 0.2], [0.3, 0.4]], np.float32),
        )

    def test_cpu_backend_matches_numpy_forward_and_gradients(self):
        legacy = JointEntityEncoder(
            6, 3, 2, 8, 12, hidden=4, seed=7, role_pooling=True, context_layer_norm=True
        )
        current = self.kind(
            6,
            3,
            2,
            8,
            12,
            hidden=4,
            seed=7,
            role_pooling=True,
            context_layer_norm=True,
            relational_attention=False,
        )
        a, e, cache = legacy.forward(*self.arguments)
        b, f, other = current.forward(*self.arguments)
        np.testing.assert_allclose(a, b, atol=1e-6)
        np.testing.assert_allclose(e, f, atol=1e-6)
        g = np.arange(4, dtype=np.float32) / 10
        h = np.arange(12, dtype=np.float32).reshape(3, 4) / 20
        expected = legacy.backward(cache, g, h)
        actual = current.backward(other, g, h)
        for name in expected:
            np.testing.assert_allclose(
                expected[name], actual[name], atol=2e-6, rtol=2e-5
            )

    def test_relational_gradients_and_neighbor_effect(self):
        encoder = self.kind(
            6,
            3,
            2,
            8,
            12,
            hidden=4,
            seed=7,
            role_pooling=True,
            relational_attention=True,
        )
        encoder.parameters["attention_output"][:] = (
            np.arange(16, dtype=np.float32).reshape(4, 4) / 30
        )
        context, entities, cache = encoder.forward(*self.arguments)
        g = np.arange(4, dtype=np.float32) / 10
        h = np.arange(12, dtype=np.float32).reshape(3, 4) / 20
        gradients = encoder.backward(cache, g, h)

        def objective():
            c, e, _ = encoder.forward(*self.arguments)
            return float(c @ g + (e * h).sum())

        for name, index in [
            ("attention_query", (1, 2)),
            ("attention_key", (2, 1)),
            ("attention_value", (1, 3)),
            ("attention_output", (3, 1)),
            ("attention_distance", (0,)),
            ("types", (2, 1)),
            ("entity", (0, 1)),
        ]:
            parameter = encoder.parameters[name]
            old = float(parameter[index])
            step = 0.001
            parameter[index] = old + step
            high = objective()
            parameter[index] = old - step
            low = objective()
            parameter[index] = old
            self.assertAlmostEqual(
                gradients[name][index], (high - low) / (2 * step), delta=0.002
            )
        changed = list(self.arguments)
        changed[1] = np.array([2, 7, 4])
        _, other, _ = encoder.forward(*changed)
        self.assertGreater(float(np.linalg.norm(other[0] - entities[0])), 1e-5)

    def test_permutation_and_empty_inputs(self):
        encoder = self.kind(
            6,
            3,
            2,
            8,
            12,
            hidden=4,
            seed=7,
            role_pooling=True,
            relational_attention=True,
        )
        encoder.parameters["attention_output"][:] = 0.1
        c, e, _ = encoder.forward(*self.arguments)
        order = np.array([2, 0, 1])
        changed = [x[order] if i < 3 else x for i, x in enumerate(self.arguments)]
        d, f, _ = encoder.forward(*changed)
        np.testing.assert_allclose(c, d, atol=1e-6)
        np.testing.assert_allclose(e[order], f, atol=1e-6)
        empty = (
            np.empty((0, 6), np.float32),
            np.array([], int),
            np.array([], int),
            self.arguments[3],
            np.array([], int),
            np.empty((0, 2), np.float32),
        )
        c, e, cache = encoder.forward(*empty)
        self.assertTrue(np.isfinite(c).all())
        self.assertEqual(e.shape, (0, 4))
        self.assertTrue(
            all(
                np.isfinite(g).all()
                for g in encoder.backward(cache, np.ones(4), np.empty((0, 4))).values()
            )
        )

    def test_checkpoint_retains_backend_and_attention(self):
        encoder = self.kind(6, 3, 2, 8, 12, hidden=4, seed=7, relational_attention=True)
        policy = JointEntityPolicy(encoder, (0, 1, 8), seed=11)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.npz"
            policy.save(path, {})
            loaded, _ = JointEntityPolicy.load(path)
            self.assertEqual(loaded.encoder.backend, "torch")
            self.assertTrue(loaded.encoder.relational_attention)
            a, e, _ = encoder.forward(*self.arguments)
            b, f, _ = loaded.encoder.forward(*self.arguments)
            np.testing.assert_array_equal(a, b)
            np.testing.assert_array_equal(e, f)

    def test_joint_command_loss_and_adam_train_the_relations(self):
        from src.learning.entity_train import Adam

        encoder = self.kind(
            6,
            3,
            2,
            8,
            12,
            hidden=4,
            seed=7,
            role_pooling=True,
            relational_attention=True,
        )
        encoder.parameters["attention_output"][:] = 0.1
        policy = JointEntityPolicy(encoder, (0, 1, 8), seed=11, refinement=True)
        inputs = dict(
            encoder=self.arguments,
            actor_mask=np.array([True, False, False]),
            target_mask=np.ones(3, bool),
            points=np.array([[0.1, 0.3], [0.6, 0.8]], np.float32),
        )
        label = dict(ability=3, actors=(0,), mode=1, queue=0, delay=0, target=1)
        before, gradients = policy.loss_and_gradients(inputs, label)
        name = "encoder.attention_query"
        index = (1, 2)
        p = policy.parameters[name]
        old = float(p[index])
        step = 0.001
        p[index] = old + step
        high = policy.loss_and_gradients(inputs, label)[0]
        p[index] = old - step
        low = policy.loss_and_gradients(inputs, label)[0]
        p[index] = old
        self.assertAlmostEqual(
            gradients[name][index], (high - low) / (2 * step), delta=0.002
        )
        original = encoder.parameters["attention_output"].copy()
        optimizer = Adam(policy, 0.001)
        for _ in range(10):
            optimizer.step([(inputs, label)])
        after, _ = policy.loss_and_gradients(inputs, label)
        self.assertLess(after, before)
        self.assertFalse(
            np.array_equal(original, encoder.parameters["attention_output"])
        )

    def test_relational_cli_fit_binds_runtime_and_source(self):
        from src.learning import entity_train
        from tests import test_entity_examples

        fixture = test_entity_examples.EntityExamplesTests()
        fixture.setUp()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dataset = root / "human"
            dataset.mkdir()
            (dataset / "static.json").write_text(
                json.dumps(
                    dict(
                        game_info={"start_raw": {"map_size": {"x": 10, "y": 6}}},
                        game_data=dict(
                            units=[dict(unit_id=7)],
                            abilities=[dict(ability_id=11)],
                            upgrades=[dict(upgrade_id=1)],
                        ),
                    )
                )
            )
            (dataset / "dataset.json").write_text(
                json.dumps(
                    dict(
                        status="completed",
                        sha256="test-human-replay",
                        disable_fog=False,
                        alignment="state_at_action_loop_minus_one",
                        teacher_kind="human_unverified",
                        player={"player_info": {"race_actual": 1}},
                        issued_command_audit={
                            "matched_issued_commands": 1,
                            "unresolved_events": [],
                        },
                    )
                )
            )
            with gzip.open(dataset / "examples.jsonl.gz", "wt") as stream:
                stream.write(
                    json.dumps(
                        dict(
                            action_loop=100,
                            next_action_delay=None,
                            observation=dict(fixture.state, game_loop=99),
                            commands=[
                                dict(ability=3, units=[fixture.tag], target_unit=12)
                            ],
                        )
                    )
                    + "\n"
                )
            output = root / "fit"
            argv = [
                "entity_train",
                "--train",
                str(dataset),
                "--output",
                str(output),
                "--epochs",
                "1",
                "--wall-seconds",
                "10",
                "--relational-attention",
            ]
            with patch("sys.argv", argv), contextlib.redirect_stdout(io.StringIO()):
                entity_train.main()
            policy, metadata = JointEntityPolicy.load(output / "policy.npz")
            self.assertTrue(policy.encoder.relational_attention)
            configuration = metadata["configuration"]
            self.assertEqual(configuration["encoder_runtime"]["device"], "cpu")
            self.assertEqual(configuration["encoder_runtime"]["threads"], 2)
            self.assertTrue(
                any(
                    Path(p).name == "entity_torch_encoder.py"
                    for p in configuration["code_before"]
                )
            )
            report = json.loads((output / "report.json").read_text())
            self.assertEqual(report["status"], "completed")
            self.assertTrue(report["bindings_unchanged"])
