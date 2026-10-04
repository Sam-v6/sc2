import json
from pathlib import Path
import tempfile
import unittest
from src.processing.replay_plotter import plot_telemetry


class ReplayPlotterTests(unittest.TestCase):
    def test_replay_observations_produce_plot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / 'frames.json'
            data.write_text(json.dumps({'telemetry': [{'game_time': 0, 'minerals': 50, 'vespene': 0},
                                                     {'game_time': 10, 'minerals': 100, 'vespene': 25}]}))
            plot_telemetry(data, root / 'resources.png')
            self.assertGreater((root / 'resources.png').stat().st_size, 0)
