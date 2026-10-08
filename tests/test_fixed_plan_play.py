import unittest
import asyncio
from types import SimpleNamespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

try:
    from src.learning.fixed_plan_play import FixedHumanPlanBot
except ModuleNotFoundError:
    FixedHumanPlanBot = None


@unittest.skipIf(FixedHumanPlanBot is None, 'SC2 SDK unavailable')
class FixedPlanFoundationTests(unittest.TestCase):
    def test_supply_assistance_reserves_overdue_production_request(self):
        st = dict(game_loop=100, units=[], player=dict(minerals=240, vespene=200,
                  food_cap=23, food_used=20))
        context = SimpleNamespace(job=dict(reactive_supply=True),
                                  data=dict(abilities=[], units=[]),
                                  tickets=[dict(command=dict(ability=321))],
                                  costs={321: (150, 0)}, food={321: 0}, index=0,
                                  pending_heads=lambda loop: [0])
        self.assertIsNone(asyncio.run(FixedHumanPlanBot.reactive_supply_command(context, st, [], set())))
        context.job['reactive_supply'] = False
        self.assertIsNone(asyncio.run(FixedHumanPlanBot.reactive_supply_command(context, {}, [], set())))

    def test_due_landing_correction_replaces_only_unsubmitted_unqueued_destination(self):
        tickets = [dict(loop=10, name='Land Factory', command=dict(units=[1], target_point=[10, 10])),
                   dict(loop=20, name='Land Factory', command=dict(units=[1], target_point=[10, 11], queue=False))]
        context = SimpleNamespace(tickets=tickets, done=set(), history=[])
        FixedHumanPlanBot.retire_superseded_landings(context, 19)
        self.assertFalse(context.done)
        FixedHumanPlanBot.retire_superseded_landings(context, 20)
        self.assertEqual(context.done, {0})
        context.done.clear()
        tickets[1]['command']['queue'] = True
        FixedHumanPlanBot.retire_superseded_landings(context, 20)
        self.assertFalse(context.done)
        tickets[1]['command']['queue'] = False
        tickets[1]['name'] = 'Train Hellion'
        FixedHumanPlanBot.retire_superseded_landings(context, 20)
        self.assertFalse(context.done)

    def test_unsubmitted_build_can_be_replaced_only_without_a_source_foundation(self):
        tickets = [dict(loop=10, name='Build SupplyDepot', actor_types=[45],
                        command=dict(units=[1], target_point=[10, 10])),
                   dict(loop=20, name='Move builder', actor_types=[45],
                        command=dict(units=[1], queue=False))]
        context = SimpleNamespace(tickets=tickets, done=set(), history=[],
                                  source_product=lambda t, p: None)
        FixedHumanPlanBot.retire_superseded_worker_builds(context, 19)
        self.assertEqual(context.done, set())
        FixedHumanPlanBot.retire_superseded_worker_builds(context, 20)
        self.assertEqual(context.done, {0})
        context.done.clear()
        context.source_product = lambda t, p: 123
        FixedHumanPlanBot.retire_superseded_worker_builds(context, 20)
        self.assertEqual(context.done, set())
        context.source_product = lambda t, p: None
        tickets[1]['command']['queue'] = True
        FixedHumanPlanBot.retire_superseded_worker_builds(context, 20)
        self.assertEqual(context.done, set())

    def test_startup_failure_cannot_write_a_finished_episode(self):
        from src.learning.fixed_plan_play import play_fixed_human_plan
        record = dict(units=dict(fields={}, step=[]), steps=dict(game_loop=[]),
                      neutral=dict(fields=dict(id=[], pos=[])))
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'plan.json').write_text('{"tickets": []}')
            (root/'record.bin').write_bytes(b'')
            job = dict(plan=str(root/'plan.json'), record=str(root/'record.bin'),
                       output=str(root/'episode'), seed=1)
            with patch('src.learning.fixed_plan_play.decode_record', return_value=record), \
                 patch('src.learning.fixed_plan_play.validate_map'), \
                 patch('src.learning.fixed_plan_play.run_game', return_value=SimpleNamespace(name='Defeat')):
                with self.assertRaisesRegex(RuntimeError, 'No native fixed-plan frames'):
                    play_fixed_human_plan(job)
            self.assertFalse((root/'episode'/'episode.json').exists())

    def test_preposition_keeps_worker_and_queued_move_preserves_construction(self):
        actor = dict(tag=1, alliance=1, unit_type=45, position=[0, 0],
                     orders=[dict(ability_id=321)])
        context = SimpleNamespace(builder_tags={99: 1}, catalog={321: dict(friendly_name='Build Barracks')},
                                  start_location=[0, 0])
        state = dict(units=[actor])
        self.assertIsNone(FixedHumanPlanBot.choose_worker(context, 99, state, [10, 10], False))
        self.assertEqual(FixedHumanPlanBot.choose_worker(context, 99, state, [10, 10], True), actor)
        actor['orders'] = []
        self.assertEqual(FixedHumanPlanBot.choose_worker(context, 99, state, [10, 10], False), actor)

    def test_independent_producer_can_pass_a_blocked_actor(self):
        tickets = [dict(loop=10, command=dict(units=[1])),
                   dict(loop=20, command=dict(units=[1])),
                   dict(loop=20, command=dict(units=[2]))]
        context = SimpleNamespace(tickets=tickets, done=set())
        self.assertEqual(FixedHumanPlanBot.pending_heads(context, 20), [0, 2])
        context.done.add(0)
        self.assertEqual(FixedHumanPlanBot.pending_heads(context, 20), [1, 2])

    def test_cancel_retires_only_latest_unsubmitted_actor_request(self):
        tickets = [dict(loop=10, name='Train SCV', command=dict(units=[1], ability=524)),
                   dict(loop=20, name='Train SCV', command=dict(units=[1], ability=524)),
                   dict(loop=30, name='Cancel Last', command=dict(units=[1], ability=3671))]
        context = SimpleNamespace(tickets=tickets, done=set(), history=[])
        FixedHumanPlanBot.retire_unsubmitted_cancellations(context, 30)
        self.assertEqual(context.done, {1, 2})
        context = SimpleNamespace(tickets=tickets, done={1}, history=[])
        FixedHumanPlanBot.retire_unsubmitted_cancellations(context, 30)
        self.assertEqual(context.done, {1})
        self.assertEqual(context.history, [])

    def test_repeated_build_uses_current_source_foundation(self):
        context = SimpleNamespace(
            products={319: [19]},
            source_frames={5199: {123: dict(kind=19, point=[143, 69])}},
            entities={123: dict(loop=5180, kind=19, point=[143, 69]),
                      124: dict(loop=6000, kind=19, point=[143, 69])})
        ticket = dict(loop=5199, command=dict(ability=319))
        self.assertEqual(FixedHumanPlanBot.source_product(context, ticket, [143, 69]), 123)

    def test_new_foundation_requires_unique_source_identity(self):
        context = SimpleNamespace(
            products={321: [21]}, source_frames={100: {}},
            entities={123: dict(loop=120, kind=21, point=[131.5, 47.5])})
        ticket = dict(loop=100, command=dict(ability=321))
        self.assertEqual(FixedHumanPlanBot.source_product(context, ticket, [131.5, 47.5]), 123)
        context.entities[124] = dict(loop=140, kind=21, point=[131.5, 47.5])
        self.assertIsNone(FixedHumanPlanBot.source_product(context, ticket, [131.5, 47.5]))
