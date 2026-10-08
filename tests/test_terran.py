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
        from types import SimpleNamespace
        bot.state = SimpleNamespace(game_loop=224)
        bot.attacking = True
        await bot.execute('retreat')
        self.assertFalse(bot.attacking)
        self.assertTrue(bot.stance_changed)
        self.assertEqual(bot.stance_changed_at, bot.time)

    async def test_gathering_precedes_macro_command(self):
        from types import SimpleNamespace
        from unittest.mock import AsyncMock
        bot = TerranLearner(Policy(FEATURES, ACTIONS), False, '/tmp/unused-actions.jsonl')
        bot.state = SimpleNamespace(game_loop=0)
        bot.combat_score = lambda: {'killed': 0, 'lost': 0}
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


class CapacityTests(unittest.TestCase):
    def test_capacity_rewards_worker_progress_but_not_spending_without_progress(self):
        from src.rl.terran import capacity_potential
        before = capacity_potential(encode({'workers': 12, 'bases': 1, 'minerals': 500}))
        spent = capacity_potential(encode({'workers': 12, 'bases': 1, 'minerals': 0}))
        worker = capacity_potential(encode({'workers': 13, 'bases': 1, 'minerals': 450}))
        self.assertLessEqual(reward(before, spent, .998), 0)
        self.assertGreater(reward(before, worker, .998), 0)
        self.assertAlmostEqual(before, 8)

    def test_encoder_distinguishes_travel_and_stance_age_under_fog(self):
        outbound = encode({'army_distance_home': 80, 'army_distance_enemy_start': 20, 'stance_seconds': 15})
        home = encode({'army_distance_home': 5, 'army_distance_enemy_start': 95, 'stance_seconds': 1})
        for feature in ('army_distance_home', 'army_distance_enemy_start', 'stance_seconds'):
            self.assertNotEqual(outbound[FEATURES.index(feature)], home[FEATURES.index(feature)])


class CompositionTests(unittest.TestCase):
    def snapshot(self, kinds):
        from types import SimpleNamespace
        from sc2.position import Point2
        from sc2.units import Units
        from sc2.ids.unit_typeid import UnitTypeId as U
        from unittest.mock import Mock
        origin = Point2((0, 0))
        units = Units([SimpleNamespace(type_id=kind, position=origin, _proto=SimpleNamespace(pos=origin),
            health=45, shield=0, ground_dps=6, air_dps=0, is_flying=False, is_structure=False,
            detect_range=0, is_cloaked=False, is_snapshot=False, is_visible=True) for kind in kinds], None)
        empty = Units([], None)
        bot = SimpleNamespace(army_units=lambda: units, units=units, enemy_units=empty, enemy_structures=empty,
                              game_info=SimpleNamespace(playable_area=SimpleNamespace(x=0,y=0,width=128,height=128)),
                              townhalls=empty, start_location=origin, time=100, minerals=500,
                              vespene=200, supply_left=10, supply_workers=12, supply_army=10,
                              structures=empty, gas_buildings=empty, attacking=False, game_seconds=1200,
                              already_pending=Mock(return_value=0), state=SimpleNamespace(upgrades=set()),
                              enemy_start_locations=[Point2((100, 0))], stance_changed_at=0)
        return TerranLearner.snapshot(bot)

    def test_equal_supply_armies_are_distinguished_in_live_state(self):
        from sc2.ids.unit_typeid import UnitTypeId as U
        hellions = self.snapshot([U.HELLION] * 5)
        vikings = self.snapshot([U.VIKINGFIGHTER] * 5)
        self.assertFalse(np.array_equal(encode(hellions), encode(vikings)))
        self.assertEqual(hellions['hellions'], 5)
        self.assertEqual(vikings['vikings'], 5)

    def test_live_counts_include_transformed_units_and_reapers(self):
        from sc2.ids.unit_typeid import UnitTypeId as U
        state = self.snapshot([U.REAPER, U.HELLION, U.HELLIONTANK, U.VIKINGFIGHTER, U.VIKINGASSAULT])
        self.assertEqual((state['reapers'], state['hellions'], state['vikings']), (1, 2, 2))

    def test_prior_schema_requires_explicit_checkpoint_migration(self):
        import tempfile
        from pathlib import Path
        from src.rl.actor_critic import ActorCritic
        old = [key for key in FEATURES if key not in ('reapers', 'hellions', 'vikings')]
        with tempfile.TemporaryDirectory() as folder:
            checkpoint = Path(folder) / 'old.npz'
            ActorCritic(old, ACTIONS).save(checkpoint)
            with self.assertRaisesRegex(ValueError, 'schema'):
                ActorCritic.load(checkpoint, FEATURES, ACTIONS)


class DetectionTests(unittest.IsolatedAsyncioTestCase):
    def test_policy_can_choose_prerequisite_gated_detectors(self):
        from src.rl.terran import BUILDINGS, UNITS
        from sc2.ids.unit_typeid import UnitTypeId as U
        self.assertIn('raven', ACTIONS)
        self.assertIn('turret', ACTIONS)
        self.assertEqual(UNITS['raven'], (U.RAVEN, U.STARPORT, True))
        self.assertEqual(BUILDINGS['turret'], U.MISSILETURRET)
        state = CompositionTests().snapshot([U.RAVEN])
        self.assertEqual(state['ravens'], 1)
        self.assertEqual(state['turrets'], 0)
        self.assertEqual(state['enemy_cloaked'], 0)

    async def test_raven_follows_combat_units_and_does_not_receive_attack_order(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from sc2.position import Point2
        from sc2.units import Units
        from sc2.ids.unit_typeid import UnitTypeId as U
        bot = TerranLearner(Policy(FEATURES, ACTIONS), False, '/tmp/unused-actions.jsonl')
        bot.state = SimpleNamespace(game_loop=0)
        bot.game_info = SimpleNamespace(player_start_location=Point2((0, 0)), map_center=Point2((100, 100)), start_locations=[Point2((100, 0))])
        bot.next_gather = 100
        def unit(kind, x):
            return SimpleNamespace(type_id=kind, position=Point2((x, 0)),
                                   _proto=SimpleNamespace(pos=Point2((x, 0))),
                                   move=Mock(), attack=Mock(), is_idle=True)
        raven, marine, medivac = unit(U.RAVEN, 0), unit(U.MARINE, 20), unit(U.MEDIVAC, 30)
        bot.units = Units([raven, marine, medivac], bot)
        bot.structures = bot.townhalls = bot.enemy_units = bot.enemy_structures = Units([], bot)
        await bot.micro()
        raven.move.assert_called_once_with(marine.position)
        raven.attack.assert_not_called()
        medivac.move.assert_called_once_with(marine.position)
        marine.attack.assert_called_once()


class FiniteMatchTests(unittest.IsolatedAsyncioTestCase):
    async def test_normal_match_endpoints_are_terminal_and_only_wins_pay(self):
        import tempfile
        from pathlib import Path
        from sc2.data import Result
        from src.rl.actor_critic import ActorCritic
        for result, bonus in ((Result.Victory, 100), (Result.Defeat, 0), (Result.Tie, 0)):
            with tempfile.TemporaryDirectory() as folder:
                policy = ActorCritic(FEATURES, ACTIONS)
                bot = TerranLearner(policy, True, Path(folder)/'actions.jsonl')
                bot.started, bot.callback_error = True, None
                bot.snapshot = lambda: {'workers': 20, 'bases': 1}
                bot.legal_mask = lambda: np.ones(len(ACTIONS), dtype=bool)
                bot.previous_score = {'killed': 0, 'lost': 0}
                bot.combat_score = lambda: {'killed': 0, 'lost': 0}
                bot.previous = (encode({'workers': 12, 'bases': 1}), 0, 8)
                bot.decisions = [{'action': 'wait'}]
                await bot.custom_on_end(result)
                self.assertTrue(bot.transitions[-1][-1])
                self.assertAlmostEqual(bot.transitions[-1][2], .01*(bonus-8))
                self.assertEqual(bot.decisions[-1]['reward_components']['potential_next'], 0)

    def test_full_return_is_discounted_win_minus_current_potential(self):
        from src.rl.actor_critic import ActorCritic
        policy = ActorCritic(['state'], ['wait'])
        policy.gamma = .9
        policy.network[5][...] = .3
        potentials = [8, 10, 9, 0]
        for won in (False, True):
            policy.rollout.clear()
            transitions = []
            for index in range(3):
                terminal = index == 2
                outcome = 100 if terminal and won else 0
                shaped = .01 * reward(potentials[index], potentials[index+1], policy.gamma, outcome)
                transitions.append((np.array([0.]), 0, shaped, np.array([0.]), np.array([True]), terminal))
            policy.collect_episode(transitions, [np.array([True])]*3)
            for index, row in enumerate(policy.rollout):
                expected = policy.gamma**(2-index)*int(won)-.01*potentials[index]
                self.assertAlmostEqual(row[5], expected)
                self.assertAlmostEqual(row[4], expected-.3)

    def test_live_state_exposes_match_horizon(self):
        state = CompositionTests().snapshot([])
        self.assertEqual(state['match_limit'], 1200)
        self.assertEqual(state['remaining_time'], 1100)
        self.assertNotEqual(encode(state)[FEATURES.index('remaining_time')], encode({})[FEATURES.index('remaining_time')])
