import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import strength_study as study
from recurrent_worker import digest
from strength_validate import validate


class RuntimeTests(unittest.TestCase):
    def test_interrupted_round_harvests_all_eight_jobs(self):
        def run(function,args,timeout,stop_event):
            if args[0]['seed']==0:raise KeyboardInterrupt()
            return {'status':'completed'}
        stop=threading.Event()
        with patch('strength_study.supervise',side_effect=run):
            rows=study.collect([{'seed':i} for i in range(8)],stop)
        self.assertTrue(stop.is_set());self.assertEqual(len(rows),8)
        self.assertEqual(rows[0]['status'],'interrupted')
        with self.assertRaises(AssertionError):study.collect([{}]*9,threading.Event())

    def test_returned_supervisor_failure_stops_other_owned_jobs(self):
        stop=threading.Event()
        def run(function,args,timeout,stop_event):
            if args[0]['seed']==0:return {'status':'error','error':'engine failed'}
            stop_event.wait(1)
            return {'status':'cancelled' if stop_event.is_set() else 'completed'}
        with patch('strength_study.supervise',side_effect=run):
            results=study.collect([{'seed':i} for i in range(8)],stop)
        self.assertTrue(stop.is_set());self.assertEqual(len(results),8)
        self.assertTrue(all(row['status']=='cancelled' for row in results[1:]))

    def test_failed_fit_and_interrupted_receipt_preserve_all_known_outcomes(self):
        for interrupt in [False,True]:
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);cases=study.training_cases();evaluations=study.evaluation_cases()
                inputs={'hashes':{},'training_cases':cases,'evaluation_cases':evaluations,'workers':4,
                        'initial_models':{'recurrent':'unused','reset':'unused'}}
                (root/'inputs.json').write_text(json.dumps(inputs))
                def make_job(case,role,model,context):
                    return {**case,'role':role,'receipt':str(root/f'{case["seed"]}-{role}.json'),
                            **{key:str(root/'unused') for key in ['trajectory','actions','journal','replay']}}
                original_write=study.write;interrupted=False
                def write(path,value):
                    nonlocal interrupted
                    if interrupt and str(path).endswith('121000-recurrent.json') and not interrupted:
                        interrupted=True;raise KeyboardInterrupt()
                    original_write(path,value)
                with patch.object(study,'ARM',root),patch.object(study,'job',side_effect=make_job),\
                     patch.object(study,'merge',return_value={}),patch.object(study,'verify'),\
                     patch.object(study,'digest',return_value='test'),patch.object(study,'write',side_effect=write),\
                     patch.object(study.budget,'baseline',return_value=0),\
                     patch.object(study.budget,'monitor',side_effect=lambda stop,done,windows:done.wait()),\
                     patch.object(study,'collect',side_effect=lambda jobs,stop:[{'status':'completed'} for j in jobs]),\
                     patch.object(study,'validate',return_value={'passed':True,'discounted_return':0}),\
                     patch.object(study,'supervise',return_value={'status':'error','error':'fit failed'}):
                    study.run('train')
                    with self.assertRaises(AssertionError):study.run('train')
                summary=json.loads((root/'train-summary.json').read_text())
                self.assertFalse(summary['completed']);self.assertEqual(summary['recorded_games'],8)
                self.assertEqual(len(json.loads((root/'train-ledger.json').read_text())),8)
                self.assertTrue(all(Path(make_job(c,r,None,None)['receipt']).exists()
                                    for c in cases[:4] for r in ['recurrent','reset']))
                if not interrupt:self.assertEqual(json.loads((root/'recurrent-001.supervision.json').read_text())['status'],'error')

    def test_replaced_final_checkpoint_is_rejected_before_evaluation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);model=root/'recurrent-016.npz';model.write_bytes(b'final')
            expected=digest(model)
            (root/'inputs.json').write_text(json.dumps({'hashes':{},'training_cases':study.training_cases(),
                'evaluation_cases':study.evaluation_cases(),'workers':4,'initial_models':{'reset':'unused'}}))
            (root/'train-summary.json').write_text(json.dumps({'completed':True,
                'final_models':{'recurrent':str(model)},'final_model_hashes':{'recurrent':expected}}))
            (root/'recurrent-016.fit.json').write_text(json.dumps({'checkpoint':str(model),'sha256':expected,
                'optimizer_clock':256,'episodes':64}))
            summary=json.loads((root/'train-summary.json').read_text())
            summary['final_fit_receipt_hashes']={'recurrent':digest(root/'recurrent-016.fit.json')}
            (root/'train-summary.json').write_text(json.dumps(summary))
            model.write_bytes(b'replaced')
            with patch.object(study,'ARM',root),patch.object(study,'supervise') as supervisor:
                with self.assertRaises(AssertionError):study.run('evaluate')
                supervisor.assert_not_called()

    def test_binding_cannot_overwrite_changed_inherited_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'encoder';path.write_text('old');expected=digest(path)
            path.write_text('changed')
            with self.assertRaises(AssertionError):study.merge({str(path):expected},{str(path):digest(path)})

    def test_validator_accepts_verified_real_smoke_and_rejects_wrong_model_clock(self):
        root=Path('logs/recurrent-memory/native-smoke')
        inputs=json.loads((root/'inputs.json').read_text())
        for job in inputs['jobs']:
            receipt=json.loads(Path(job['receipt']).read_text())
            job={**job,'model_updates':0}
            self.assertTrue(validate(job,receipt)['passed'])
            with self.assertRaises(AssertionError):validate({**job,'model_updates':1},receipt)


if __name__=='__main__':unittest.main()
