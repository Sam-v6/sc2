import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import preflight as run


class PreflightTests(unittest.TestCase):
    def test_fixed_cases_and_competence_require_all_races(self):
        bank=run.cases();self.assertEqual(len(bank),12)
        for race in ['Terran','Protoss','Zerg']:
            own=[c for c in bank if c['race']==race]
            self.assertEqual([c['map'] for c in own].count('Simple64'),2)
            self.assertEqual([c['map'] for c in own].count('TritonLE'),2)
        rows=[{**c,'status':'completed','episode_audit':{'passed':True},'result':'Victory'} for c in bank]
        self.assertTrue(run.gate(rows)['competent'])
        for row in rows:
            if row['race']=='Zerg':row['result']='Defeat'
        self.assertEqual(run.gate(rows)['wins'],8);self.assertFalse(run.gate(rows)['competent'])
        with self.assertRaises(AssertionError):run.gate(rows[:-1]+[rows[0]])

    def test_worker_failure_stops_and_harvests_all_four(self):
        stop=threading.Event()
        def supervise(function,args,timeout,stop_event):
            if args[0]['seed']==0:return {'status':'error','error':'native failed'}
            stop_event.wait(1);return {'status':'cancelled'}
        with patch('preflight.supervise',side_effect=supervise),patch('preflight.validate',side_effect=AssertionError('incomplete')):
            rows=run.collect([{'seed':i} for i in range(4)],stop)
        self.assertTrue(stop.is_set());self.assertEqual(len(rows),4)
        self.assertEqual(rows[0]['episode_status'],'error');self.assertEqual(rows[0]['error'],'native failed')
        with self.assertRaises(AssertionError):run.collect([{}]*5,threading.Event())

    def test_receipt_interrupt_preserves_known_games_and_unstarted_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            jobs=[{**case,'receipt':str(root/f'{case["seed"]}.json'),'journal':str(root/f'{case["seed"]}.journal')} for case in run.cases()]
            (root/'inputs.json').write_text(json.dumps({'workers':4,'hashes':{},'jobs':jobs}))
            original_write=run.write;interrupted=False
            def write(path,value):
                nonlocal interrupted
                if str(path).endswith('125000.json') and not interrupted:
                    interrupted=True;raise KeyboardInterrupt()
                original_write(path,value)
            with patch.object(run,'ARM',root),patch.object(run,'merge',return_value={}),patch.object(run,'verify'),\
                 patch.object(run,'digest',return_value='test'),patch.object(run,'write',side_effect=write),\
                 patch.object(run.budget,'baseline',return_value=0),\
                 patch.object(run.budget,'monitor',side_effect=lambda stop,done,windows:done.wait()),\
                 patch.object(run,'collect',side_effect=lambda jobs,stop:[{**j,'status':'completed','result':'Defeat',
                    'episode_audit':{'passed':True}} for j in jobs]):
                run.run()
                with self.assertRaises(AssertionError):run.run()
            summary=json.loads((root/'summary.json').read_text());ledger=json.loads((root/'ledger.json').read_text())
            self.assertFalse(summary['completed']);self.assertEqual(summary['fits'],0)
            self.assertEqual(summary['validated_games'],4);self.assertEqual(len(ledger),12)
            self.assertEqual(sum(row['status']=='not_started' for row in ledger),8)
            self.assertTrue(all(Path(j['receipt']).exists() for j in jobs))


if __name__=='__main__':unittest.main()
