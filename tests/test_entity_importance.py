import contextlib
import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from src.learning import entity_train
from tests import test_entity_examples, test_entity_policy


class ImportanceTests(unittest.TestCase):
    def test_main_weighted_fit_keeps_native_vocabulary_dimensions(self):
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
                "--ability-importance",
            ]
            with patch("sys.argv", argv), contextlib.redirect_stdout(io.StringIO()):
                entity_train.main()
            policy, metadata = entity_train.JointEntityPolicy.load(
                output / "policy.npz"
            )
            self.assertEqual(policy.encoder.parameters["types"].shape[0], 8)
            self.assertEqual(policy.encoder.parameters["abilities"].shape[0], 12)
            self.assertEqual(metadata["configuration"]["vocabulary"], [8, 12, 2])
            self.assertEqual(
                metadata["configuration"]["importance"]["abilities"]["3"]["count"], 1
            )

    def test_smart_reduction_rare_cap_and_global_mean(self):
        abilities = [1] * 8 + [3] * 2 + [4]
        weights = entity_train.ability_importance_weights(abilities, 100)
        raw = np.array([0.25] * 8 + [10.0] * 3)
        np.testing.assert_allclose(weights, raw / raw.mean())
        self.assertAlmostEqual(weights.mean(), 1.0)
        self.assertTrue(np.all(weights > 0))

    def test_common_non_smart_unchanged_relative_and_order_preserved(self):
        abilities = [3, 1, 4, 3, 4, 4]
        actual = entity_train.ability_importance_weights(abilities, 2)
        expected = np.array([1.0, 0.25, 1.0, 1.0, 1.0, 1.0])
        np.testing.assert_allclose(actual, expected / expected.mean())

    def policies(self):
        first, second = (
            test_entity_policy.EntityPolicyTests(),
            test_entity_policy.EntityPolicyTests(),
        )
        first.setUp()
        second.setUp()
        return first, second

    def test_unit_weights_preserve_default_loss_and_parameters(self):
        first, second = self.policies()
        a, b = (
            entity_train.Adam(first.policy, 0.01),
            entity_train.Adam(second.policy, 0.01),
        )
        for _ in range(3):
            x = a.step([(first.inputs, first.label)])
            y = b.step([(second.inputs, second.label)], weights=np.ones(1))
            self.assertEqual(x, y)
        for name, parameter in first.policy.parameters.items():
            np.testing.assert_array_equal(parameter, second.policy.parameters[name])

    def test_weighted_loss_and_update_match_duplicated_examples(self):
        first, second = self.policies()
        other = dict(first.label, ability=2, queue=1)
        batch = [(first.inputs, first.label), (first.inputs, other)]
        repeated = [batch[0], batch[0], batch[0], batch[1]]
        a, b = (
            entity_train.Adam(first.policy, 0.01),
            entity_train.Adam(second.policy, 0.01),
        )
        for _ in range(3):
            loss_a = a.step(batch, weights=np.array([1.5, 0.5]))
            loss_b = b.step(repeated)
            self.assertAlmostEqual(loss_a, loss_b, places=6)
        for name, parameter in first.policy.parameters.items():
            np.testing.assert_allclose(
                parameter, second.policy.parameters[name], rtol=1e-5, atol=1e-6
            )
