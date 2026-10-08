from pathlib import Path
import json
import os
import subprocess
import sys
import unittest


class LowLoadTests(unittest.TestCase):
    def test_limits_are_inherited_without_changing_parent(self):
        affinity=sorted(os.sched_getaffinity(0));priority=os.getpriority(os.PRIO_PROCESS,0)
        probe="import json,os; print(json.dumps({'cores':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'cuda':os.environ.get('CUDA_VISIBLE_DEVICES'),'software':os.environ.get('LIBGL_ALWAYS_SOFTWARE'),'threads':[os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')]}))"
        child="import subprocess,sys; subprocess.run([sys.executable,'-c',sys.argv[1]],check=True)"
        wrapper=Path(__file__).absolute().parents[1]/'tools/low_load.py'
        result=subprocess.run([sys.executable,str(wrapper),sys.executable,'-c',child,probe],capture_output=True,text=True,check=True)
        state=json.loads(result.stdout)
        self.assertEqual(state['cores'],affinity[-8:])
        self.assertEqual(state['nice'],min(priority+10,19))
        self.assertEqual(state['cuda'],'')
        self.assertEqual(state['software'],'1')
        self.assertEqual(state['threads'],['1','1','1'])
        self.assertEqual(sorted(os.sched_getaffinity(0)),affinity)
        self.assertEqual(os.getpriority(os.PRIO_PROCESS,0),priority)
