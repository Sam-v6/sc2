import gzip
import json
from pathlib import Path
import tempfile
import unittest
from src.learning.teacher_states import teacher_states, remember_command


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
        rows = [
            {"observation": first, "action_loop": 10, "commands": [command]},
            {"observation": second, "action_loop": 20, "commands": []},
        ]
        if modern == "hybrid":
            rows.append(
                {
                    "observation": {"units": [], "game_loop": 29},
                    "action_loop": 30,
                    "commands": [],
                }
            )
        return rows

    def test_authoritative_death_remains_known_in_later_legacy_event_frames(self):
        rows = self.reconstruct("hybrid")
        self.assertEqual(rows[2][1]["owned_memory"], [])

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

    def test_command_roles_survive_actor_death_without_retaining_hidden_health(self):
        rows = self.reconstruct(True)
        command = rows[1][1]["recent_commands"][0]
        self.assertEqual(command["actor_types"], [45])
        self.assertNotIn("health", command)
        self.assertEqual(rows[1][1]["units"], [])

    def test_unknown_target_is_not_filled_from_later_observations(self):
        state = self.rows(False)[0]["observation"]
        command = dict(self.rows(False)[0]["commands"][0], target_unit=99)
        remembered = remember_command(command, state, 10)
        state["units"].append(
            {
                "tag": 99,
                "unit_type": 105,
                "alliance": 4,
                "position": [30.0, 40.0],
                "health": 145,
            }
        )
        self.assertEqual(remembered["target_type"], 0)
        self.assertEqual(remembered["target_position"], [])
        self.assertEqual(remembered["target_alliance"], 0)

    def test_authoritative_memory_does_not_resurrect_dead_own_units(self):
        rows = self.reconstruct(True)
        self.assertEqual(rows[1][1]["owned_memory"], [])
