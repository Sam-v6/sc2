import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root=Path.cwd()
old=json.loads((root/'logs/roadmap/joint-entity-fit-contract-01.json').read_text())
command=list(old['command'])
command[command.index('--output')+1]=str(root/'logs/roadmap/joint-entity-fit-02')
command.append('--refinement')
baseline=root/'logs/roadmap/joint-entity-fit-01/policy.npz'
contract=dict(old, command=command, expected_optimizer_updates=44400,
              refinement=True, baseline_checkpoint_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
              initial_model='Fresh same seed7000/7001; no baseline checkpoint continuation',
              comparison='Same200epoch/update budget, datasets, seed, width/rate/batch. Combined actor-ranking and spatial-conditioning/tile-loss changes; no component-specific attribution.',
              budget_reason='Prior measured200epoch complete fit483.316seconds; retain900second wall bound for this comparable experiment',
              scope='One refined human supervised fit; reused diagnostics only; no native/RL or professional claim')
(root/'logs/roadmap/joint-entity-fit-contract-02.json').write_text(json.dumps(contract,indent=2)+'\n')
environment=dict(os.environ,OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',PYTHONPATH=str(root))
result=subprocess.run(command,env=environment,timeout=1050)
sys.exit(result.returncode)
