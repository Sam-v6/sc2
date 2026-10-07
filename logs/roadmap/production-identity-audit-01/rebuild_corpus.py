"""Sequential guarded imports; preserve the prior professional corpus."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import psutil

root = Path(__file__).parent
code = 'import json,sys; from src.learning.tournament_import import import_game; r=import_game(json.load(open(sys.argv[1]))); print(json.dumps(dict(status=r["status"],commands=r["issued_command_audit"]["matched_issued_commands"],output=json.load(open(sys.argv[1]))["output"])))'
psutil.cpu_percent(None)
peak = 0.0
results = []
for game in ('294', '870', '955', '839', '991', '523'):
    old = Path('logs/roadmap/pro-preconverted-probe-01' if game in ('294', '870') else 'logs/roadmap/pro-corpus-expansion-01') / f'import-job-{game}-07.json'
    job = json.loads(old.read_text())
    job['reconciliation'] = str(root / 'audit.json')
    job['output'] = f'logs/roadmap/pro-demonstrations-production-08/{game}'
    path = root / f'import-job-{game}.json'
    path.write_text(json.dumps(job, indent=2)+'\n')
    env = dict(os.environ, OPENBLAS_NUM_THREADS='2', OMP_NUM_THREADS='2', CUDA_VISIBLE_DEVICES='', PYTHONPATH='.')
    start = time.monotonic(); streak = 0
    with (root / f'import-{game}.log').open('w') as stream:
        process = subprocess.Popen([sys.executable, '-c', code, str(path)], stdout=stream, stderr=stream, env=env, start_new_session=True)
        try:
            while process.poll() is None:
                cpu = psutil.cpu_percent(interval=.5)
                peak = max(peak, cpu)
                streak = streak+1 if cpu > 80 else 0
                if streak >= 3 or time.monotonic()-start > 120:
                    raise RuntimeError('CPU or wall guard triggered')
            if process.returncode:
                raise RuntimeError(f'Import {game} failed: see log')
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL); process.wait()
    result = dict(game=game, exit_code=process.returncode, wall_seconds=time.monotonic()-start,
                  job_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    results.append(result)
    print(json.dumps(result), flush=True)
receipt = dict(results=results, peak_host_cpu_percent=peak, cpu_guard_percent=80,
               cpu_only=True, training=False, rl=False,
               audit_sha256=hashlib.sha256((root/'audit.json').read_bytes()).hexdigest(),
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(root/'import-results.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt), flush=True)
