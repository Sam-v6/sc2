import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path.cwd()
inventory = json.loads((root/'logs/roadmap/expanded-human-macro-01/contract.json').read_text())['train_inventory']
output = root/'logs/roadmap/joint-entity-fit-01'
validation = [root/'logs/roadmap/issued-timing-masked-01/issued-50925', root/'logs/roadmap/issued-51960-p1']
command = [str((root/'.venv/bin/python').absolute()), '-m', 'src.learning.entity_train',
           '--train', *[r['dataset'] for r in inventory], '--validation', *map(str, validation),
           '--output', str(output), '--epochs', '200', '--batch-size', '16',
           '--hidden', '32', '--rate', '0.001', '--seed', '7000', '--wall-seconds', '900']
smoke = root/'logs/roadmap/joint-entity-throughput-01/report.json'
contract = dict(command=command, initial_model='Fresh deterministic seed; throughput checkpoint is not reused',
                smoke_report_sha256=hashlib.sha256(smoke.read_bytes()).hexdigest(),
                smoke_epoch_seconds=json.loads(smoke.read_text())['history'][0]['seconds'],
                budget_reason='200 epochs at measured 2.4 seconds each, 900 second fitting wall cap; one fixed architecture/configuration, no sweep',
                expected_optimizer_updates=44400, cpu='CPU-only, two BLAS/OMP threads',
                teaching_gate=dict(ability_fraction=.95, actors_fraction=.90, complete_fraction=.75,
                                   point_tolerance_tiles=1, denominator='All 3543 teaching commands including exclusions',
                                   timing='Report separately; native gate is not implied'),
                validation='Reused Lyra and Huski whole-replay diagnostics, not fresh acceptance',
                reserved_replays_not_opened=['51483', '51886'],
                scope='Human command supervised fit and reconstruction audit; no professional/native/micro/RL claim')
(root/'logs/roadmap/joint-entity-fit-contract-01.json').write_text(json.dumps(contract, indent=2)+'\n')
environment = dict(os.environ, OPENBLAS_NUM_THREADS='2', OMP_NUM_THREADS='2', PYTHONPATH=str(root))
result = subprocess.run(command, env=environment, timeout=1050)
sys.exit(result.returncode)
