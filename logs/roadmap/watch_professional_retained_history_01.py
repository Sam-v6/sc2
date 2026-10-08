"""Whole-host CPU guard for one bounded human imitation fit."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

root = Path.cwd()
script = root / 'logs/roadmap/run_professional_retained_history_01.py'
receipt = root / 'logs/roadmap/professional-retained-history-01.telemetry.json'
assert not receipt.exists()
runtime = '/home/sam/repos/hobby-repos/exoplanet/.venv/bin/python'
env = dict(os.environ, OPENBLAS_NUM_THREADS='2', OMP_NUM_THREADS='2', CUDA_VISIBLE_DEVICES='',
           PYTHONPATH=f'.:{root}/.venv/lib/python3.12/site-packages', SC2_IMITATION_WATCHDOG=str(Path(__file__).absolute()))
record = dict(status='running', watchdog_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              script_sha256=hashlib.sha256(script.read_bytes()).hexdigest(), logical_cpus=psutil.cpu_count(),
              cpu_limit=80, samples=[], stop_reason=None, runtime=runtime)
child = subprocess.Popen([runtime, '-W', 'ignore::DeprecationWarning', str(script)], cwd=root, env=env)
record['pid'] = child.pid
high = 0
while child.poll() is None:
    cpu = psutil.cpu_percent(interval=1)
    try:
        rss = psutil.Process(child.pid).memory_info().rss
    except psutil.NoSuchProcess:
        rss = 0
    record['samples'].append(dict(unix_time=time.time(), whole_cpu_percent=cpu,
                                  memory_percent=psutil.virtual_memory().percent, process_rss_bytes=rss))
    high = high + 1 if cpu > 80 else 0
    if high >= 3:
        record['stop_reason'] = 'Whole-host CPU above80percent on three consecutive samples'
        child.terminate()
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
    receipt.write_text(json.dumps(record, indent=2) + '\n')
    if child.poll() is None:
        time.sleep(4)
record.update(returncode=child.wait(), status='completed' if child.returncode == 0 else 'stopped')
receipt.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(dict(watchdog_status=record['status'], returncode=record['returncode'], samples=len(record['samples']),
                      max_cpu=max((s['whole_cpu_percent'] for s in record['samples']), default=0), stop_reason=record['stop_reason'])), flush=True)
sys.exit(0 if child.returncode == 0 else 1)
