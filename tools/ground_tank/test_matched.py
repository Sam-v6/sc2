import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import matched as run
import matched_worker as worker


class MatchedTests(unittest.TestCase):
    def test_case_pairs_and_competence_require_all_races_and_control_retention(self):
        bank=run.cases();self.assertEqual(len(bank),24)
        for seed in range(128000,128012):
            pair=[row for row in bank if row['seed']==seed]
            self.assertEqual([row['role'] for row in pair],['control','candidate'])
            for key in ['map','race','build','policy_seed']:self.assertEqual(pair[0][key],pair[1][key])
        rows=[{**case,'status':'completed','result':'Victory','episode_audit':{'passed':True,'discounted_return':.5}} for case in bank]
        self.assertTrue(run.gate(rows)['competent'])
        for row in rows:
            if row['role']=='candidate' and row['race']=='Terran':row['result']='Defeat'
        self.assertFalse(run.gate(rows)['competent'])
        with self.assertRaises(AssertionError):run.gate(rows[:-1]+[rows[0]])

    def test_worker_restores_observer_after_candidate_error(self):
        original=worker.teacher_worker.ObservedLearner
        def fail(job):
            self.assertIs(worker.teacher_worker.ObservedLearner.micro,worker.ground_micro)
            raise RuntimeError('native error')
        with patch.object(worker.teacher_worker,'episode',side_effect=fail):
            with self.assertRaisesRegex(RuntimeError,'native error'):
                worker.episode({'experiment':'ground-tank-matched','role':'candidate','micro_version':'ground-tank-v1'})
        self.assertIs(worker.teacher_worker.ObservedLearner,original)

    def test_receipt_interrupt_retains_all_four_native_outcomes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);jobs=[{**case,'receipt':str(root/f'{case["seed"]}-{case["role"]}.json')} for case in run.cases()]
            (root/'inputs.json').write_text(json.dumps({'workers':4,'hashes':{},'jobs':jobs}))
            original=run.preflight.persist;interrupted=False
            def persist(rows):
                nonlocal interrupted
                if not interrupted:interrupted=True;raise KeyboardInterrupt()
                original(rows)
            previous=run.preflight.episode
            with patch.object(run,'ARM',root),patch.object(run,'digest',return_value='test'),\
                 patch.object(run,'merge',return_value={}),patch.object(run,'verify'),\
                 patch.object(run.budget,'baseline',return_value=0),\
                 patch.object(run.budget,'monitor',side_effect=lambda stop,done,windows:done.wait()),\
                 patch.object(run.preflight,'persist',side_effect=persist),\
                 patch.object(run.preflight,'collect',side_effect=lambda jobs,stop:[{**job,'status':'completed'} for job in jobs]):
                run.run()
                with self.assertRaises(AssertionError):run.run()
            ledger=json.loads((root/'ledger.json').read_text());summary=json.loads((root/'summary.json').read_text())
            self.assertEqual(sum(row['status']=='completed' for row in ledger),4)
            self.assertEqual(sum(row['status']=='not_started' for row in ledger),20)
            self.assertFalse(summary['completed']);self.assertEqual(summary['fits'],0)
            self.assertTrue(all(Path(job['receipt']).exists() for job in jobs))
            self.assertIs(run.preflight.episode,previous)


if __name__=='__main__':unittest.main()
