import gzip
import json
from pathlib import Path
import tempfile
import unittest
from src.learning.teacher_states import teacher_states


class TeacherStateTests(unittest.TestCase):
    def rows(self, modern):
        own = {
            "tag": 7,
            "unit_type": 45,
            "alliance": 1,
            "position": [1.0, 2.0],
            "health": 45,
        }
        command = {
            "ability": 1,
            "units": [7],
            "queue": False,
            "target_unit": None,
            "target_point": None,
            "autocast": False,
        }
        first = {"units": [own], "game_loop": 9, "recent_commands": [{"ability": 295}]}
        second = {"units": [], "game_loop": 19}
        if modern:
            first["owned_memory"] = []
            second["owned_memory"] = []
        return [
            {"observation": first, "action_loop": 10, "commands": [command]},
            {"observation": second, "action_loop": 20, "commands": []},
        ]

    def reconstruct(self, modern):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            (directory / "static.json").write_text(
                json.dumps(
                    {"game_info": {"start_raw": {"map_size": {"x": 64, "y": 64}}}}
                )
            )
            with gzip.open(directory / "examples.jsonl.gz", "wt") as stream:
                for row in self.rows(modern):
                    stream.write(json.dumps(row) + "\n")
            return list(teacher_states(directory))

    def test_history_contains_only_prior_human_commands(self):
        rows = self.reconstruct(False)
        self.assertEqual(rows[0][1]["recent_commands"], [])
        self.assertEqual(rows[1][1]["recent_commands"][0]["ability"], 1)
        self.assertEqual(rows[1][1]["recent_commands"][0]["game_loop"], 10)
        self.assertNotIn("health", rows[1][1]["owned_memory"][0])

    def test_authoritative_memory_does_not_resurrect_dead_own_units(self):
        rows = self.reconstruct(True)
        self.assertEqual(rows[1][1]["owned_memory"], [])
