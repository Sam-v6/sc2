"""Frozen queue head on teacher harvest groups and the native interrupted worker."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from src.learning.actor_selection import group_features
from src.learning.global_imitation import global_features
from src.learning.imitation import FactorPolicy
from src.learning.teacher_states import own_actors, teacher_states

root = Path('logs/roadmap')
out = root / 'worker-queue-construction-01'
out.mkdir(exist_ok=False)
source = root / 'worker-harvest-diagnosis-01/report.json'
progress_path = root / 'worker-build-progress-01/report.json'
harvest = json.loads(source.read_text())
progress = json.loads(progress_path.read_text())
paths = [root / 'consistent-fullgame-02/macro/policy.npz', root / 'worker-construction-arguments-01/arguments/arguments.npz']
trace = root / 'consistent-fullgame-live-zerg-02/trace.jsonl.gz'
files = [Path(__file__), source, progress_path, *paths, trace, *sorted(Path('src/learning').glob('*.py')), *[Path(d) / n for d in harvest['datasets'] for n in ('static.json', 'examples.jsonl.gz')]]
def hashes():
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before = hashes()
macro, arguments = [FactorPolicy.load(p) for p in paths]
def queue(state, command):
    x, origin = global_features(state, macro.unit_types, macro.sizes['ability'], canonical=True, summarize=True, semantics=macro.evidence.get('action_history_encoder') == 'roles_targets_age', upgrade_count=macro.evidence.get('upgrade_count', 0))
    by_tag = {u['tag']: u for u in own_actors(state)}
    group = [by_tag[t] for t in command['units']]
    features = group_features(state, group, macro.unit_types, macro.sizes['ability'], origin, macro.command_context(x, command['ability']), arguments.evidence.get('worker_construction_products'))
    logits = arguments.predict(features[None, :])['queue'][0]
    return {'predicted_queue': bool(logits.argmax()), 'queue_margin': float(logits[1] - logits[0]), 'correct': bool(logits.argmax()) == command['queue']}
records = []
for d in harvest['datasets']:
    for row, state in teacher_states(Path(d)):
        for record in [r for r in harvest['records'] if r['dataset'] == d and r['loop'] == row['action_loop']]:
            stages = [r['stage'] for r in progress['records'] if r['dataset'] == d and r['loop'] == row['action_loop'] and r['worker'] in record['teacher']['units']]
            records.append(dict(dataset=d, loop=row['action_loop'], teacher=record['teacher'], selected_builder_stages=stages, **queue(state, record['teacher'])))
with gzip.open(trace, 'rt') as stream:
    frame = next(r for r in map(json.loads, stream) if r['observation']['game_loop'] == 1448)
command = next(c for c in frame['issued_model_commands'] if c['ability'] == 1)
live = queue(dict(frame['observation'], recent_commands=frame['model_recent_commands']), command)
assert not command['queue']  # Record the frozen counterfactual; no prescribed result.
summary = {}
for label, rows in [('all', records), ('selected_builder_no_foundation', [r for r in records if 'no_visible_foundation' in r['selected_builder_stages']]), ('selected_builder_foundation', [r for r in records if 'unfinished_foundation' in r['selected_builder_stages']])]:
    summary[label] = {'commands': len(rows), 'queue_hits': sum(r['correct'] for r in rows), 'human_queued': sum(r['teacher']['queue'] for r in rows), 'model_queued': sum(r['predicted_queue'] for r in rows)}
assert len(records) == len(harvest['records']) and hashes() == before
report = {'status': 'completed', 'scope': 'Teacher ability/group oracle on human mineral-command examples; actual issued group/ability on native failure. No training, native mask, target decoding or claims of autonomous competence.', 'files_before': before, 'files_after': hashes(), 'records': records, 'summary': summary, 'live': live}
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'summary': summary, 'live': live}, indent=2))
