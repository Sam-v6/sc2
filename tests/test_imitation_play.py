import unittest
import numpy as np

try:
    from src.learning.imitation_play import decode_commands
except ImportError:
    decode_commands = None


class ImitationPlayTests(unittest.TestCase):
    def predictions(self):
        return {
            "ability": np.zeros((1, 600)),
            "mode": np.array([[0.0, 0.0, 10.0, 0.0]]),
            "target_type": np.array([[0.0, 0.0, 10.0]]),
            "alliance": np.array([[0.0, 0.0, 0.0, 0.0, 10.0]]),
            "queue": np.array([[0.0, 10.0]]),
            "delay": np.zeros((1, 10)),
            "point": np.array([[5 / 128, 0.0]]),
        }

    def test_live_targets_remap_to_current_tags_and_engine_rules_mask_abilities(self):
        self.assertIsNotNone(decode_commands)
        own = {"tag": 10, "unit_type": 48, "alliance": 1, "position": [10.0, 10.0, 0.0]}
        enemy = {
            "tag": 99,
            "unit_type": 105,
            "alliance": 4,
            "position": [15.0, 10.0, 0.0],
        }
        output = self.predictions()
        output["ability"][0, 23] = 10
        output["ability"][0, 524] = 20
        commands, rows = decode_commands(
            {"units": [own, enemy]},
            [own],
            output,
            {10: {23}},
            {23: {"target": 4}},
            [48, 105],
            (64, 64),
        )
        self.assertEqual(commands[0].ability, 23)
        self.assertEqual(commands[0].target_unit, 99)
        self.assertTrue(commands[0].queue)
        self.assertEqual(rows[0]["raw_ability"], 524)
        self.assertEqual(rows[0]["ability"], 23)

    def test_no_target_and_empty_availability_do_not_fabricate_targets(self):
        self.assertIsNotNone(decode_commands)
        own = {"tag": 10, "unit_type": 48, "alliance": 1, "position": [10.0, 10.0, 0.0]}
        output = self.predictions()
        output["ability"][0, 524] = 10
        commands, _ = decode_commands(
            {"units": [own]},
            [own],
            output,
            {10: {524}},
            {524: {"target": 1}},
            [48, 105],
            (64, 64),
        )
        self.assertIsNone(commands[0].target_unit)
        self.assertIsNone(commands[0].target_point)
        self.assertEqual(
            decode_commands(
                {"units": [own]},
                [own],
                output,
                {10: set()},
                {524: {"target": 1}},
                [48, 105],
                (64, 64),
            )[0],
            [],
        )


class WorkerExecutionTests(unittest.TestCase):
    def test_idle_worker_execution_preserves_ongoing_and_current_model_orders(self):
        from src.learning.imitation_play import idle_worker_harvest

        units = [
            {"tag": 1, "unit_type": 45, "alliance": 1, "position": [1.0, 1.0]},
            {"tag": 2, "unit_type": 45, "alliance": 1, "position": [2.0, 1.0]},
            {
                "tag": 3,
                "unit_type": 45,
                "alliance": 1,
                "position": [2.0, 1.0],
                "orders": [{"ability_id": 319}],
            },
            {"tag": 4, "unit_type": 45, "alliance": 1, "position": [2.0, 1.0]},
            {
                "tag": 5,
                "unit_type": 341,
                "alliance": 3,
                "position": [3.0, 1.0],
                "mineral_contents": 900,
            },
        ]
        commands = idle_worker_harvest({"units": units}, {4})
        self.assertEqual(len(commands), 2)
        self.assertEqual([c.units for c in commands], [(1,), (2,)])
        self.assertEqual(commands[0].target_unit, 5)
