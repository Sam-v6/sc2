import unittest
import numpy as np
from src.rl.terran import encode, FEATURES, reward
from src.rl.terran import TerranLearner, ACTIONS
from src.rl.policy import Policy


class TerranTests(unittest.TestCase):
    def test_encoder_uses_declared_live_features(self):
        empty = encode({})
        live = encode({'minerals': 400, 'workers': 20, 'enemy_ground': 10, 'enemy_near_base': 1})
        self.assertEqual(len(live), len(FEATURES))
        self.assertTrue(np.isfinite(live).all())
        self.assertNotEqual(live[FEATURES.index('enemy_ground')], empty[FEATURES.index('enemy_ground')])
        self.assertGreater(live[FEATURES.index('enemy_near_base')], 0)

    def test_reward_uses_potential_difference(self):
        # Unchanged state cannot yield a recurring positive shaping reward.
        self.assertLessEqual(reward(2, 2, .99), 0)
        self.assertEqual(reward(2, 0, .99, terminal_reward=100), 98)


class StanceTests(unittest.IsolatedAsyncioTestCase):
    async def test_retreat_requires_new_combat_orders(self):
        bot = TerranLearner(Policy(FEATURES, ACTIONS), False, '/tmp/unused-actions.jsonl')
        bot.attacking = True
        await bot.execute('retreat')
        self.assertFalse(bot.attacking)
        self.assertTrue(bot.stance_changed)

    async def test_gathering_precedes_macro_command(self):
        from types import SimpleNamespace
        from unittest.mock import AsyncMock
        bot = TerranLearner(Policy(FEATURES, ACTIONS), False, '/tmp/unused-actions.jsonl')
        bot.state = SimpleNamespace(game_loop=0)
        bot.snapshot = lambda: {}
        bot.legal_mask = lambda: np.array([True] + [False] * (len(ACTIONS) - 1))
        bot.potential = lambda: 0
        order = []
        bot.prepare_macro_options = AsyncMock()
        bot.micro = AsyncMock(side_effect=lambda: order.append('gather'))
        bot.execute = AsyncMock(side_effect=lambda action: order.append('macro'))
        await bot.custom_on_step(0)
        self.assertEqual(order, ['gather', 'macro'])


class SpatialTests(unittest.IsolatedAsyncioTestCase):
    async def test_blocked_expansion_and_addon_are_excluded_and_feasible_candidates_used(self):
        from types import SimpleNamespace
        from unittest.mock import AsyncMock, Mock
        from sc2.position import Point2
        from sc2.units import Units
        from sc2.ids.unit_typeid import UnitTypeId as U
        bot = TerranLearner(Policy(FEATURES, ACTIONS), False, '/tmp/unused-actions.jsonl')
        mask = np.zeros(len(ACTIONS), dtype=bool)
        mask[[ACTIONS.index('wait'), ACTIONS.index('expand'), ACTIONS.index('barracks_techlab')]] = True
        bot.legal_mask = Mock(return_value=mask)
        bot.state = SimpleNamespace(game_loop=0)
        bot.expansion_locations_list = [Point2((20, 0)), Point2((40, 0))]
        bot.game_info = SimpleNamespace(player_start_location=Point2((0, 0)))
        bot.townhalls = Units([], bot)
        candidates = [SimpleNamespace(is_ready=True, is_idle=True, has_add_on=False,
                                     add_on_position=Point2((x, 0)), build=Mock(return_value=True)) for x in (10, 30)]
        bot.structures = Mock(side_effect=lambda kind: Units(candidates if kind == U.BARRACKS else [], bot))
        bot.structures.of_type.return_value = Units([], bot)
        bot.game_data = SimpleNamespace(units={U.COMMANDCENTER.value: SimpleNamespace(footprint_radius=2.5)})
        bot.client = SimpleNamespace(_query_building_placement_fast=AsyncMock(return_value=[False, True]),
                                     query_pathings=AsyncMock(return_value=[20]))
        bot.can_place_single = AsyncMock(side_effect=[False, True])
        builder = SimpleNamespace(position=Point2((100, 100)), tag=1)
        bot.select_build_worker = Mock(return_value=builder)
        await bot.prepare_macro_options()
        self.assertEqual(bot.expansion_target, Point2((40, 0)))
        bot.client.query_pathings.assert_awaited_once_with([[builder.position, Point2((40, 0))]])
        self.assertEqual(bot.addon_candidates['barracks_techlab'], [candidates[1]])
        await bot.execute('barracks_techlab')
        candidates[0].build.assert_not_called()
        candidates[1].build.assert_called_once()
        bot.client._query_building_placement_fast.return_value = [False, False]
        bot.can_place_single.side_effect = [False, False]
        await bot.prepare_macro_options()
        self.assertIsNone(bot.expansion_target)
        self.assertEqual(bot.addon_candidates['barracks_techlab'], [])

    def test_reserved_addon_footprint_blocks_later_construction(self):
        from sc2.position import Point2
        from src.rl.terran import avoids_addons
        site = Point2((2.5, -.5))
        self.assertFalse(avoids_addons(site, 1, [site]))
        self.assertFalse(avoids_addons(site.offset((1.9, 0)), 1, [site]))
        self.assertTrue(avoids_addons(site.offset((2, 0)), 1, [site]))
