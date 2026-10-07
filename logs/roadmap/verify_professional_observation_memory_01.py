"""Reconstruct every pointer without the preparation selector."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from src.learning.actor_selection import construction_products
from src.learning.entity_examples import state_inputs

ROOT = Path('logs/roadmap')
OUT = ROOT / 'professional-observation-memory-01'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with gzip.open(path, 'rt') as stream:
        return [json.loads(line) for line in stream]


def main():
    report = read(OUT / 'report.json')
    for path, digest in report['bindings'].items():
        assert sha(Path(path)) == digest, path
    assert report['lags_loops'] == [45, 112, 336]
    corpus = read(ROOT / 'professional-production-choice-01/report.json')
    catalog = ROOT / 'dense-timing-cohort-01/51574/static.json'
    data = read(catalog)['game_data']
    counts = [max(row[key] for row in data[name]) + 1 for name, key in
              (('units', 'unit_id'), ('abilities', 'ability_id'), ('upgrades', 'upgrade_id'))]
    products = construction_products(data)
    total = 0
    missing = [0, 0, 0]
    ages = [[], [], []]
    encoded = 0
    games = []
    for game in corpus['games']:
        source = rows(ROOT / 'human-command-cohort-02' / game['game'] / 'corpus/examples.jsonl.gz')
        targets = rows(ROOT / 'professional-production-choice-01' / game['game'] / 'examples.jsonl.gz')
        pointers = read(OUT / (game['game'] + '.json'))
        assert len(pointers) == len(targets)
        used = set()
        for target, entry in zip(targets, pointers):
            assert entry['source_key'] == target['label']['source_key']
            loop = target['observation']['game_loop']
            assert entry['current_loop'] == loop
            for index, lag in enumerate(report['lags_loops']):
                eligible = [(row['observation']['game_loop'], i) for i, row in enumerate(source)
                            if row['observation']['game_loop'] <= loop - lag]
                slot = entry['slots'][index]
                if not eligible:
                    assert slot is None
                    missing[index] += 1
                    continue
                observed_loop, row_index = max(eligible)
                assert slot == {'source_row': row_index, 'loop': observed_loop, 'age_loops': loop - observed_loop}
                assert observed_loop < loop
                ages[index].append(loop - observed_loop)
                used.add(row_index)
                total += 1
        for row_index in used:
            # Only observations enter encoding; source commands and delay are excluded.
            state = dict(source[row_index]['observation'], recent_commands=[])
            inputs = state_inputs(state, *counts, products=products, missing_fields=True)
            assert not np.any(inputs['encoder'][0][:, 30:94])
            assert len(inputs['encoder'][4]) == 0
            encoded += 1
        games.append({'game': game['game'], 'role': game['role'], 'targets': len(targets),
                      'unique_past_observations': len(used)})
    assert total == report['available_past_frames']
    assert missing == report['missing_slots']
    bindings = dict(report['bindings'])
    for path in (OUT / 'report.json', Path(__file__), catalog,
                 Path('src/learning/entity_examples.py'), Path('src/learning/actor_selection.py')):
        bindings[str(path)] = sha(path)
    result = {'status': 'verified_causal_observation_pointers_and_empty_command_features',
              'available_past_frames': total, 'unique_past_observations_encoded': encoded,
              'missing_slots': missing, 'games': games,
              'age_loops': [{'min': min(values), 'median': float(np.median(values)), 'max': max(values)}
                            for values in ages],
              'limits': 'Source observations occur at command events, not dense fixed cadence; actual ages must be encoded. This verifies data selection only, not learned memory behavior or native inference.',
              'bindings': bindings}
    (OUT / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'bindings'}))


if __name__ == '__main__':
    main()
