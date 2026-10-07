"""Broad learned commands coexist with real mining and combat primitives."""

import io
import json
import unittest
from types import SimpleNamespace as NS
from s2clientprotocol import sc2api_pb2 as pb, query_pb2 as q
from sc2.position import Point2
from src.learning.entity_play import JointImitationBot
from src.learning.entity_execution import JointCommandAgent
from src.learning.gameplay import Command
from tests.test_terran_primitives import economy, unit
from tests.test_production_primitives import DATA


class PrimitiveBridgeTests(unittest.IsolatedAsyncioTestCase):
    def bot(self, command=None, code=1, enabled=True):
        state = dict(
            economy([unit(1, 45), unit(2, 45)]),
            game_loop=24,
            upgrades=[],
            player=dict(minerals=100, vespene=0, food_cap=15, food_used=12),
        )
        state["units"].append(unit(3, 48, x=20, y=20, health_max=45))
        actions = []

        async def execute(**kwargs):
            if "action" in kwargs:
                commands = kwargs["action"].actions
                actions.extend(commands)
                return pb.Response(
                    action=pb.ResponseAction(result=[code] * len(commands))
                )
            return pb.Response(
                query=q.ResponseQuery(
                    abilities=[
                        q.ResponseQueryAvailableAbilities(
                            unit_tag=tag, abilities=[dict(ability_id=16)]
                        )
                        for tag in command.units
                    ]
                )
            )

        agent = JointCommandAgent(None, (1970, 3801, 296), {})
        agent.decide = lambda *args: (command, 40) if command else (None, None)
        bot = NS(
            job=dict(primitive_assistance=enabled, max_game_step=64),
            view=NS(observe=lambda _: state),
            state=NS(response_observation=pb.ResponseObservation()),
            game_info=NS(map_size=NS(x=64, y=64), map_center=Point2((32, 32))),
            start_location=Point2((0, 0)),
            enemy_start_locations=[Point2((60, 60))],
            expansion_locations_list=[Point2((40, 40))],
            in_map_bounds=lambda _: True,
            in_pathing_grid=lambda _: True,
            client=NS(_execute=execute),
            agent=agent,
            catalog={},
            units_by_id={
                **DATA,
                18: dict(name="CommandCenter", attributes=[8]),
                20: dict(name="Refinery", attributes=[8]),
            },
            frames=0,
            commands=0,
            decisions=0,
            availability_blocks=0,
            placement_blocks=0,
            placement_adjustments=0,
            action_results={},
            stream=io.StringIO(),
            next_mining=0,
            attacking=False,
            search_index=0,
            learned_control=set(),
            primitive_commands=0,
            primitive_results={},
            scheduled_step_counts={},
        )
        bot.run_primitives = JointImitationBot.run_primitives.__get__(bot)
        bot.schedule_step = JointImitationBot.schedule_step.__get__(bot)
        return bot, state, actions

    async def test_wait_keeps_mining_and_combat_active_without_inventing_production(
        self,
    ):
        bot, _, actions = self.bot()
        bot.agent.next_loop = 200
        await JointImitationBot.on_step(bot, 0)
        rows = [json.loads(line) for line in bot.stream.getvalue().splitlines()]
        commands = [a.action_raw.unit_command for a in actions]
        self.assertEqual({t for c in commands for t in c.unit_tags}, {1, 2, 3})
        self.assertEqual({c.ability_id for c in commands}, {295, 23})
        self.assertEqual(bot.agent.history, [])
        self.assertEqual(bot.commands, 0)
        self.assertEqual(bot.primitive_commands, 3)
        self.assertEqual(rows[0]["phase"], "primitives")
        self.assertLessEqual(bot.client.game_step, 8)

    async def test_learned_worker_and_army_orders_are_protected_through_model_wait(
        self,
    ):
        command = Command(16, (1, 3), target_point=(15, 15))
        bot, state, actions = self.bot(command)
        await JointImitationBot.on_step(bot, 0)
        state["game_loop"] = 32
        bot.agent.decide = lambda *args: (None, None)
        await JointImitationBot.on_step(bot, 1)
        actors = [list(a.action_raw.unit_command.unit_tags) for a in actions]
        self.assertEqual(actors, [[1, 3], [2]])
        self.assertEqual([c["ability"] for c in bot.agent.history], [16])
        self.assertEqual(bot.commands, 1)
        self.assertEqual(bot.primitive_commands, 1)
        rows = [json.loads(line) for line in bot.stream.getvalue().splitlines()]
        self.assertEqual(rows[0]["primitive_protected"], [1, 3])
        self.assertEqual(rows[1]["primitive_protected"], [1, 3])

    async def test_rejected_learned_action_does_not_claim_history_or_protection(self):
        bot, _, _ = self.bot(Command(16, (1,), target_point=(15, 15)), code=6)
        await JointImitationBot.on_step(bot, 0)
        self.assertEqual(bot.agent.history, [])
        self.assertEqual(bot.agent.next_loop, 0)
        self.assertEqual(bot.learned_control, set())

    async def test_default_wait_has_no_assistance(self):
        bot, _, actions = self.bot(enabled=False)
        await JointImitationBot.on_step(bot, 0)
        self.assertEqual(actions, [])
        self.assertEqual(bot.stream.getvalue(), "")
