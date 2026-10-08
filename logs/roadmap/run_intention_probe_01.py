"""Frozen teaching-only intention diagnostic; no controller or RL."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import scipy
from scipy.sparse import hstack, vstack

from src.learning.actor_selection import construction_products
from src.learning.entity_examples import replay_examples
from src.learning.entity_train import DELAYS, validate_datasets
from src.learning.intention_probe import fit_probe, probe_features, probe_logits, probe_metrics

ROOT = Path('logs/roadmap')
OUT = ROOT / 'intention-probe-01'
FOLDS = [('294', '887', '920'), ('870', '839', '851'), ('955', '991', '523')]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def check_time():
    if time.monotonic() >= deadline:
        raise TimeoutError('Combined preparation/fitting bound')


assert not OUT.exists()
assert os.environ['OPENBLAS_NUM_THREADS'] == os.environ['OMP_NUM_THREADS'] == '2'
assert os.environ['CUDA_VISIBLE_DEVICES'] == ''
config_path = ROOT / 'joint-professional-fit-05/configuration.json'
config = read(config_path)
sources = [s for s in config['sources'] if s['role'] == 'teaching']
paths = [Path(s['dataset']) for s in sources]
assert sorted(p.name for p in paths) == sorted(g for fold in FOLDS for g in fold)
parent = ROOT / 'professional-mixed-history-01/verification.json'
assert read(parent)['status'] == 'verified_completed_failure'
bindings = {str(config_path): sha(config_path), str(parent): sha(parent)}
for source in sources:
    bindings.update(source['bindings'])
code_paths = list(config['code_before']) + ['src/learning/intention_probe.py', __file__,
    os.environ['SC2_IMITATION_WATCHDOG'], 'docs/superpowers/plans/2026-10-06-intention-sufficiency-probe.md']
bindings.update({str(p): sha(p) for p in code_paths})
for path, digest in bindings.items():
    assert sha(path) == digest
contract = dict(bindings=bindings, folds=FOLDS, vocabulary=config['vocabulary'],
    regularization=.01, max_iterations=100, wall_seconds=300, spatial=False, missing_fields=True,
    arms=['state', 'history', 'both'], labels='All retained native ability IDs, including command rows lacking complete actor/target labels.',
    history='Original causal human event slots, including unresolved events; unchanged world states.',
    runtime=dict(executable=sys.executable, numpy=np.__version__, scipy=scipy.__version__, threads=2, gpu=False),
    criterion=dict(state_macro_recall=.25, margin_over_history_and_frequency=.10, max_macro_false_positive=.10, folds_required=2),
    scope='Teaching-only whole-game-fold signal diagnostic; no774/reserved inputs or predictions; no native competence, RL, or controller promotion.')
OUT.mkdir()
write(OUT / 'contract.json', contract)
started = time.monotonic()
deadline = started + 300
report = dict(status='running', contract_sha256=sha(OUT / 'contract.json'), preparation={}, folds=[])
try:
    validate_datasets(paths, [], missing_fields=True)
    games = {}
    static = read(paths[0] / 'static.json')['game_data']
    macro_ids = {a['ability_id'] for a in static['abilities'] if any(k in a.get('friendly_name', '').upper() for k in ('BUILD ', 'TRAIN ', 'RESEARCH '))}
    report['macro_ids'] = sorted(macro_ids)
    for path in paths:
        check_time()
        data = read(path / 'static.json')['game_data']
        actual = [max(x[key] for x in data[name])+1 for name,key in [('units','unit_id'),('abilities','ability_id'),('upgrades','upgrade_id')]]
        assert actual == config['vocabulary']
        rows, states, histories, labels = [], [], [], []
        for inputs, label, command, reason in replay_examples(path, *actual, DELAYS, construction_products(data), spatial=False, missing_fields=True):
            check_time()
            state, history = probe_features(inputs, actual[0], actual[1])
            states.append(state)
            histories.append(history)
            labels.append(command.ability)
            rows.append(dict(index=len(rows), ability=command.ability, complete_label=label is not None, exclusion=reason))
        assert len(rows) == read(path / 'dataset.json')['issued_command_audit']['matched_issued_commands']
        games[path.name] = dict(state=vstack(states).tocsr(), history=vstack(histories).tocsr(), labels=np.array(labels), rows=rows)
        report['preparation'][path.name] = dict(rows=len(rows), complete_labels=sum(r['complete_label'] for r in rows))
        print(json.dumps(dict(stage='prepared', game=path.name, rows=len(rows), seconds=time.monotonic()-started)), flush=True)
    assert sum(g['labels'].size for g in games.values()) == 4513
    for number, held in enumerate(FOLDS):
        check_time()
        train = [p.name for p in paths if p.name not in held]
        training_labels = np.concatenate([games[g]['labels'] for g in train])
        held_labels = np.concatenate([games[g]['labels'] for g in held])
        classes, counts = np.unique(training_labels, return_counts=True)
        baseline = dict(classes=classes, columns=np.array([], dtype=int), scales=np.array([]), weights=np.zeros((0,len(classes))), bias=np.log(counts/counts.sum()))
        fold = dict(held=list(held), train=train, arms={}, models={}, predictions={}, baseline={})
        report['folds'].append(fold)
        for arm in contract['arms']:
            check_time()
            def matrix(game):
                return hstack((games[game]['state'],games[game]['history'])).tocsr() if arm == 'both' else games[game][arm]
            training = vstack([matrix(g) for g in train]).tocsr()
            validation = vstack([matrix(g) for g in held]).tocsr()
            model, fitted = fit_probe(training, training_labels, regularization=.01, max_iterations=100, deadline=deadline)
            model_path = OUT / f'fold-{number}-{arm}.npz'
            np.savez(model_path, **model)
            fold['models'][arm] = dict(path=str(model_path), sha256=sha(model_path))
            fold['arms'][arm] = dict(fit=fitted, metrics=probe_metrics(model, validation, held_labels, macro_ids), per_game={g:probe_metrics(model,matrix(g),games[g]['labels'],macro_ids) for g in held})
            fold['predictions'][arm] = model['classes'][probe_logits(model,validation).argmax(axis=1)].tolist()
            fold['baseline'] = probe_metrics(baseline,validation,held_labels,macro_ids)
            print(json.dumps(dict(stage='fit', fold=number, arm=arm, status=fitted['status'], macro_recall=fold['arms'][arm]['metrics']['macro_exact_recall'], seconds=time.monotonic()-started)), flush=True)
            write(OUT / 'report.json', report)
        state, history = (fold['arms'][a] for a in ['state','history'])
        s, h, b = state['metrics'], history['metrics'], fold['baseline']
        fold['positive_state_signal'] = bool(state['fit']['status'] == history['fit']['status'] == 'converged' and s['macro_exact_recall'] >= .25 and s['macro_exact_recall'] >= h['macro_exact_recall'] + .10 and s['macro_exact_recall'] >= b['macro_exact_recall'] + .10 and s['macro_false_positive_rate'] <= .10)
    check_time()
    report['status'] = 'wall_bound_inconclusive' if any(a['fit']['status'] == 'wall_bound' for f in report['folds'] for a in f['arms'].values()) else 'completed'
except TimeoutError:
    report['status'] = 'wall_bound_inconclusive'
report['seconds'] = time.monotonic()-started
report['positive_state_signal'] = report['status'] == 'completed' and sum(f.get('positive_state_signal',False) for f in report['folds']) >= 2
report['bindings_unchanged'] = all(sha(p)==digest for p,digest in bindings.items())
assert report['bindings_unchanged']
write(OUT / 'report.json', report)
print(json.dumps(dict(status=report['status'], seconds=report['seconds'], positive_state_signal=report['positive_state_signal'])), flush=True)
