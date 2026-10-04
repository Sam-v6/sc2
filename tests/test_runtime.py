import os
import subprocess
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from src import path
from src import runtime
import psutil


def running(pid):
    try:
        return psutil.Process(pid).status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False


def wait_stopped(pid):
    deadline = time.monotonic() + 1
    while running(pid) and time.monotonic() < deadline:
        time.sleep(0.01)
    return not running(pid)


def sleep_worker():
    time.sleep(30)


def spawn_descendant(pid_file):
    child = subprocess.Popen(['sleep', '30'])
    Path(pid_file).write_text(str(child.pid))
    time.sleep(30)


def leave_descendant():
    child = subprocess.Popen(['sleep', '30'])
    return {'status': 'completed', 'result': None, 'pid': child.pid}


class RuntimeTests(unittest.TestCase):
    def test_explicit_game_path(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {'SC2PATH': directory}):
                self.assertEqual(path.resolve_sc2_path(), Path(directory))

    def test_worktree_default_game_path(self):
        with patch.dict(os.environ, {}, clear=True):
            game = path.resolve_sc2_path()
        self.assertTrue((game / 'Versions/Base75689/SC2_x64').is_file())

    def test_unique_artifact_names(self):
        self.assertNotEqual(runtime.match_id(), runtime.match_id())

    def test_timeout_is_distinct(self):
        receipt = runtime.supervise(sleep_worker, (), timeout=0.1)
        self.assertEqual(receipt['status'], 'wall_timeout')
        self.assertIsNone(receipt['result'])

    def test_timeout_stops_descendant(self):
        with tempfile.TemporaryDirectory() as directory:
            pid_file = Path(directory) / 'pid'
            receipt = runtime.supervise(spawn_descendant, (str(pid_file),), timeout=1)
            self.assertEqual(receipt['status'], 'wall_timeout')
            pid = int(pid_file.read_text())
            self.assertTrue(wait_stopped(pid))

    def test_cancellation_stops_worker_and_descendant(self):
        import threading
        stop = threading.Event()
        timer = threading.Timer(1, stop.set)
        with tempfile.TemporaryDirectory() as directory:
            pid_file = Path(directory) / 'pid'
            timer.start()
            try:
                receipt = runtime.supervise(spawn_descendant, (str(pid_file),), timeout=30, stop_event=stop)
            finally:
                timer.cancel()
            self.assertEqual(receipt['status'], 'cancelled')
            self.assertTrue(wait_stopped(int(pid_file.read_text())))

    def test_finished_worker_leaves_no_descendant(self):
        receipt = runtime.supervise(leave_descendant, (), timeout=3)
        pid = receipt['pid']
        try:
            self.assertTrue(wait_stopped(pid))
        finally:
            try:
                if running(pid):
                    psutil.Process(pid).terminate()
            except psutil.NoSuchProcess:
                pass

    def test_invalid_config_rejected(self):
        from src.runner import parser
        with self.assertRaises(SystemExit):
            parser().parse_args(['--workers', '0'])

    def test_invalid_map_rejected(self):
        from src.runner import validate_map
        with self.assertRaises(FileNotFoundError):
            validate_map('DefinitelyMissingMap')


if __name__ == '__main__':
    unittest.main()
