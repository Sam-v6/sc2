import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from fixture_semantics import interpret


class MorphologyTests(unittest.TestCase):
    def test_lowered_structure_identity_uses_unchanged_physical_requirements(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'trace.jsonl'
            enemy={'tag':7,'type':'SUPPLYDEPOTLOWERED','structure':True,'flying':False}
            path.write_text(json.dumps({'tanks':[{'enemies':[enemy]}]})+'\n')
            job={'trace':str(path),'target':'SUPPLYDEPOT'}
            row={'engineering_result':'Tie','status':'audit_failed'}
            with patch('fixture_semantics.validate',return_value={'passed':True}) as validator:
                audit=interpret(job,row)
            self.assertEqual(validator.call_args.args[0]['target'],'SUPPLYDEPOTLOWERED')
            self.assertEqual(audit['structure_identity_tag'],7);self.assertEqual(row['status'],'audit_failed')
            enemy['flying']=True;path.write_text(json.dumps({'tanks':[{'enemies':[enemy]}]})+'\n')
            with self.assertRaises(AssertionError):interpret(job,row)


if __name__=='__main__':unittest.main()
