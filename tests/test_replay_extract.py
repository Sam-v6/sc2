import tempfile
import unittest
from pathlib import Path
from s2clientprotocol import sc2api_pb2 as pb, common_pb2 as common

try:
    from src.learning.replay_extract import (
        validate_replay_info,
        require_engine,
        load_protocol,
    )
except ImportError:
    validate_replay_info = require_engine = load_protocol = None


class ReplayPreflightTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(validate_replay_info, "Replay preflight is missing")

    def test_missing_build_fails_before_engine_launch(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileNotFoundError):
                require_engine(Path(folder), "Base75689")
            p = Path(folder) / "Versions/Base75689/SC2_x64"
            p.parent.mkdir(parents=True)
            p.touch()
            self.assertEqual(require_engine(Path(folder), "Base75689"), p)

    def test_teacher_is_terran_and_not_a_computer_or_anonymous_pro_claim(self):
        info = pb.ResponseReplayInfo()
        info.player_info.add().player_info.CopyFrom(
            pb.PlayerInfo(player_id=1, type=pb.Participant, race_actual=common.Terran)
        )
        self.assertEqual(
            validate_replay_info(info, 1)["teacher_kind"], "human_unverified"
        )
        with self.assertRaises(ValueError):
            validate_replay_info(info, 2)
        info.player_info[0].player_info.type = pb.Computer
        with self.assertRaises(ValueError):
            validate_replay_info(info, 1)
        info.player_info[0].player_info.type = pb.Participant
        info.player_info[0].player_info.race_actual = common.Protoss
        with self.assertRaises(ValueError):
            validate_replay_info(info, 1)

    def test_official_replay_decoder_works_on_python312_without_imp(self):
        protocol = load_protocol(75689)
        self.assertTrue(callable(protocol.decode_replay_game_events))
        with self.assertRaises(FileNotFoundError):
            load_protocol(123456789)
