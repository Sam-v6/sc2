"""Same teacher and ordinary episode; change only candidate tank micro."""
import teacher_worker
from learner import ground_micro


def episode(job):
    assert job['experiment']=='ground-tank-matched' and job['role'] in ['control','candidate']
    assert job['micro_version']==('original' if job['role']=='control' else 'ground-tank-v1')
    previous=teacher_worker.ObservedLearner
    if job['role']=='candidate':
        class Corrected(previous):micro=ground_micro
        teacher_worker.ObservedLearner=Corrected
    try:return teacher_worker.episode(job)
    finally:teacher_worker.ObservedLearner=previous


def entrypoint_probe():return {'file':__file__,'games_launched':0}
