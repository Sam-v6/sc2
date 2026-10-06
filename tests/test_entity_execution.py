import unittest
import numpy as np

from src.learning.entity_encoder import JointEntityEncoder
from src.learning.entity_policy import JointEntityPolicy

try:
    from src.learning.entity_execution import JointCommandAgent
except ImportError:
    JointCommandAgent = None


class EntityExecutionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(JointCommandAgent, "joint command execution is missing")
        self.policy = JointEntityPolicy(
            JointEntityEncoder(94, 13, 9, 8, 12, hidden=4), (0, 1, 8)
        )
        for parameter in self.policy.parameters.values():
            parameter[:] = 0
        self.policy.heads["ability_bias"][3] = 100
        self.policy.heads["mode_bias"][2] = 100
        self.policy.heads["queue_bias"][1] = 100
        self.policy.heads["delay_bias"][2] = 100
        self.tag = 2**63 + 17
        self.state = dict(
            game_loop=10,
            map_size=[10, 6],
            player={},
            units=[dict(tag=self.tag, unit_type=2, alliance=1, position=[2, 3, 0])],
            owned_memory=[
                dict(
                    tag=25, unit_type=2, alliance=1, position=[1, 2, 0], observed=False
                )
            ],
            memory=[],
            upgrades=[],
        )
        self.agent = JointCommandAgent(self.policy, (8, 12, 0), {})

    def test_decision_preserves_raw_group_queue_and_world_point(self):
        command, delay = self.agent.decide(self.state)
        self.assertEqual(command.units, (25, self.tag))
        self.assertEqual(command.ability, 3)
        self.assertTrue(command.queue)
        np.testing.assert_array_equal(command.target_point, (4, 3))
        self.assertEqual(delay, 8)
        self.assertEqual(
            command.to_proto().action_raw.unit_command.unit_tags[1], self.tag
        )
        self.assertEqual(self.agent.history, [])

    def test_only_issued_commands_enter_history_and_schedule_next_decision(self):
        command, delay = self.agent.decide(self.state)
        self.agent.record_issued(command, self.state, delay)
        self.assertEqual(self.agent.history[0]["game_loop"], 10)
        self.assertEqual(
            self.agent.decide(dict(self.state, game_loop=17)), (None, None)
        )
        self.assertIsNotNone(self.agent.decide(dict(self.state, game_loop=18))[0])
        self.assertEqual(len(self.agent.history), 1)

    def test_target_history_freezes_position_and_zero_delay_advances_one_loop(self):
        from src.learning.gameplay import Command

        state = dict(
            self.state,
            units=[
                *self.state["units"],
                dict(tag=42, unit_type=5, alliance=4, position=[8, 2, 0]),
            ],
        )
        command = Command(3, (self.tag,), target_unit=42)
        self.agent.record_issued(command, state, 0)
        state["units"][-1]["position"] = [9, 5, 0]
        self.assertEqual(self.agent.history[0]["target_position"], [8, 2])
        self.assertEqual(self.agent.decide(state), (None, None))
        self.assertIsNotNone(self.agent.decide(dict(state, game_loop=11))[0])


class EntityEngineSchemaTests(unittest.TestCase):
    def test_engine_schema_accepts_matching_and_rejects_mismatched_vocabularies(self):
        from s2clientprotocol import sc2api_pb2 as pb, data_pb2 as data

        try:
            from src.learning.entity_play import validate_engine
        except ImportError:
            validate_engine = None
        self.assertIsNotNone(validate_engine, "joint native schema guard is missing")
        policy = JointEntityPolicy(
            JointEntityEncoder(94, 13, 9, 8, 12, hidden=4), (0, 1, 8)
        )
        response = pb.ResponseData(
            units=[data.UnitTypeData(unit_id=7)],
            abilities=[data.AbilityData(ability_id=11)],
        )
        self.assertEqual(validate_engine(policy, response), (8, 12, 0))
        response.abilities.add(ability_id=12)
        with self.assertRaises(ValueError):
            validate_engine(policy, response)


class EntityAvailabilityTests(unittest.TestCase):
    def test_unit_command_availability_accepts_aliases_and_requires_all_actors(self):
        from s2clientprotocol import query_pb2 as query
        from src.learning.gameplay import Command

        try:
            from src.learning.entity_execution import command_available
        except ImportError:
            command_available = None
        self.assertIsNotNone(command_available, "native availability check is missing")
        response = query.ResponseQuery()
        response.abilities.add(unit_tag=11).abilities.add(ability_id=3674)
        response.abilities.add(unit_tag=12).abilities.add(ability_id=23)
        catalog = {23: {"remaps_to_ability_id": 3674}, 3674: {}}
        command = Command(23, (11, 12), target_point=(10, 10))
        self.assertTrue(command_available(command, response, catalog))
        response.abilities[1].abilities[0].ability_id = 1
        self.assertFalse(command_available(command, response, catalog))
        self.assertFalse(
            command_available(
                Command(23, (13,), target_point=(10, 10)), response, catalog
            )
        )

    def test_autocast_stays_on_the_engine_validated_path(self):
        from s2clientprotocol import query_pb2 as query
        from src.learning.gameplay import Command

        try:
            from src.learning.entity_execution import command_available
        except ImportError:
            command_available = None
        self.assertIsNotNone(command_available, "native availability check is missing")
        self.assertTrue(
            command_available(
                Command(39, (11,), autocast=True), query.ResponseQuery(), {}
            )
        )


class DecisionStepTests(unittest.TestCase):
    def test_step_cap_never_passes_scheduled_decision_and_due_retries_one(self):
        from src.learning.entity_play import decision_step

        self.assertEqual(decision_step(10, 18, 32), 8)
        self.assertEqual(decision_step(10, 18, 4), 4)
        self.assertEqual(decision_step(10, 18, 1), 1)
        self.assertEqual(decision_step(18, 18, 32), 1)
        self.assertEqual(decision_step(19, 18, 32), 1)


class ObservationProjectionTests(unittest.TestCase):
    def test_projection_normalizes_orders_without_changing_native_state(self):
        from copy import deepcopy
        from src.learning.entity_execution import project_observation

        state = dict(
            player={"minerals": 50, "food_used": 12},
            units=[dict(tag=1, orders=[dict(ability_id=295, progress=0.2)])],
            recent_commands=[dict(game_loop=0, ability=1, units=[1])],
        )
        original = deepcopy(state)
        profile = dict(
            unknown_fields=dict(
                player=["food_used"],
                units=["energy"],
                world=["command_history", "upgrade_absence"],
            ),
            order_aliases={"295": 3666},
        )
        projected = project_observation(state, profile)
        self.assertEqual(projected["units"][0]["orders"][0]["ability_id"], 3666)
        self.assertEqual(projected["unknown_fields"]["world"], ["upgrade_absence"])
        self.assertEqual(projected["recent_commands"], state["recent_commands"])
        self.assertEqual(state, original)
        self.assertIs(project_observation(state, None), state)

    def test_agent_applies_profile_to_features_and_retains_issued_history(self):
        from unittest.mock import Mock
        from src.learning.entity_execution import JointCommandAgent

        policy = Mock(missing_fields=True, spatial_features=2)
        policy.predict.return_value = None
        state = dict(
            game_loop=4,
            map_size=[10, 10],
            player={"food_used": 12},
            units=[
                dict(
                    tag=1,
                    unit_type=2,
                    alliance=1,
                    position=[2, 3],
                    orders=[dict(ability_id=3)],
                )
            ],
        )
        profile = dict(
            unknown_fields=dict(
                player=["food_used"], units=[], world=["command_history"]
            ),
            order_aliases={"3": 4},
        )
        agent = JointCommandAgent(policy, (8, 12, 0), {}, observation_profile=profile)
        agent.history = [dict(game_loop=2, ability=3, units=[1])]
        agent.decide(state)
        encoder = policy.predict.call_args.args[0]["encoder"]
        self.assertEqual(encoder[2].tolist(), [4])
        self.assertEqual(encoder[4].tolist(), [3])
        self.assertEqual(encoder[0][0, 30], 0)  # Left-padded history slots.
        self.assertEqual(encoder[0][0, 92], 1)  # Known latest actor reference.
        self.assertEqual(encoder[3][6], 0)  # Unavailable food_used value.
        self.assertEqual(encoder[3][19], 0)  # Its scene availability mask.
        self.assertEqual(state["units"][0]["orders"][0]["ability_id"], 3)

    def test_profile_rejects_an_alias_not_declared_by_the_engine(self):
        from src.learning.entity_execution import validate_order_aliases

        catalog = {295: {"remaps_to_ability_id": 3666}, 3666: {}}
        validate_order_aliases({"order_aliases": {"295": 3666}}, catalog)
        for aliases in ({"295": 524}, {"524": 3666}, {"3666": 295}):
            with self.assertRaisesRegex(ValueError, "engine catalog"):
                validate_order_aliases({"order_aliases": aliases}, catalog)
