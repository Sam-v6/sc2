import unittest
from src.learning.production_scout import WorkerScout
from tests.test_terran_primitives import unit


def state(loop, workers):
    return dict(
        game_loop=loop,
        units=workers
        + [
            unit(100, 21),
            unit(101, 18),
            unit(200, 999, alliance=3, mineral_contents=1000),
        ],
        owned_memory=[],
    )


class ScoutTests(unittest.TestCase):
    def test_only_ready_barracks_and_idle_mining_unprotected_worker_can_start(self):
        scout = WorkerScout()
        st = state(1688, [unit(1, 45), unit(2, 45), unit(3, 45)])
        st["units"][1]["orders"] = [dict(ability_id=318)]
        commands = scout.update(st, {1}, (100, 100), (0, 0))
        self.assertEqual(commands[0].units, (3,))
        self.assertEqual(scout.protected, {3})
        scout = WorkerScout()
        st["units"][3]["build_progress"] = 0.5
        self.assertEqual(scout.update(st, {1}, (100, 100), (0, 0)), [])

    def test_no_start_before_window_or_after_it(self):
        for loop in [0, 1680, 3024]:
            scout = WorkerScout()
            self.assertEqual(
                scout.update(state(loop, [unit(1, 45)]), set(), (100, 100), (0, 0)), []
            )
            self.assertFalse(scout.protected)

    def test_protection_persists_when_move_order_needs_no_repeat(self):
        scout = WorkerScout()
        st = state(1688, [unit(1, 45)])
        scout.update(st, set(), (100, 100), (0, 0))
        st["units"][0]["orders"] = [
            dict(ability_id=16, target_world_space_pos=dict(x=100, y=100))
        ]
        self.assertEqual(scout.update(st, set(), (100, 100), (0, 0)), [])
        self.assertEqual(scout.protected, {1})

    def test_damage_or_deadline_returns_to_mining_once(self):
        for damaged in [True, False]:
            scout = WorkerScout()
            st = state(1688, [unit(1, 45)])
            scout.update(st, set(), (100, 100), (0, 0))
            st["game_loop"] = 2000 if damaged else 3032
            st["units"][0].update(health=20 if damaged else 45, health_max=45)
            commands = scout.update(st, set(), (100, 100), (0, 0))
            self.assertEqual((commands[0].ability, commands[0].target_unit), (295, 200))
            self.assertIsNone(scout.tag)
            self.assertEqual(scout.protected, {1})
            self.assertEqual(scout.update(st, set(), (100, 100), (0, 0)), [])
            self.assertFalse(scout.protected)

    def test_dead_or_macro_claimed_scout_is_not_commanded(self):
        for claimed in [True, False]:
            scout = WorkerScout()
            st = state(1688, [unit(1, 45)])
            scout.update(st, set(), (100, 100), (0, 0))
            if not claimed:
                st["units"] = st["units"][1:]
            self.assertEqual(
                scout.update(st, {1} if claimed else set(), (100, 100), (0, 0)), []
            )
            self.assertIsNone(scout.tag)

    def test_owned_memory_scout_is_not_marked_dead(self):
        scout = WorkerScout()
        st = state(1688, [unit(1, 45)])
        scout.update(st, set(), (100, 100), (0, 0))
        st["units"] = st["units"][1:]
        st["owned_memory"] = [dict(tag=1, unit_type=45, alliance=1)]
        self.assertEqual(scout.update(st, set(), (100, 100), (0, 0)), [])
        self.assertEqual(scout.protected, {1})

    def test_late_start_gets_full_bounded_outing(self):
        scout = WorkerScout()
        st = state(2184, [unit(1, 45)])
        scout.update(st, set(), (100, 100), (0, 0))
        st["game_loop"] = 3024
        st["units"][0]["orders"] = [
            dict(ability_id=16, target_world_space_pos=dict(x=100, y=100))
        ]
        self.assertEqual(scout.update(st, set(), (100, 100), (0, 0)), [])
        self.assertEqual(scout.tag, 1)
        self.assertEqual(scout.protected, {1})
        st["game_loop"] = 2184 + 1344
        commands = scout.update(st, set(), (100, 100), (0, 0))
        self.assertEqual(commands[0].ability, 295)
        self.assertIsNone(scout.tag)

    def test_memory_only_observation_does_not_extend_deadline(self):
        scout = WorkerScout()
        st = state(2184, [unit(1, 45)])
        scout.update(st, set(), (100, 100), (0, 0))
        st["units"] = st["units"][1:]
        st["owned_memory"] = [dict(tag=1, unit_type=45, alliance=1)]
        st["game_loop"] = 3024
        scout.update(st, set(), (100, 100), (0, 0))
        self.assertEqual(scout.tag, 1)
        st["game_loop"] = 3528
        scout.update(st, set(), (100, 100), (0, 0))
        self.assertIsNone(scout.tag)
        self.assertEqual(scout.events[0]["event"], "deadline_unobserved")
