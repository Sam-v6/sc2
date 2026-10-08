import json
import os
from pathlib import Path
import subprocess
import sys

root = Path.cwd()
inventory = json.loads((root/'logs/roadmap/expanded-human-macro-01/contract.json').read_text())['train_inventory']
command = [str((root/'.venv/bin/python').absolute()), '-m', 'src.learning.entity_train',
           '--train', *[r['dataset'] for r in inventory],
           '--output', str(root/'logs/roadmap/joint-entity-throughput-01'),
           '--epochs', '1', '--batch-size', '16', '--hidden', '32', '--rate', '0.001',
           '--seed', '7000', '--wall-seconds', '120']
(root/'logs/roadmap/joint-entity-throughput-command-01.json').write_text(json.dumps(dict(command=command, scope='One-epoch bounded CPU throughput smoke, unpromoted; no native game or RL'), indent=2)+'\n')
environment = dict(os.environ, OPENBLAS_NUM_THREADS='2', OMP_NUM_THREADS='2', PYTHONPATH=str(root))
result = subprocess.run(command, env=environment, timeout=240)
sys.exit(result.returncode)
