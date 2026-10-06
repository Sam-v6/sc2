"""Native callback integration for the existing placement execution primitive."""

import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from s2clientprotocol import sc2api_pb2 as pb, query_pb2 as query
from src.learning.entity_play import JointImitationBot
from src.learning.gameplay import Command


class NativePlacementTests(unittest.IsolatedAsyncioTestCase):
    async def run_callback(self, enabled, legal=True):
        requested = Command(321, (7,), target_point=(10.0, 10.0), queue=True)
        state = dict(game_loop=0, player={}, units=[dict(tag=7, alliance=1)])

        async def execute(**kwargs):
            if "action" in kwargs:
                return pb.Response(action=pb.ResponseAction(result=[1]))
            packet = kwargs["query"]
            if packet.placements:
                return pb.Response(
                    query=query.ResponseQuery(
                        placements=[
                            query.ResponseQueryBuildingPlacement(
                                result=1
                                if legal
                                and p.target_pos.x == 11
                                and p.target_pos.y == 10
                                else 41
                            )
                            for p in packet.placements
                        ]
                    )
                )
            return pb.Response(
                query=query.ResponseQuery(
                    abilities=[
                        query.ResponseQueryAvailableAbilities(
                            unit_tag=7, abilities=[dict(ability_id=321)]
                        )
                    ]
                )
            )

        bot = SimpleNamespace(
            job=dict(engine_placement=enabled, wait_unavailable=True),
            state=SimpleNamespace(response_observation=pb.ResponseObservation()),
            view=SimpleNamespace(observe=Mock(return_value=state)),
            game_info=SimpleNamespace(map_size=SimpleNamespace(x=64, y=64)),
            client=SimpleNamespace(_execute=AsyncMock(side_effect=execute)),
            agent=SimpleNamespace(
                history=[],
                next_loop=0,
                decide=Mock(return_value=(requested, 4)),
                record_issued=Mock(),
            ),
            catalog={321: dict(is_building=True)},
            frames=0,
            commands=0,
            decisions=0,
            availability_blocks=0,
            placement_blocks=0,
            placement_adjustments=0,
            action_results={},
            stream=io.StringIO(),
            schedule_step=Mock(),
        )
        await JointImitationBot.on_step(bot, 0)
        self.assertFalse(hasattr(bot, "callback_error"))
        return bot, requested, json.loads(bot.stream.getvalue())

    async def test_adjustment_dispatches_and_records_actual_command(self):
        bot, requested, trace = await self.run_callback(True)
        self.assertEqual(trace["command"], requested.as_dict())
        self.assertEqual(trace["issued_command"]["target_point"], [11.0, 10.0])
        self.assertEqual(trace["issued_command"]["units"], [7])
        self.assertTrue(trace["issued_command"]["queue"])
        self.assertEqual(
            bot.agent.record_issued.call_args.args[0].target_point, (11.0, 10.0)
        )
        self.assertEqual(bot.placement_adjustments, 1)
        self.assertTrue(trace["placement_queries"])
        self.assertEqual(bot.commands, 1)
        action = next(
            c.kwargs["action"]
            for c in bot.client._execute.call_args_list
            if "action" in c.kwargs
        )
        unit_command = action.actions[0].action_raw.unit_command
        self.assertEqual(
            (
                unit_command.target_world_space_pos.x,
                unit_command.target_world_space_pos.y,
            ),
            (11.0, 10.0),
        )
        self.assertEqual(list(unit_command.unit_tags), [7])
        self.assertTrue(unit_command.queue_command)

    async def test_rejection_never_dispatches_or_records_an_intention(self):
        bot, _, trace = await self.run_callback(True, False)
        self.assertFalse(trace["issued"])
        self.assertIsNone(trace["issued_command"])
        bot.agent.record_issued.assert_not_called()
        self.assertEqual(bot.commands, 0)
        self.assertEqual(bot.placement_blocks, 1)
        self.assertEqual(bot.availability_blocks, 0)
        self.assertEqual(trace["results"], [])
        self.assertFalse(
            any("action" in c.kwargs for c in bot.client._execute.call_args_list)
        )

    async def test_default_retains_requested_point_without_placement_queries(self):
        bot, requested, trace = await self.run_callback(False)
        self.assertEqual(trace["issued_command"], requested.as_dict())
        self.assertEqual(trace["placement_queries"], [])
        self.assertEqual(bot.placement_adjustments, 0)
