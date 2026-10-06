import unittest
from s2clientprotocol import sc2api_pb2 as pb, raw_pb2 as raw
from src.learning.gameplay import Command

try:
    from src.learning.demonstrations import ReplayExamples
except ImportError:
    ReplayExamples = None


def packet(loop, minerals=0, actions=()):
    p = pb.ResponseObservation(actions=actions)
    p.observation.game_loop = loop
    p.observation.player_common.minerals = minerals
    return p


class DemonstrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ReplayExamples, "Replay-to-action alignment is missing")

    def test_actions_use_state_strictly_before_issue_loop_not_post_action_resources(
        self,
    ):
        examples = ReplayExamples()
        examples.push(packet(42, 100))
        examples.push(packet(43, 150))
        examples.push(packet(44, 100))
        action = Command(524, (101,)).to_proto()
        action.game_loop = 44
        rows = examples.push(packet(45, 50, [action]))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["observation"]["game_loop"], 43)
        self.assertEqual(rows[0]["observation"]["player"]["minerals"], 150)
        self.assertEqual(rows[0]["action_loop"], 44)
        self.assertEqual(rows[0]["commands"][0]["ability"], 524)

    def test_multiaction_bursts_are_preserved_in_order_and_ui_is_counted(self):
        examples = ReplayExamples()
        for i in range(3):
            examples.push(packet(i))
        a = Command(16, (1,), target_point=(10.0, 20.0)).to_proto()
        a.game_loop = 2
        b = Command(23, (2,), target_unit=9, queue=True).to_proto()
        b.game_loop = 2
        ui = pb.Action(
            action_raw=raw.ActionRaw(camera_move=raw.ActionRawCameraMove()), game_loop=3
        )
        rows = examples.push(packet(3, actions=[a, ui, b]))
        self.assertEqual(len(rows), 1)
        self.assertEqual([c["units"] for c in rows[0]["commands"]], [[1], [2]])
        self.assertTrue(rows[0]["commands"][1]["queue"])
        self.assertEqual(examples.counts["gameplay"], 2)
        self.assertEqual(examples.counts["ui"], 1)

    def test_missing_prestate_or_untranslated_gameplay_fails_instead_of_silent_wait(
        self,
    ):
        examples = ReplayExamples()
        examples.push(packet(0))
        a = Command(524, (1,)).to_proto()
        a.game_loop = 0
        with self.assertRaises(ValueError):
            examples.push(packet(1, actions=[a]))
        examples = ReplayExamples()
        examples.push(packet(0))
        examples.push(packet(1))
        feature = pb.Action(game_loop=1)
        feature.action_feature_layer.unit_command.ability_id = 23
        with self.assertRaises(ValueError):
            examples.push(packet(2, actions=[feature]))
        examples = ReplayExamples()
        examples.push(packet(0))
        with self.assertRaises(ValueError):
            examples.push(packet(8))

    def test_timestamp_only_replay_record_is_counted_without_losing_gameplay(self):
        examples = ReplayExamples()
        examples.push(packet(12579))
        examples.push(packet(12580))
        empty = pb.Action(game_loop=12580)
        command = Command(23, (1,), target_point=(10.0, 20.0)).to_proto()
        command.game_loop = 12580
        rows = examples.push(packet(12581, actions=[empty, command]))
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0]["commands"], [Command.from_proto(command).as_dict()]
        )
        self.assertEqual(examples.counts["empty"], 1)
        self.assertEqual(examples.counts["gameplay"], 1)
        with self.assertRaises(ValueError):
            examples.push(packet(12582, actions=[pb.Action()]))


class TimingTests(unittest.TestCase):
    def test_next_delay_is_a_label_and_last_action_has_no_fabricated_delay(self):
        from src.learning.demonstrations import label_timing

        rows = [
            {"action_loop": 10, "commands": [{"ability": 16}]},
            {"action_loop": 14, "commands": [{"ability": 23}]},
        ]
        labeled = list(label_timing(iter(rows)))
        self.assertEqual(labeled[0]["next_action_delay"], 4)
        self.assertIsNone(labeled[1]["next_action_delay"])
        self.assertNotIn("next_action_delay", rows[0])

    def test_same_loop_groups_merge_without_reordering_queued_commands(self):
        from src.learning.demonstrations import label_timing

        rows = [
            {"action_loop": 10, "commands": [{"ability": 16}]},
            {"action_loop": 10, "commands": [{"ability": 23, "queue": True}]},
            {"action_loop": 20, "commands": [{"ability": 4}]},
        ]
        labeled = list(label_timing(iter(rows)))
        self.assertEqual(len(labeled), 2)
        self.assertEqual(
            labeled[0]["commands"], [{"ability": 16}, {"ability": 23, "queue": True}]
        )
        self.assertEqual(labeled[0]["next_action_delay"], 10)
