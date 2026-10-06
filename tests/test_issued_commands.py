import unittest
from src.learning.issued_commands import issued_rows


def event(loop, data, flags=256):
    return {
        "_event": "NNet.Game.SCmdEvent",
        "_gameloop": loop,
        "_userid": {"m_userId": 1},
        "m_data": data,
        "m_cmdFlags": flags,
    }


def command(point=None, target=None):
    return {
        "ability": 1 if point or target else 524,
        "units": [7],
        "target_point": point,
        "target_unit": target,
        "autocast": False,
        "queue": False,
    }


class IssuedCommandTests(unittest.TestCase):
    def test_queue_identity_is_checked_before_accepting_same_target(self):
        rows = [{"action_loop": 20, "commands": [command(point=[1.0, 2.0])]}]
        selected, audit = issued_rows(
            rows, [event(20, {"TargetPoint": {"x": 4096, "y": 8192}}, flags=258)], 1
        )
        self.assertEqual(selected, [])
        self.assertEqual(audit["matched_issued_commands"], 0)
        rows[0]["commands"][0]["queue"] = True
        selected, _ = issued_rows(
            rows, [event(20, {"TargetPoint": {"x": 4096, "y": 8192}}, flags=258)], 1
        )
        self.assertEqual(len(selected), 1)

    def test_repeats_are_excluded_and_delay_recomputed_from_issued_events(self):
        rows = [{"action_loop": t, "commands": [command()]} for t in (20, 24, 30)]
        selected, audit = issued_rows(
            rows, [event(20, {"None": None}), event(30, {"None": None})], 1
        )
        self.assertEqual([r["action_loop"] for r in selected], [20, 30])
        self.assertEqual(selected[0]["next_action_delay"], 10)
        self.assertEqual(audit["excluded_engine_commands"], 1)

    def test_same_loop_target_update_is_not_mistaken_for_new_command(self):
        rows = [{"action_loop": 20, "commands": [command(point=[1.0, 2.0]), command()]}]
        selected, audit = issued_rows(rows, [event(20, {"None": None})], 1)
        self.assertEqual(selected[0]["commands"], [command()])
        self.assertEqual(audit["matched_issued_commands"], 1)

    def test_missing_or_ambiguous_events_are_audited_without_fake_waits(self):
        rows = [{"action_loop": 20, "commands": [command(), command()]}]
        selected, audit = issued_rows(
            rows, [event(20, {"None": None}), event(30, {"None": None})], 1
        )
        self.assertEqual(selected, [])
        self.assertEqual(len(audit["unresolved_events"]), 2)

    def test_target_unit_protocol_tag_matches_raw_tag_without_future_state(self):
        rows = [{"action_loop": 20, "commands": [command(target=0x101040001)]}]
        selected, _ = issued_rows(
            rows, [event(20, {"TargetUnit": {"m_tag": 0x1040001}})], 1
        )
        self.assertEqual(len(selected), 1)
