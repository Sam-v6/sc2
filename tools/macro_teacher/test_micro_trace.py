import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import micro_trace as run


class TraceRunTests(unittest.TestCase):
    def test_fixed_observation_bank_has_no_strength_gate(self):
        bank=run.cases()
        self.assertEqual([row['seed'] for row in bank],list(range(126000,126004)))
        self.assertEqual([row['build'] for row in bank],['Rush','Timing','Air','Macro'])
        self.assertTrue(all(row['diagnostic_only'] and row['mode']=='evaluate' for row in bank))

    def test_trace_failure_preserves_all_native_outcomes_and_rejects_restart(self):
        original=run.preflight.episode
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            jobs=[{**case,'receipt':str(root/f'{case["seed"]}.json'),
                   'micro_trace':str(root/f'{case["seed"]}.trace')} for case in run.cases()]
            (root/'inputs.json').write_text(json.dumps({'workers':4,'hashes':{},'jobs':jobs}))
            with patch.object(run,'ARM',root),patch.object(run,'merge',return_value={}),patch.object(run,'verify'),\
                 patch.object(run,'digest',return_value='test'),patch.object(run.budget,'baseline',return_value=0),\
                 patch.object(run.budget,'monitor',side_effect=lambda stop,done,windows:done.wait()),\
                 patch.object(run.preflight,'collect',side_effect=lambda jobs,stop:[{**job,'status':'completed',
                    'result':'Defeat','micro_trace_bytes':10} for job in jobs]):
                run.run()
                with self.assertRaises(AssertionError):run.run()
            summary=json.loads((root/'summary.json').read_text())
            self.assertFalse(summary['completed']);self.assertEqual(summary['validated_games'],4)
            self.assertEqual(summary['fits'],0);self.assertFalse(summary['teacher_gate_changed'])
            self.assertTrue(all(Path(job['receipt']).exists() for job in jobs))
        self.assertIs(run.preflight.episode,original)


if __name__=='__main__':unittest.main()
