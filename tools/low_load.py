"""Run this project's Linux jobs on eight logical CPUs at lower priority."""
import os
import sys


if len(sys.argv) < 2 or sys.argv[1] == '--help':
    print('Usage: python tools/low_load.py COMMAND [ARG ...]')
    print('Eight logical CPUs, nice +10, CPU-only CUDA/software OpenGL. Use --workers 4 for simulations.')
    raise SystemExit(0 if len(sys.argv) > 1 else 2)

os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[-8:])
os.nice(10)
for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[name] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
os.execvp(sys.argv[1], sys.argv[1:])
