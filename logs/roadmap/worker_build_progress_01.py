"""Locate visible foundations at pending SCV build targets, using current state only."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from src.learning.teacher_states import teacher_states

root = Path('logs/roadmap')
source = root / 'worker-harvest-diagnosis-01/report.json'
out = root / 'worker-build-progress-01'
out.mkdir(exist_ok=False)
audit = json.loads(source.read_text())
files = [Path(__file__), source, *[Path(d) / n for d in audit['datasets'] for n in ('static.json', 'examples.jsonl.gz')], root / 'consistent-fullgame-live-zerg-02/trace.jsonl.gz']
def hashes():
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before = hashes()

def describe(state, worker, mapping):
    order = worker['orders'][0]
    point = order.get('target_world_space_pos')
    target = next((u for u in state['units'] if u['tag'] == order.get('target_unit_tag')), None)
    if point:
        point = [point['x'], point['y']]
    elif target:
        point = target['position'][:2]
    if point is None:
        return {'stage': 'target_not_observed'}
    types = mapping.get(order['ability_id'], [])
    buildings = [u for u in state['units'] if u['alliance'] == 1 and u['unit_type'] in types and np.linalg.norm(np.asarray(u['position'][:2]) - point) <= 1.0]
    building = min(buildings, key=lambda u: np.linalg.norm(np.asarray(u['position'][:2]) - point)) if buildings else None
    progress = building.get('build_progress', 1) if building else None
    return {'stage': 'no_visible_foundation' if not building else 'complete' if progress >= 1 else 'unfinished_foundation', 'progress': progress, 'building_tag': building['tag'] if building else None, 'worker_distance_to_target': float(np.linalg.norm(np.asarray(worker['position'][:2]) - point)), 'target': point}

records = []
for d in audit['datasets']:
    directory = Path(d)
    static = json.loads((directory / 'static.json').read_text())
    mapping = {}
    for u in static['game_data']['units']:
        mapping.setdefault(u.get('ability_id', -1), []).append(u['unit_id'])
    wanted = {r['loop']: r for r in audit['records'] if r['dataset'] == d}
    # Retain multiple mineral commands at the same loop rather than assuming one.
    for row, state in teacher_states(directory):
        if row['action_loop'] not in wanted:
            continue
        known = {u['tag']: u for u in state['units']}
        for command_record in [r for r in audit['records'] if r['dataset'] == d and r['loop'] == row['action_loop']]:
            for b in command_record['builders']:
                record = {'dataset': d, 'loop': row['action_loop'], 'worker': b['tag'], 'ability': b['order']['ability_id'], 'teacher_selected': b['teacher_selected'], 'model_selected': b['model_selected'], 'queue': command_record['teacher']['queue']}
                record.update(describe(state, known[b['tag']], mapping))
                records.append(record)
with gzip.open(files[-1], 'rt') as stream:
    frame = next(r for r in map(json.loads, stream) if r['observation']['game_loop'] == 1448)
worker = next(u for u in frame['observation']['units'] if u['tag'] == 4350803969)
live = describe(frame['observation'], worker, mapping)
summary = {}
for label, rows in [('all', records), ('teacher_selected_queued', [r for r in records if r['teacher_selected'] and r['queue']]), ('teacher_selected_nonqueued', [r for r in records if r['teacher_selected'] and not r['queue']]), ('model_false_positive', [r for r in records if r['model_selected'] and not r['teacher_selected']])]:
    summary[label] = {stage: {'count': sum(r['stage'] == stage for r in rows), 'progress': [r['progress'] for r in rows if r['stage'] == stage and r.get('progress') is not None]} for stage in sorted({r['stage'] for r in records})}
assert len(records) == audit['aggregate']['builder_candidates']
assert hashes() == before
report = {'status': 'completed', 'scope': 'Current fog-safe visible building at first build-order target; not future completion, mining success or proof intentional human cancel. No model changes or games.', 'files_before': before, 'files_after': hashes(), 'summary': summary, 'records': records, 'live': live}
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'summary': summary, 'live': live}, indent=2))
