from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from src.processing.replay_video import validate_frame, validate_inputs, check_encoder
from src.processing.replay_video import check_replay_start
from src.processing.replay_video import overview_request
from s2clientprotocol import sc2api_pb2 as pb


class ReplayTests(unittest.TestCase):
    def test_overview_is_valid_protocol_request(self):
        request = pb.Request(**overview_request(64, 64))
        self.assertTrue(request.SerializeToString())
    def test_successful_replay_has_no_error_field(self):
        check_replay_start(pb.ResponseStartReplay())

    def test_present_replay_error_is_reported(self):
        with self.assertRaises(RuntimeError):
            check_replay_start(pb.ResponseStartReplay(error=1, error_details='map unavailable'))
    def test_missing_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                validate_inputs(Path(directory) / 'none.SC2Replay', Path(directory) / 'none.SC2Map')

    def test_empty_rgb(self):
        frame = SimpleNamespace(size=SimpleNamespace(x=640, y=480), bits_per_pixel=24, data=b'')
        with self.assertRaises(ValueError):
            validate_frame(frame, 640, 480)

    def test_wrong_dimensions(self):
        frame = SimpleNamespace(size=SimpleNamespace(x=2, y=1), bits_per_pixel=24, data=b'123456')
        with self.assertRaises(ValueError):
            validate_frame(frame, 1, 2)

    def test_nonzero_encoder_exit(self):
        with self.assertRaises(RuntimeError):
            check_encoder(1)

    def test_rgb_size(self):
        frame = SimpleNamespace(size=SimpleNamespace(x=2, y=1), bits_per_pixel=24, data=b'123456')
        self.assertEqual(validate_frame(frame, 2, 1), b'123456')


class ReplayLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_terminal_without_rgb_finishes_without_step(self):
        from unittest.mock import AsyncMock
        from src.processing.replay_video import record_frames
        server = SimpleNamespace(_execute=AsyncMock(return_value=pb.Response(
            observation=pb.ResponseObservation(player_result=[pb.PlayerResult(player_id=1, result=pb.Defeat)]), status=pb.ended)))
        encoder = SimpleNamespace(stdin=SimpleNamespace(write=lambda data: self.fail('terminal has no frame')))
        telemetry, ended = await record_frames(server, encoder, {'max_frames': 2, 'width': 2, 'height': 2, 'step': 8})
        self.assertTrue(ended)
        self.assertEqual(telemetry, [])
        self.assertEqual(server._execute.await_count, 1)

    async def test_ended_status_fetches_delayed_results_without_step(self):
        from unittest.mock import AsyncMock
        from src.processing.replay_video import record_frames
        server = SimpleNamespace(_execute=AsyncMock(side_effect=[
            pb.Response(observation=pb.ResponseObservation(), status=pb.ended),
            pb.Response(observation=pb.ResponseObservation(player_result=[pb.PlayerResult(player_id=1, result=pb.Defeat)]), status=pb.ended)]))
        encoder = SimpleNamespace(stdin=SimpleNamespace(write=lambda data: self.fail('no frame')))
        _, ended = await record_frames(server, encoder, {'max_frames': 2, 'width': 2, 'height': 2, 'step': 8})
        self.assertTrue(ended)
        self.assertTrue(all('observation' in call.kwargs for call in server._execute.await_args_list))

    async def test_render_failure_preserves_original_error(self):
        from unittest.mock import AsyncMock, Mock, patch
        from src.processing import replay_video
        with tempfile.TemporaryDirectory() as directory:
            replay = Path(directory) / 'game.SC2Replay'
            replay.write_bytes(b'test')
            server = SimpleNamespace(_execute=AsyncMock(return_value=pb.Response(start_replay=pb.ResponseStartReplay())))
            process = Mock(_arguments={})
            process.__aenter__ = AsyncMock(return_value=server)
            process.__aexit__ = AsyncMock(return_value=False)
            encoder = Mock()
            encoder.wait.return_value = -9
            encoder.stdin.close.side_effect = BrokenPipeError("cleanup pipe flush")
            job = {'replay': str(replay), 'map': str(replay), 'library': '/fake/library', 'width': 2,
                   'height': 2, 'output': str(Path(directory) / 'game.mp4'), 'player': 1,
                   'omniscient': False, 'camera': 'base', 'fps': 4}
            with patch.object(replay_video, 'validate_inputs'), patch.object(replay_video, 'get_replay_version', return_value=('Base75689', 'hash')), \
                 patch.object(Path, 'is_file', return_value=True), patch.object(replay_video, 'SC2Process', return_value=process), \
                 patch.object(replay_video.subprocess, 'Popen', return_value=encoder), \
                 patch.object(replay_video, 'record_frames', side_effect=ValueError('original invalid RGB')):
                with self.assertRaisesRegex(ValueError, 'original invalid RGB'):
                    await replay_video.render(job)
            encoder.kill.assert_called_once()
            encoder.wait.assert_called_once()

    async def test_early_failure_receipt_survives_new_directory(self):
        import json
        from unittest.mock import patch
        from src.processing import replay_video
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'new' / 'game.mp4'
            with patch('sys.argv', ['replay_video', 'game.SC2Replay', '--map-file', 'map.SC2Map', '--output', str(output)]), \
                 patch.object(replay_video, 'validate_inputs'), \
                 patch.object(replay_video, 'supervise', return_value={'status': 'error', 'result': None, 'error': 'missing build'}):
                with self.assertRaises(SystemExit):
                    replay_video.main()
            self.assertEqual(json.loads(output.with_suffix('.export.json').read_text())['error'], 'missing build')
