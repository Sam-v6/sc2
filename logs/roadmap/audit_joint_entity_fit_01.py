import hashlib
import json
from collections import Counter
from pathlib import Path
import time

import numpy as np

from src.learning.entity_examples import decode_command
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect, digest, validate_datasets

root = Path.cwd()
output = root/'logs/roadmap/joint-entity-fit-01'
report = json.loads((output/'report.json').read_text())
contract = json.loads((root/'logs/roadmap/joint-entity-fit-contract-01.json').read_text())
configuration = json.loads((output/'configuration.json').read_text())
assert report['status'] == 'completed' and report['bindings_unchanged']
assert report['optimizer_updates'] == contract['expected_optimizer_updates'] == 44400
assert len(report['history']) == 200
assert all(r['commands'] == 3542 for r in report['history'])
assert digest(output/'policy.npz') == report['checkpoint_sha256']
policy, metadata = JointEntityPolicy.load(output/'policy.npz')
assert metadata['configuration'] == configuration and metadata['updates'] == 44400 and metadata['status'] == 'completed'
paths = {role:[Path(s['dataset']) for s in configuration['sources'] if s['role']==role] for role in ('teaching','diagnostic')}
assert validate_datasets(paths['teaching'], paths['diagnostic']) == configuration['sources']
assert all(digest(Path(path))==value for path,value in configuration['code_before'].items())
start = time.monotonic()
results = {}
for role, directories in paths.items():
    examples,_ = collect(directories, configuration['vocabulary'])
    counts = Counter()
    breakdown = {}
    group_stats = Counter()
    actor_loss = 0.
    actor_rows = 0
    geometry = Counter()
    for inputs,label,command,exclusion in examples:
        prediction = policy.predict(inputs)
        actual = decode_command(prediction, inputs) if prediction else None
        ability = command.ability
        local = breakdown.setdefault(str(ability), Counter())
        local['commands'] += 1
        if actual is None:
            continue
        same_mode = (actual.autocast==command.autocast and (actual.target_unit is None)==(command.target_unit is None) and (actual.target_point is None)==(command.target_point is None))
        target_ok = actual.target_unit == command.target_unit
        if command.target_point is not None:
            target_ok = actual.target_point is not None and np.linalg.norm(np.asarray(actual.target_point)-command.target_point) <= configuration['point_tolerance']
        matches = dict(ability=actual.ability==ability, actors=set(actual.units)==set(command.units), mode=same_mode, queue=actual.queue==command.queue, target=target_ok)
        complete = all(matches.values()) and exclusion is None
        counts.update({k:int(v) for k,v in matches.items()})
        counts['complete'] += int(complete)
        local['ability'] += int(matches['ability']); local['actors'] += int(matches['actors']); local['complete'] += int(complete)
        gold, selected = set(command.units), set(actual.units)
        group_stats['true_positive'] += len(gold & selected)
        group_stats['false_positive'] += len(selected-gold)
        group_stats['false_negative'] += len(gold-selected)
        group_stats['over_selected'] += int(len(selected)>len(gold))
        group_stats['under_selected'] += int(len(selected)<len(gold))
        group_stats['same_size_wrong_members'] += int(len(selected)==len(gold) and gold!=selected)
        if label is not None:
            scores = policy.scores(inputs, ability=ability, actors=label['actors'])
            eligible = np.flatnonzero(inputs['actor_mask'])
            targets = np.isin(eligible,label['actors']).astype(float)
            actor_loss += float(np.logaddexp(0,scores['actor'][eligible]).sum()-(targets*scores['actor'][eligible]).sum())
            actor_rows += len(eligible)
            if command.target_point is not None:
                geometry['point_commands'] += 1
                geometry['oracle_correct_cell'] += int(scores['point'].argmax()==label['point'])
                # Continuous head fidelity measured using the human cell, explicitly oracle.
                candidate = inputs['world_points'][label['point']]+scores['offset']*inputs['point_radii'][label['point']]
                geometry['oracle_cell_offset_within_one_tile'] += int(np.linalg.norm(candidate-command.target_point)<=1)
    official = report['teaching' if role=='teaching' else 'validation']['predicted']
    assert all(counts[k]==official[k] for k in ('ability','actors','mode','queue','target','complete'))
    results[role] = dict(commands=len(examples), ordinary=dict(counts), actor_membership=dict(group_stats), mean_actor_bce_per_eligible_entity=actor_loss/max(actor_rows,1), spatial_oracle=dict(geometry), per_ability={k:dict(v) for k,v in breakdown.items()})
    print(json.dumps({k:v for k,v in results[role].items() if k!='per_ability'}),flush=True)
assert validate_datasets(paths['teaching'],paths['diagnostic'])==configuration['sources']
assert digest(output/'policy.npz')==report['checkpoint_sha256']
assert all(digest(Path(path))==value for path,value in configuration['code_before'].items())
teaching=results['teaching']; n=teaching['commands']; gate=contract['teaching_gate']
accepted = all(teaching['ordinary'][k]/n >= gate[k+'_fraction'] for k in ('ability','actors','complete'))
receipt = dict(status='verified', fit_terminal=True, full_update_budget_satisfied=True, loaded_checkpoint_sha256=report['checkpoint_sha256'], bindings_unchanged=True,
               results=results, frozen_teaching_gate_passed=accepted, native_play_allowed=accepted,
               seconds=time.monotonic()-start, reserved_replays_opened=False, rl_run=False,
               scope='Reloaded checkpoint, independently recomputed ordinary complete-command counts; oracle spatial diagnostics are explicitly named. Reused validation; no native competence claim.')
(root/'logs/roadmap/joint-entity-fit-verification-01.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(teaching_gate_passed=accepted,seconds=receipt['seconds'])),flush=True)
