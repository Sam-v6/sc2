import io
import unittest
from collections import Counter
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock, patch
from s2clientprotocol import sc2api_pb2 as pb, query_pb2 as q
from src.learning.production_goal_play import ProductionGoalBot
from src.learning.production_ledger import ProductionLedger
from tests.test_terran_primitives import unit


class GoalFlowTests(unittest.IsolatedAsyncioTestCase):
    def bot(self):
        bot = ProductionGoalBot.__new__(ProductionGoalBot)
        st = dict(units=[unit(10, 18)], game_loop=24, upgrades=[], player=dict(minerals=50, vespene=0))
        bot.view = NS(observe=Mock(return_value=st))
        bot.state = NS(response_observation=None)
        bot.game_info = NS(map_size=NS(x=64, y=64))
        bot.next_plan = bot.frames = 0
        bot.prior = None
        bot.intent_mode = False
        bot.record_outcomes = Mock()
        bot.vocabulary, bot.products, bot.profile, bot.model = [], {}, {}, {}
        bot.requested, bot.acknowledged, bot.blocks, bot.result_counts = Counter(), Counter(), Counter(), Counter()
        bot.last_sent, bot.ledger = {}, ProductionLedger()
        bot.catalog, bot.unit_names, bot.units_by_id = {1: {}, 524: {}}, {}, {}
        bot.goals = {name: dict(ability=ability, minerals=cost, gas=0, upgrade=None,
                               descriptor=dict(target=1), unit_type=45)
                     for name, ability, cost in [('expensive', 1, 100), ('worker', 524, 50)]}
        available = q.ResponseQuery(abilities=[q.ResponseQueryAvailableAbilities(unit_tag=10,
            abilities=[dict(ability_id=a) for a in (1, 524)])])
        bot.client = NS(_execute=AsyncMock(return_value=pb.Response(query=available)))
        bot.assistance_destination = (30, 30)
        bot.assistance = Mock(return_value=[])
        bot.stream = io.StringIO()
        return bot

    async def test_unaffordable_forecast_does_not_block_an_affordable_learned_request(self):
        bot = self.bot()
        with patch('src.learning.production_goal_play.current_features', return_value=None), \
             patch('src.learning.production_goal_play.predict_goals', return_value=({'expensive': 1, 'worker': 1}, NS(tolist=lambda: [1, 1]))), \
             patch('src.learning.production_goal_play.eligible_actors', return_value=[unit(10, 18)]), \
             patch('src.learning.production_goal_play.resolve_production_placement', side_effect=self.resolved), \
             patch('src.learning.production_goal_play.issue', new_callable=AsyncMock, return_value=pb.ResponseAction(result=[1])) as issue:
            await bot.on_step(0)
            issue.assert_awaited_once()
            self.assertEqual([c.ability for c in issue.call_args.args[1]], [524])
            self.assertEqual(bot.acknowledged['worker'], 1)

    async def resolved(self, client, command, *args):
        return [command], []

    async def test_micro_runs_between_forecasts_and_keeps_pending_casters_protected(self):
        from src.learning.gameplay import Command
        bot = self.bot()
        bot.next_plan = 100
        bot.ledger.pending[1] = dict(actor=12)
        bot.assistance.return_value = [Command(23, (20,), target_point=(30, 30))]
        with patch('src.learning.production_goal_play.issue', new_callable=AsyncMock, return_value=pb.ResponseAction(result=[1])) as issue:
            await bot.on_step(1)
            bot.assistance.assert_called_once()
            self.assertIn(12, bot.assistance.call_args.args[1])
            issue.assert_awaited_once()
            self.assertEqual(bot.frames, 0)

    async def run_intent(self, *, predicted=None, candidates=None, placement=None, supply=False):
        from src.learning.production_intents import ProductionIntents
        bot = self.bot()
        bot.intent_mode = True
        bot.ledger = ProductionIntents()
        bot.prior = dict(names=['expensive', 'worker'], teacher_prior={'0,1': [0, 1]})
        state = bot.view.observe.return_value
        state['player'].update(minerals=85, food_cap=15, food_used=12)
        bot.goals['worker']['minerals'] = 75
        if supply:
            bot.goals['expensive']['unit_type'] = 99
            bot.units_by_id[99] = dict(food_required=4)
        bot.ledger.plan({'expensive': 1, 'worker': 1}, {}, 0)
        with patch('src.learning.production_goal_play.current_features', return_value=None), \
             patch('src.learning.production_goal_play.predict_goals', return_value=(predicted or {}, NS(tolist=lambda: []))), \
             patch('src.learning.production_goal_play.eligible_actors', side_effect=candidates or (lambda *args: [unit(10, 18)])), \
             patch('src.learning.production_goal_play.resolve_production_placement', side_effect=placement or self.resolved), \
             patch('src.learning.production_goal_play.issue', new_callable=AsyncMock, return_value=pb.ResponseAction(result=[1])) as issue:
            await bot.on_step(0)
        return bot, issue

    async def test_intent_reserves_resources_even_after_forecast_disappears(self):
        import json
        bot, issue = await self.run_intent()
        issue.assert_not_awaited()
        row = json.loads(bot.stream.getvalue())
        self.assertEqual([a['after'][0] for a in row['allocations']], [0, 0])
        self.assertEqual(row['goals'], {})
        self.assertEqual(len(row['intents']), 2)

    async def test_missing_prerequisite_releases_budget_for_other_intent(self):
        bot, issue = await self.run_intent(candidates=lambda state, ability, *args: [] if ability == 1 else [unit(10, 18)])
        self.assertEqual([c.ability for c in issue.call_args.args[1]], [524])
        self.assertEqual(bot.acknowledged['worker'], 1)

    async def test_invalid_placement_releases_budget_for_other_intent(self):
        async def placement(client, command, *args):
            return ([], []) if command.ability == 1 else ([command], [])
        bot, issue = await self.run_intent(placement=placement)
        self.assertEqual([c.ability for c in issue.call_args.args[1]], [524])
        self.assertEqual(bot.blocks['placement:expensive'], 1)

    async def test_supply_blocked_intent_does_not_reserve_resources(self):
        bot, issue = await self.run_intent(supply=True)
        self.assertEqual([c.ability for c in issue.call_args.args[1]], [524])
        self.assertEqual(bot.blocks['supply:expensive'], 1)
