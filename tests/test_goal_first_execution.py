"""Optional controller integration checks, not native strength tests."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np


@unittest.skipUnless(importlib.util.find_spec("torch"), "optional CPU Torch absent")
class GoalFirstExecutionTests(unittest.TestCase):
    def setUp(self):
        import torch
        from src.learning.goal_first_policy import GoalFirstPolicy
        from src.learning.entity_execution import JointCommandAgent
        from tests.test_entity_execution import EntityExecutionTests

        fixture = EntityExecutionTests()
        fixture.setUp()
        self.state = fixture.state
        self.policy = GoalFirstPolicy((188, 26, 9, 8, 12, 2), (0, 1, 8), hidden=4)
        with torch.no_grad():
            for p in self.policy.parameters():
                p.zero_()
            self.policy.ability.bias[3] = 100
            self.policy.mode.bias[2] = 100
            self.policy.queue.bias[1] = 100
            self.policy.delay.bias[2] = 100
        self.agent = JointCommandAgent(self.policy, (8, 12, 0), {})

    def test_raw_commands_and_issued_only_history(self):
        command, delay = self.agent.decide(self.state)
        self.assertEqual(command.ability, 3)
        self.assertEqual(command.units, (25, 2**63 + 17))
        np.testing.assert_array_equal(command.target_point, (4, 3))
        self.assertTrue(command.queue)
        self.assertEqual(delay, 8)
        self.assertEqual(
            command.to_proto().action_raw.unit_command.unit_tags[1], 2**63 + 17
        )
        self.assertEqual(self.agent.history, [])
        self.agent.record_issued(command, self.state, delay)
        self.assertEqual(len(self.agent.history), 1)
        self.assertEqual(
            self.agent.decide(dict(self.state, game_loop=17)), (None, None)
        )
        self.assertIsNotNone(self.agent.decide(dict(self.state, game_loop=18))[0])

    def test_explicit_loader_parity_and_native_schema_guard(self):
        from src.learning.entity_play import load_policy, validate_engine
        from s2clientprotocol import sc2api_pb2 as pb, data_pb2 as data

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.npz"
            self.policy.save(path, {"phase": "integration_test"})
            loaded, meta = load_policy(path, "goal-first")
            self.assertEqual(meta["phase"], "integration_test")
            from src.learning.entity_execution import JointCommandAgent

            self.assertEqual(
                self.agent.decide(self.state),
                JointCommandAgent(loaded, (8, 12, 0), {}).decide(self.state),
            )
        response = pb.ResponseData(
            units=[data.UnitTypeData(unit_id=7)],
            abilities=[data.AbilityData(ability_id=11)],
        )
        self.assertEqual(validate_engine(self.policy, response), (8, 12, 0))
        response.abilities.add(ability_id=12)
        with self.assertRaises(ValueError):
            validate_engine(self.policy, response)

    def test_spatial_masked_native_inputs_and_reject_toy_schema(self):
        from src.learning.goal_first_policy import GoalFirstPolicy
        from src.learning.entity_execution import JointCommandAgent
        from src.learning.entity_examples import state_inputs
        from src.learning.entity_play import validate_engine
        from tests.test_entity_spatial import EntitySpatialTests
        from s2clientprotocol import sc2api_pb2 as pb

        fixture = EntitySpatialTests()
        fixture.setUp()
        state = dict(self.state, map=fixture.state["map"])
        inputs = state_inputs(
            state, 8, 12, 0, terrain=fixture.terrain, missing_fields=True
        )
        self.assertEqual(inputs["point_features"].shape[1], 401)
        policy = GoalFirstPolicy((188, 26, 9, 8, 12, 401), (0, 1, 8), hidden=4)
        agent = JointCommandAgent(policy, (8, 12, 0), {}, fixture.terrain)
        from src.learning.entity_examples import decode_command

        predicted = policy.predict(inputs)
        self.assertEqual(
            agent.decide(state), (decode_command(predicted, inputs), predicted["delay"])
        )
        for dimensions in (
            (6, 2, 2, 8, 12, 2),
            (188, 26, 2, 8, 12, 2),
            (188, 26, 9, 8, 12, 386),
        ):
            toy = GoalFirstPolicy(dimensions, (0, 1), hidden=4)
            with self.assertRaises(ValueError):
                validate_engine(toy, pb.ResponseData())


class DefaultPolicyLoaderTests(unittest.TestCase):
    def test_joint_default_does_not_import_optional_controller(self):
        from unittest.mock import patch
        from src.learning.entity_examples import state_inputs
        from src.learning.entity_play import load_policy
        from tests.test_entity_execution import EntityExecutionTests

        fixture = EntityExecutionTests()
        fixture.setUp()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.npz"
            fixture.policy.save(path, {"phase": "default_loader"})
            with patch.dict("sys.modules", {"src.learning.goal_first_policy": None}):
                loaded, metadata = load_policy(path)
            self.assertEqual(metadata["phase"], "default_loader")
            inputs = state_inputs(fixture.state, 8, 12)
            self.assertEqual(loaded.predict(inputs), fixture.policy.predict(inputs))


@unittest.skipUnless(importlib.util.find_spec("torch"), "optional CPU Torch absent")
class GoalFirstTypeStatusTests(unittest.TestCase):
    def test_zero_initialization_gradients_checkpoint_and_native_agent(self):
        import torch
        from src.learning.goal_first_policy import GoalFirstPolicy
        from src.learning.entity_examples import state_inputs, command_label
        from src.learning.entity_execution import JointCommandAgent
        from src.learning.gameplay import Command
        from tests.test_entity_execution import EntityExecutionTests

        fixture = EntityExecutionTests()
        fixture.setUp()
        dimensions = (188, 26, 9, 8, 12, 2)
        baseline = GoalFirstPolicy(dimensions, (0, 1, 8), hidden=4, seed=8156)
        policy = GoalFirstPolicy(
            dimensions, (0, 1, 8), hidden=4, seed=8156, type_status=True
        )
        for name, value in baseline.state_dict().items():
            torch.testing.assert_close(value, policy.state_dict()[name], rtol=0, atol=0)
        inputs = state_inputs(fixture.state, 8, 12, missing_fields=True)
        self.assertEqual(baseline.predict(inputs), policy.predict(inputs))
        command = Command(3, (25, fixture.tag), target_point=(4, 3), queue=True)
        label = command_label(command, inputs, (0, 1, 8), 8)
        sum(policy.loss(inputs, label).values()).backward()
        gradient = policy.status_projection.weight.grad
        self.assertTrue(torch.isfinite(gradient).all())
        self.assertGreater(float(gradient.abs().sum()), 0)
        with torch.no_grad():
            policy.status_projection.weight -= 0.01 * gradient
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.npz"
            policy.save(path, {"phase": "typed_state_test"})
            loaded, metadata = GoalFirstPolicy.load(path)
            self.assertTrue(loaded.type_status)
            self.assertEqual(policy.predict(inputs), loaded.predict(inputs))
            self.assertIsNotNone(
                JointCommandAgent(loaded, (8, 12, 0), {}).decide(fixture.state)[0]
            )
            baseline.save(path, {})
            with np.load(path, allow_pickle=False) as archive:
                arrays = {name: archive[name] for name in archive.files}
            import json

            configuration = json.loads(str(arrays["configuration"]))
            configuration.pop("type_status")
            arrays["configuration"] = json.dumps(configuration)
            np.savez(path, **arrays)
            legacy, _ = GoalFirstPolicy.load(path)
            self.assertFalse(legacy.type_status)
            self.assertEqual(baseline.predict(inputs), legacy.predict(inputs))


@unittest.skipUnless(importlib.util.find_spec("torch"), "optional CPU Torch absent")
class GoalFirstAvailabilityTests(GoalFirstExecutionTests):
    def test_candidates_mask_ability_and_selected_actors(self):
        from src.learning.entity_examples import state_inputs
        from src.learning.entity_execution import JointCommandAgent

        inputs = state_inputs(self.state, 8, 12, missing_fields=True)
        inputs["command_candidates"] = {4: {"normal": [1], "autocast": []}}
        original_mask = inputs["actor_mask"].copy()
        prediction = self.policy.predict(inputs)
        np.testing.assert_array_equal(inputs["actor_mask"], original_mask)
        self.assertEqual(self.policy.predict(inputs), prediction)
        self.assertEqual(prediction["ability"], 4)
        self.assertEqual(prediction["actors"], (1,))
        self.assertNotEqual(prediction["mode"], 3)
        self.assertEqual(self.agent.decide(self.state)[0].ability, 3)
        agent = JointCommandAgent(self.policy, (8, 12, 0), {})
        command, _ = agent.decide(
            self.state, {4: {"normal": [2**63 + 17], "autocast": []}}
        )
        self.assertEqual(command.ability, 4)
        self.assertEqual(command.units, (2**63 + 17,))

    def test_empty_candidates_wait_and_autocast_needs_no_normal_cast(self):
        from src.learning.entity_examples import state_inputs

        inputs = state_inputs(self.state, 8, 12, missing_fields=True)
        inputs["command_candidates"] = {}
        self.assertIsNone(self.policy.predict(inputs))
        inputs["command_candidates"] = {4: {"normal": [], "autocast": [0]}}
        prediction = self.policy.predict(inputs)
        self.assertEqual(prediction["ability"], 4)
        self.assertEqual(prediction["mode"], 3)
        self.assertEqual(prediction["actors"], (0,))
