import gzip
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from s2clientprotocol import sc2api_pb2 as pb, data_pb2 as data

from src.learning.entity_encoder import JointEntityEncoder
from src.learning.entity_execution import JointCommandAgent
from src.learning.entity_play import validate_engine
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect


class MissingFieldRuntimeTests(unittest.TestCase):
    def policy(self):
        policy = JointEntityPolicy(
            JointEntityEncoder(188, 28, 9, 8, 12, hidden=4),
            (0, 1, 8),
            missing_fields=True,
        )
        for value in policy.parameters.values():
            value[:] = 0
        policy.heads["ability_bias"][3] = 10
        return policy

    def test_saved_format_drives_real_native_agent_and_engine_validation(self):
        state = dict(
            game_loop=10,
            map_size=[10, 6],
            player={},
            units=[dict(tag=1, unit_type=2, alliance=1, position=[2, 3, 0])],
            upgrades=[],
            recent_commands=[],
        )
        policy = self.policy()
        expected = JointCommandAgent(policy, (8, 12, 1), {}).decide(state)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "policy.npz"
            policy.save(path, {"test": "format"})
            restored, metadata = JointEntityPolicy.load(path)
            self.assertTrue(restored.missing_fields)
            self.assertEqual(metadata["test"], "format")
            self.assertEqual(
                JointCommandAgent(restored, (8, 12, 1), {}).decide(state), expected
            )
            response = pb.ResponseData(
                units=[data.UnitTypeData(unit_id=7)],
                abilities=[data.AbilityData(ability_id=11)],
                upgrades=[data.UpgradeData(upgrade_id=0)],
            )
            self.assertEqual(validate_engine(restored, response), (8, 12, 1))
            response.upgrades.add(upgrade_id=1)
            with self.assertRaises(ValueError):
                validate_engine(restored, response)

    def test_legacy_checkpoint_without_format_flag_uses_original_inputs(self):
        policy = JointEntityPolicy(
            JointEntityEncoder(94, 13, 9, 8, 12, hidden=4), (0, 1, 8)
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "policy.npz"
            policy.save(path, {})
            with np.load(path, allow_pickle=False) as archive:
                arrays = dict(archive)
            config = json.loads(str(arrays["configuration"]))
            config.pop("missing_fields", None)
            arrays["configuration"] = json.dumps(config)
            np.savez_compressed(path, **arrays)
            restored, _ = JointEntityPolicy.load(path)
            self.assertFalse(restored.missing_fields)

    def test_incompatible_dimensions_cannot_claim_masked_input_format(self):
        with self.assertRaisesRegex(ValueError, "missing-field"):
            JointEntityPolicy(
                JointEntityEncoder(94, 13, 9, 8, 12), (0, 1), missing_fields=True
            )

    def test_trainer_collection_produces_masked_inputs_for_native_human_examples(self):
        state = dict(
            game_loop=9,
            player={},
            units=[dict(tag=1, unit_type=2, alliance=1, position=[2, 3, 0])],
            upgrades=[],
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            static = dict(
                game_info=dict(start_raw=dict(map_size=dict(x=10, y=6))),
                game_data=dict(
                    units=[dict(unit_id=7)],
                    abilities=[dict(ability_id=11)],
                    upgrades=[dict(upgrade_id=0)],
                ),
            )
            (root / "static.json").write_text(json.dumps(static))
            (root / "dataset.json").write_text(
                json.dumps(dict(issued_command_audit=dict(matched_issued_commands=1)))
            )
            with gzip.open(root / "examples.jsonl.gz", "wt") as stream:
                stream.write(
                    json.dumps(
                        dict(
                            action_loop=10,
                            observation=state,
                            commands=[dict(ability=3, units=[1])],
                            next_action_delay=None,
                        )
                    )
                    + "\n"
                )
            examples, reports = collect([root], (8, 12, 1), missing_fields=True)
            inputs, label, _, reason = examples[0]
            self.assertEqual(inputs["encoder"][0].shape, (1, 188))
            self.assertEqual(inputs["encoder"][3].shape, (28,))
            self.assertEqual(label["ability"], 3)
            self.assertIsNone(reason)
            self.assertEqual(reports[0]["commands"], 1)

            # A partial source cannot promote reconstructed label history into
            # complete observed history merely by enabling availability inputs.
            partial = dict(state, unknown_fields=dict(world=["command_history"]))
            with gzip.open(root / "examples.jsonl.gz", "wt") as stream:
                for loop in (10, 20):
                    stream.write(
                        json.dumps(
                            dict(
                                action_loop=loop,
                                observation=dict(partial, game_loop=loop - 1),
                                commands=[dict(ability=3, units=[1])],
                                next_action_delay=None,
                            )
                        )
                        + "\n"
                    )
            with self.assertRaisesRegex(ValueError, "history"):
                collect([root], (8, 12, 1), missing_fields=True)

    def test_spatial_policy_uses_identical_format_in_trainer_inputs_and_live_agent(
        self,
    ):
        from src.learning.entity_examples import state_inputs
        from tests import test_entity_spatial

        fixture = test_entity_spatial.EntitySpatialTests()
        fixture.setUp()
        state = dict(
            fixture.state,
            game_loop=10,
            player={},
            units=[dict(tag=1, unit_type=2, alliance=1, position=[2, 3, 0])],
            upgrades=[],
            recent_commands=[],
        )
        inputs = state_inputs(
            state, 8, 12, 1, terrain=fixture.terrain, missing_fields=True
        )
        self.assertEqual(inputs["point_features"].shape, (2, 401))
        policy = JointEntityPolicy(
            JointEntityEncoder(188, 28, 9, 8, 12, hidden=4),
            (0, 1, 8),
            missing_fields=True,
            spatial_features=401,
        )
        prediction = policy.predict(inputs)
        command, delay = JointCommandAgent(
            policy, (8, 12, 1), {}, terrain=fixture.terrain
        ).decide(state)
        self.assertEqual(command.ability, prediction["ability"])
        self.assertEqual(delay, prediction["delay"])
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "spatial.npz"
            policy.save(path, {})
            restored, _ = JointEntityPolicy.load(path)
            self.assertEqual(restored.predict(inputs), prediction)
            self.assertEqual(
                JointCommandAgent(
                    restored, (8, 12, 1), {}, terrain=fixture.terrain
                ).decide(state),
                (command, delay),
            )
