import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import fixture as run


class FixtureTests(unittest.TestCase):
    def test_frozen_bank_covers_siege_unsiege_and_ground_structure(self):
        bank=run.cases();self.assertEqual([row['seed'] for row in bank],list(range(127000,127006)))
        self.assertEqual([row['target'] for row in bank],['OVERLORD']*4+['ROACH','SUPPLYDEPOT'])
        self.assertTrue(all(row['engineering_only'] and row['game_limit']==8 for row in bank))

    def test_receipt_interrupt_retains_all_submitted_results_and_rejects_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);jobs=[{**case,'receipt':str(root/f'{case["seed"]}.json')} for case in run.cases()]
            (root/'inputs.json').write_text(json.dumps({'workers':2,'hashes':{},'jobs':jobs}))
            original=run.write;interrupted=False
            def write(path,value):
                nonlocal interrupted
                if str(path).endswith('127000.json') and not interrupted:
                    interrupted=True;raise KeyboardInterrupt()
                original(path,value)
            with patch.object(run,'ARM',root),patch.object(run,'digest',return_value='test'),\
                 patch.object(run,'merge',return_value={}),patch.object(run,'verify'),\
                 patch.object(run,'write',side_effect=write),patch.object(run.budget,'baseline',return_value=0),\
                 patch.object(run.budget,'monitor',side_effect=lambda stop,done,windows:done.wait()),\
                 patch.object(run,'collect',side_effect=lambda jobs,stop:[{**job,'status':'completed'} for job in jobs]),\
                 patch.object(run,'validate',return_value={'passed':True}):
                run.run()
                with self.assertRaises(AssertionError):run.run()
            ledger=json.loads((root/'ledger.json').read_text());summary=json.loads((root/'summary.json').read_text())
            self.assertEqual(sum(row['status']=='completed' for row in ledger),2)
            self.assertEqual(sum(row['status']=='not_started' for row in ledger),4)
            self.assertFalse(summary['completed']);self.assertFalse(summary['physical_gate_passed'])
            self.assertTrue(all(Path(job['receipt']).exists() for job in jobs))

    def test_late_cpu_stop_prevents_physical_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);jobs=[{**case,'receipt':str(root/f'{case["seed"]}.json')} for case in run.cases()]
            (root/'inputs.json').write_text(json.dumps({'workers':2,'hashes':{},'jobs':jobs}))
            def monitor(stop,done,windows):done.wait();stop.set()
            with patch.object(run,'ARM',root),patch.object(run,'digest',return_value='test'),\
                 patch.object(run,'merge',return_value={}),patch.object(run,'verify'),\
                 patch.object(run.budget,'baseline',return_value=0),patch.object(run.budget,'monitor',side_effect=monitor),\
                 patch.object(run,'collect',side_effect=lambda jobs,stop:[{**job,'status':'completed'} for job in jobs]),\
                 patch.object(run,'validate',return_value={'passed':True}):run.run()
            summary=json.loads((root/'summary.json').read_text())
            self.assertFalse(summary['completed']);self.assertFalse(summary['physical_gate_passed'])
            self.assertEqual(summary['error'],'CPU guard stopped fixture')


if __name__=='__main__':unittest.main()
