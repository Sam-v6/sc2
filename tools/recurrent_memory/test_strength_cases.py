import unittest
from strength_cases import training_cases,evaluation_cases,gate


class CasesTests(unittest.TestCase):
    def test_training_is_balanced_across_difficulties_and_maps(self):
        cases=training_cases();self.assertEqual(len(cases),64)
        self.assertEqual({x['seed'] for x in cases},set(range(121000,121064)))
        for difficulty in ['Medium','Hard']:
            panel=[x for x in cases if x['difficulty']==difficulty]
            self.assertEqual(len(panel),32)
            self.assertEqual({x['map'] for x in panel},{'Simple64','TritonLE'})
            self.assertEqual({x['race'] for x in panel},{'Terran','Protoss','Zerg'})

    def rows(self):
        return [{**case,'role':role,'result':'Victory' if role!='reference' or case['seed']%3==0 else 'Defeat',
                 'discounted_return':1 if role!='reference' else .2} for case in evaluation_cases() for role in ['recurrent','reset','reference']]

    def test_gate_accepts_either_arm_without_claiming_memory_when_tied(self):
        result=gate(self.rows())
        self.assertEqual(result['selected_role'],'reset')
        self.assertTrue(result['supported']['recurrent'])
        self.assertFalse(result['memory_advantage'])

    def test_retention_and_duplicate_cases_fail_closed(self):
        rows=self.rows()
        for row in rows:
            if row['phase']=='easy_sampled' and row['role']!='reference':row['result']='Defeat';row['discounted_return']=-1
        self.assertIsNone(gate(rows)['selected_role'])
        rows=self.rows();rows[-1]=rows[0]
        with self.assertRaises(AssertionError):gate(rows)


if __name__=='__main__':unittest.main()
