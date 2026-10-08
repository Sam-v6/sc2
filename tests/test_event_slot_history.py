import gzip
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from src.learning.entity_examples import replay_examples


class EventSlotHistoryTests(unittest.TestCase):
    def test_source_event_slots_survive_teacher_conversion(self):
        state = dict(
            game_loop=10,
            player={},
            units=[dict(tag=1, unit_type=2, alliance=1, position=[2, 3, 0])],
            upgrades=[],
            unknown_fields=dict(world=["command_history"]),
            history_quality="event_slots",
            recent_commands=[dict(game_loop=8, unknown=True)],
        )
        row = dict(
            action_loop=10,
            observation=state,
            commands=[dict(ability=3, units=[1])],
            next_action_delay=None,
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "static.json").write_text(
                json.dumps(
                    dict(game_info=dict(start_raw=dict(map_size=dict(x=10, y=6))))
                )
            )
            with gzip.open(root / "examples.jsonl.gz", "wt") as stream:
                stream.write(json.dumps(row) + "\n")
            examples = list(
                replay_examples(root, 8, 12, 0, (0, 1, 8), missing_fields=True)
            )
        self.assertEqual(len(examples), 1)
        np.testing.assert_array_equal(examples[0][0]["encoder"][4], [0])
        self.assertIsNone(examples[0][1]["delay"])

    def test_source_event_slots_require_one_row_per_original_event(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "static.json").write_text(
                json.dumps(
                    dict(game_info=dict(start_raw=dict(map_size=dict(x=10, y=6))))
                )
            )
            row = dict(
                action_loop=10,
                observation=dict(
                    game_loop=10,
                    player={},
                    units=[],
                    upgrades=[],
                    history_quality="event_slots",
                    recent_commands=[],
                ),
                commands=[dict(ability=3, units=[1]), dict(ability=4, units=[1])],
                next_action_delay=None,
            )
            with gzip.open(root / "examples.jsonl.gz", "wt") as stream:
                stream.write(json.dumps(row) + "\n")
            with self.assertRaisesRegex(ValueError, "one row per original event"):
                list(replay_examples(root, 8, 12, 0, (0, 1, 8), missing_fields=True))
