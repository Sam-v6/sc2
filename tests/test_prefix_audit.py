import unittest
from src.learning.prefix_audit import roundtrip


class PrefixAuditTests(unittest.TestCase):
    def test_teacher_arguments_roundtrip_actor_target_queue_and_reflection(self):
        state = {
            "player": {},
            "game_loop": 0,
            "units": [
                {
                    "tag": 1,
                    "unit_type": 18,
                    "alliance": 1,
                    "position": [80.0, 20.0, 0.0],
                },
                {
                    "tag": 2,
                    "unit_type": 45,
                    "alliance": 1,
                    "position": [82.0, 20.0, 0.0],
                },
            ],
            "owned_memory": [],
            "map_size": [100.0, 100.0],
        }
        command = {
            "ability": 319,
            "units": [2],
            "target_point": [75.0, 25.0],
            "target_unit": None,
            "queue": True,
            "autocast": False,
        }
        self.assertEqual(
            roundtrip(command, state, [18, 45], {319: {"target": 2}}, 16), []
        )

    def test_irrecoverable_actors_are_reported(self):
        state = {
            "player": {},
            "game_loop": 0,
            "units": [
                {
                    "tag": 1,
                    "unit_type": 18,
                    "alliance": 1,
                    "position": [20.0, 20.0, 0.0],
                },
                {
                    "tag": 2,
                    "unit_type": 45,
                    "alliance": 1,
                    "position": [25.0, 25.0, 0.0],
                },
                {
                    "tag": 3,
                    "unit_type": 45,
                    "alliance": 1,
                    "position": [25.0, 25.0, 0.0],
                },
            ],
            "owned_memory": [],
            "map_size": [100.0, 100.0],
        }
        command = {
            "ability": 319,
            "units": [3],
            "target_point": [30.0, 30.0],
            "target_unit": None,
            "queue": False,
            "autocast": False,
        }
        self.assertIn(
            "units", roundtrip(command, state, [18, 45], {319: {"target": 2}}, 16)
        )
