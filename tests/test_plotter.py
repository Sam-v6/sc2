from pathlib import Path
import tempfile
import unittest
import pandas as pd
from src.processing.plotter import Plotter


class PlotterTests(unittest.TestCase):
    def test_multiple_match_telemetry_plots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('a', 'b'):
                pd.DataFrame({'game_time': [0., 10., 20.],
                              'collection_rate_minerals': [0., 100., 200.],
                              'collection_rate_vespene': [0., 20., 40.],
                              'current_apm': [0., 10., 20.]}).to_parquet(root / f'{name}.parquet')
            Plotter(str(root)).plot()
            for name in ('minerals_rate.png', 'gas_rate.png', 'apm.png', 'columns.txt'):
                self.assertGreater((root / 'plots' / name).stat().st_size, 0)
