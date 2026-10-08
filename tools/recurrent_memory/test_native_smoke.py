import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import native_smoke as smoke


class SmokeTests(unittest.TestCase):
    def test_interrupted_collection_harvests_every_started_job(self):
        def supervised(function,args,timeout,stop_event):
            if args[0]['seed']==0: raise KeyboardInterrupt()
            return {'status':'completed','result':'Defeat'}
        stop=threading.Event()
        with patch('native_smoke.supervise',side_effect=supervised):
            results=smoke.collect([{'seed':0},{'seed':1}],stop)
        self.assertTrue(stop.is_set());self.assertEqual(len(results),2)
        self.assertEqual(results[0]['status'],'interrupted')
        self.assertEqual(results[1]['status'],'completed')

    def test_interrupt_while_writing_receipt_preserves_both_known_results(self):
        with tempfile.TemporaryDirectory() as directory:
            arm=Path(directory)
            jobs=[{'role':role,'receipt':str(arm/f'{role}.json')} for role in ['recurrent','reset']]
            (arm/'inputs.json').write_text(json.dumps({'jobs':jobs,'workers':2,'hashes':{}}))
            original=smoke.write;interrupted=[]
            def write(path,value):
                if path==arm/'recurrent.json' and not interrupted:
                    interrupted.append(True);raise KeyboardInterrupt()
                original(path,value)
            with patch('native_smoke.ARM',arm),patch('native_smoke.write',side_effect=write),patch('native_smoke.budget.monitor'),patch('native_smoke.budget.baseline',return_value=0),patch('native_smoke.collect',return_value=[{'status':'completed','result':'Defeat'}]*2):
                smoke.run()
            self.assertTrue((arm/'recurrent.json').exists());self.assertTrue((arm/'reset.json').exists())
            summary=json.loads((arm/'summary.json').read_text())
            self.assertFalse(summary['completed']);self.assertEqual(summary['recorded_games'],2)

    def test_failed_fit_preserves_supervisor_error_and_failure_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            arm=Path(directory)
            jobs=[{'role':role,'receipt':str(arm/f'{role}.json')} for role in ['recurrent','reset']]
            (arm/'inputs.json').write_text(json.dumps({'jobs':jobs,'workers':2,'hashes':{}}))
            with patch('native_smoke.ARM',arm),patch('native_smoke.budget.monitor'),patch('native_smoke.budget.baseline',return_value=0),patch('native_smoke.collect',return_value=[{'status':'completed'}]*2),patch('native_smoke.supervise',return_value={'status':'error','error':'torch failed stderr'}):
                smoke.run()
            summary=json.loads((arm/'summary.json').read_text())
            self.assertFalse(summary['completed']);self.assertEqual(summary['recorded_games'],2)
            receipt=json.loads((arm/'recurrent-fit-supervision.json').read_text())
            self.assertEqual(receipt['error'],'torch failed stderr')
            self.assertFalse((arm/'reset-fit-supervision.json').exists())


if __name__=='__main__':unittest.main()
