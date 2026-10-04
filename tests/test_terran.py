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
        bot.micro = AsyncMock(side_effect=lambda: order.append('gather'))
        bot.execute = AsyncMock(side_effect=lambda action: order.append('macro'))
        await bot.custom_on_step(0)
        self.assertEqual(order, ['gather', 'macro'])
