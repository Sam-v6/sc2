import json
from pathlib import Path
import subprocess

root=Path.cwd()
previous=json.loads((root/'logs/roadmap/joint-entity-fit-05/configuration.json').read_text())
teaching=[s['dataset'] for s in previous['sources'] if s['role']=='teaching']
teaching += [str(root/f'logs/roadmap/pro-demonstrations-05/{idx}') for idx in (294,870)]
validation=[str(root/'logs/roadmap/pro-demonstrations-05/774')]
command=[str((root/'.venv/bin/python').absolute()),'-m','src.learning.entity_train',
    '--train',*teaching,'--validation',*validation,'--output',
    str(root/'logs/roadmap/joint-professional-fit-02'),
    '--epochs','50','--batch-size','16','--hidden','32','--rate','0.001',
    '--refinement','--actor-cutoff','--spatial','--missing-fields',
    '--seed','8100','--wall-seconds','600']
print(json.dumps(dict(command=command,cpu_threads=2,rl_updates=0)),flush=True)
raise SystemExit(subprocess.run(command,check=False).returncode)
