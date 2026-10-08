import unittest


class OccupancyTests(unittest.TestCase):
    def test_quiet_frames_exclude_issued_and_unresolved_command_windows(self):
        from src.learning.occupancy import occupancy_rows

        states = [
            {"game_loop": t, "units": [], "player": {"minerals": t}}
            for t in range(0, 25, 4)
        ]
        event = {
            "action_loop": 10,
            "observation": {"game_loop": 9, "units": []},
            "commands": [{"ability": 524}],
            "next_action_delay": 20,
        }
        rows = list(occupancy_rows(states, [event], 4, [21]))
        self.assertIn(event, rows)
        quiet = [r for r in rows if not r["commands"]]
        self.assertEqual([r["action_loop"] for r in quiet], [1, 5])
        self.assertTrue(
            all(r["observation"]["game_loop"] == r["action_loop"] - 1 for r in rows)
        )
        self.assertEqual(event["next_action_delay"], 20)

    def test_command_bursts_keep_order_and_no_wait_is_fabricated_at_event(self):
        from src.learning.occupancy import occupancy_rows

        event = {
            "action_loop": 5,
            "observation": {"game_loop": 4},
            "commands": [{"ability": 16}, {"ability": 23}],
        }
        result = list(occupancy_rows([{"game_loop": 4}], [event], 4, []))
        self.assertEqual(result, [event])

    def test_observation_clock_errors_fail(self):
        from src.learning.occupancy import occupancy_rows

        with self.assertRaises(ValueError):
            list(occupancy_rows([{"game_loop": 4}, {"game_loop": 4}], [], 4, []))


class OccupancyMetricTests(unittest.TestCase):
    def test_always_wait_cannot_hide_missing_production_behind_quiet_accuracy(self):
        import numpy as np
        from src.learning.imitation_train import metrics
        from src.learning.imitation import FactorPolicy

        policy = FactorPolicy(2, 3, [], seed=1)
        for value in policy.parameters.values():
            value[:] = 0
        policy.parameters["ability_bias"][0] = 10
        x = np.zeros((4, 2), dtype=np.float32)
        labels = {k: np.full(4, -1, dtype=int) for k in policy.sizes}
        labels.update(
            ability=np.array([0, 0, 0, 1]), point_valid=np.zeros(4, dtype=int)
        )
        report = metrics(policy, x, labels, np.full((4, 2), np.nan))
        self.assertEqual(report["quiet_accuracy"], 1)
        self.assertEqual(report["commanded_ability_accuracy"], 0)
        self.assertEqual(report["balanced_event_wait_accuracy"], 0.5)
