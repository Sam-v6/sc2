import gzip
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.learning.gameplay import Command

try:
    from src.learning.entity_examples import (
        state_inputs,
        command_label,
        decode_command,
        replay_examples,
    )
except ImportError:
    state_inputs = command_label = decode_command = None


class EntityExamplesTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(state_inputs, "causal entity examples are missing")
        self.tag = 2**63 + 17
        self.state = dict(
            game_loop=100,
            map_size=[10, 6],
            player={"minerals": 50},
            units=[
                dict(
                    tag=self.tag,
                    unit_type=2,
                    alliance=1,
                    position=[2, 3, 0],
                    health=40,
                    health_max=45,
                ),
                dict(tag=12, unit_type=5, alliance=4, position=[8, 2, 0], health=20),
            ],
            owned_memory=[
                dict(
                    tag=25, unit_type=2, alliance=1, position=[1, 2, 0], observed=False
                )
            ],
            memory=[dict(tag=30, unit_type=5, position=[9, 2, 0], last_seen_loop=80)],
            recent_commands=[],
            upgrades=[],
        )
        self.inputs = state_inputs(self.state, 8, 12)

    def test_map_candidates_cover_edges_without_inserting_the_human_target(self):
        np.testing.assert_array_equal(self.inputs["world_points"], [[4, 3], [9, 3]])
        before = self.inputs["world_points"].copy()
        for point in ((0, 0), (10, 6), (8.123, 4.321)):
            command = Command(3, (self.tag,), target_point=point)
            label = command_label(command, self.inputs, (0, 1, 8), 8)
            decoded = decode_command(dict(label, delay=8), self.inputs)
            np.testing.assert_allclose(decoded.target_point, point, atol=1e-6)
            self.assertEqual(Command.from_proto(decoded.to_proto()).units, (self.tag,))
        np.testing.assert_array_equal(self.inputs["world_points"], before)

    def test_fog_memory_is_context_only_with_no_hidden_health_or_target_eligibility(
        self,
    ):
        tags = self.inputs["tags"]
        self.assertFalse(self.inputs["target_mask"][tags.index(30)])
        self.assertFalse(self.inputs["actor_mask"][tags.index(30)])
        self.assertTrue(self.inputs["actor_mask"][tags.index(25)])
        changed = dict(
            self.state, memory=[dict(self.state["memory"][0], health=1000, energy=200)]
        )
        np.testing.assert_array_equal(
            state_inputs(changed, 8, 12)["encoder"][0], self.inputs["encoder"][0]
        )
        with self.assertRaises(ValueError):
            command_label(
                Command(3, (self.tag,), target_unit=30), self.inputs, (0, 1, 8), 8
            )

    def test_large_tags_and_raw_command_modes_roundtrip_exactly(self):
        commands = [
            Command(3, (self.tag, 25), queue=True),
            Command(3, (self.tag,), target_unit=12, queue=True),
            Command(3, (self.tag,), autocast=True),
        ]
        for command in commands:
            label = command_label(command, self.inputs, (0, 1, 8), None)
            self.assertIsNone(label["delay"])
            self.assertEqual(decode_command(label, self.inputs), command)

    def test_entity_references_include_the_oldest_of_32_commands(self):
        command = dict(
            ability=3, units=[self.tag], target_unit=12, game_loop=80, queue=True
        )
        changed = dict(
            self.state,
            recent_commands=[command]
            + [dict(command, units=[25], target_unit=None)] * 31,
        )
        inputs = state_inputs(changed, 8, 12)
        features = inputs["encoder"][0]
        self.assertGreater(
            np.linalg.norm(
                features[inputs["tags"].index(self.tag)]
                - self.inputs["encoder"][0][self.inputs["tags"].index(self.tag)]
            ),
            0,
        )
        self.assertEqual(len(inputs["encoder"][4]), 32)
        with self.assertRaises(ValueError):
            state_inputs(
                dict(self.state, recent_commands=[dict(command, game_loop=101)]), 8, 12
            )

    def test_same_frame_burst_keeps_every_command_and_causal_history(self):
        first = Command(3, (self.tag,), queue=True)
        second = Command(4, (25,), target_unit=12)
        row = dict(
            observation=self.state,
            action_loop=101,
            commands=[first.as_dict(), second.as_dict()],
            next_action_delay=None,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "static.json").write_text(
                json.dumps(
                    {"game_info": {"start_raw": {"map_size": {"x": 10, "y": 6}}}}
                )
            )
            with gzip.open(path / "examples.jsonl.gz", "wt") as stream:
                stream.write(json.dumps(row) + "\n")
            examples = list(replay_examples(path, 8, 12, 0, (0, 1, 8)))
        self.assertEqual(len(examples), 2)
        self.assertEqual(examples[0][1]["delay"], 0)
        self.assertIsNone(examples[1][1]["delay"])
        self.assertEqual(list(examples[0][0]["encoder"][4]), [])
        self.assertEqual(list(examples[1][0]["encoder"][4]), [3])
        self.assertEqual(decode_command(examples[1][1], examples[1][0]), second)

    def test_unobserved_target_is_reported_without_losing_later_burst_commands(self):
        missing = Command(3, (self.tag,), target_unit=999)
        later = Command(4, (25,))
        row = dict(
            observation=self.state,
            action_loop=101,
            commands=[missing.as_dict(), later.as_dict()],
            next_action_delay=8,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "static.json").write_text(
                json.dumps(
                    {"game_info": {"start_raw": {"map_size": {"x": 10, "y": 6}}}}
                )
            )
            with gzip.open(path / "examples.jsonl.gz", "wt") as stream:
                stream.write(json.dumps(row) + "\n")
            examples = list(replay_examples(path, 8, 12, 0, (0, 1, 8)))
        self.assertEqual(len(examples), 2)
        self.assertIsNone(examples[0][1])
        self.assertTrue(examples[0][3])
        self.assertIsNone(examples[1][3])
        self.assertEqual(list(examples[1][0]["encoder"][4]), [3])
        self.assertEqual(decode_command(examples[1][1], examples[1][0]), later)


if __name__ == "__main__":
    unittest.main()
