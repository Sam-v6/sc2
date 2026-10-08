import json
import os
from pathlib import Path
import subprocess
import sys

root=Path.cwd()
split=json.loads((root/'logs/roadmap/multiplayer-teacher-split-contract-01.json').read_text())
audit=json.loads((root/'logs/roadmap/multiplayer-teacher-split-audit-01.json').read_text())
assert audit['status']=='verified' and audit['results']['teaching']['representable']==4189
command=[str((root/'.venv/bin/python').absolute()),'-m','src.learning.entity_train',
         '--train',*split['teaching'],'--validation',*split['diagnostic'],
         '--output',str(root/'logs/roadmap/joint-entity-fit-05'),
         '--epochs','169','--batch-size','16','--hidden','32','--rate','0.001',
         '--seed','7000','--wall-seconds','1500','--refinement','--actor-cutoff','--spatial']
contract=dict(command=command,split=split,expected_optimizer_updates=44278,expected_example_passes=707941,
              previous_example_passes=707941,previous_optimizer_updates=44278,
              budget='Identical split, passes and updates to fit04; added spatial compute is not compute-matched',
              architecture='Refined cutoff model plus full-pixel spatial embedding/global context; added rows/bias/context zero; common initial parameter values unchanged, float32 spatial precision differs',
              teaching_gate=dict(ability_fraction=.95,actors_fraction=.90,complete_fraction=.75,point_tolerance_tiles=1,denominator='All4190commands including exclusions'),
              cpu='CPU-only two BLAS/OMP threads',reserved_replays_not_opened=['51483','51886'],
              validation='Separate Rom diagnostic, previously inspected source; not randomized fresh acceptance',
              scope='One three-player human supervised experiment; no native/RL/professional claim')
(root/'logs/roadmap/joint-entity-fit-contract-05.json').write_text(json.dumps(contract,indent=2)+'\n')
result=subprocess.run(command,env=dict(os.environ,OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',PYTHONPATH=str(root)),timeout=1650)
sys.exit(result.returncode)
