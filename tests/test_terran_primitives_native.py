"""Opt-in native economy/production gate using the installed game."""
import os
from pathlib import Path
import tempfile
import unittest

from src.runner import play_job
from src.runtime import supervise


@unittest.skipUnless(os.getenv('SC2_PRIMITIVE_SMOKE'), 'Opt-in native SC2 game')
class NativePrimitiveTests(unittest.TestCase):
    def test_baseline_collects_resources_and_produces_workers_and_army(self):
        with tempfile.TemporaryDirectory() as output:
            job = dict(bot='primitives', race='Zerg', difficulty='VeryEasy', build='Macro',
                       map='AcropolisLE', seed=818001, game_step=8, game_seconds=240,
                       dev=False, replay=str(Path(output)/'game.SC2Replay'))
            result = supervise(play_job, (job,), 90)
            self.assertIn(result['status'], ('completed', 'truncated'), result)
            metrics = result['primitives']
            self.assertGreaterEqual(metrics['worker_peak'], 18)
            self.assertGreaterEqual(metrics['army_peak'], 3)
            self.assertGreater(metrics['collected_minerals'], 1000)
            self.assertGreater(metrics['mining_commands'], 0)
            self.assertTrue(Path(output, 'game.primitives.jsonl.gz').is_file())
