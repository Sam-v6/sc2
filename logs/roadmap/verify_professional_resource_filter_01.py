"""Recompute probabilities and compare independent price filtering with helper."""
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

import numpy as np
import torch

from src.learning.actor_selection import construction_products
from src.learning.entity_examples import state_inputs
from src.learning.production_component import ProductionComponent
from src.learning.production_execution import command_cost, resource_affordable_choices

ROOT = Path('logs/roadmap')
OUT = ROOT / 'professional-resource-filter-01'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    torch.set_num_threads(2)
    torch.set_num_interop_threads(2)
    report = read(OUT / 'report.json')
    contract = read(OUT / 'contract.json')
    for path, digest in report['bindings'].items():
        source = Path(path)
        if sha(source) != digest:
            source = OUT / 'source-snapshot' / path
        assert sha(source) == digest, path
    historical = OUT / 'source-snapshot/src/learning/production_execution.py'
    spec = importlib.util.spec_from_file_location('historical_execution', historical)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = read(ROOT / 'dense-timing-cohort-01/51574/static.json')['game_data']
    counts = [max(row[key] for row in data[name]) + 1 for name, key in
              (('units', 'unit_id'), ('abilities', 'ability_id'), ('upgrades', 'upgrade_id'))]
    products = construction_products(data)
    names = {row['ability_id']: row.get('friendly_name', '') for row in data['abilities']}
    model_path = ROOT / 'professional-choice-fit-04/choice.npz'
    model, _ = ProductionComponent.load(model_path)
    prices = {}
    for ability in model.abilities:
        try:
            prices[ability] = module.command_cost(ability, data)
            assert prices[ability] == command_cost(ability, data)
        except ValueError:
            assert ability in contract['unknown_prices']
    assert sorted(set(model.abilities) - set(prices)) == sorted(contract['unknown_prices'])
    records = {(row['game'], str(row['key'])): row for row in report['records']}
    saved = {(row['game'], str(row['key'])): row for row in read(ROOT / 'professional-choice-fit-04/evaluation.json')['predictions']}
    totals = Counter()
    for game in ('887', '920', '851'):
        result = Counter()
        for line in gzip.open(ROOT / 'professional-production-choice-02' / game / 'examples.jsonl.gz', 'rt'):
            row = json.loads(line)
            key = game, str(row['label']['source_key'])
            state = row['observation']
            inputs = state_inputs(dict(state, recent_commands=[]), *counts, products=products, missing_fields=True)
            assert not len(inputs['encoder'][4]) and not np.any(inputs['encoder'][0][:, 30:94])
            probabilities = model.predict(inputs)
            assert all(abs(probability - saved[key]['probabilities'][str(ability)]) < 1e-7 for ability, probability in probabilities.items())
            budget = state['player']['minerals'], state['player']['vespene']
            blocked = sorted(ability for ability, cost in prices.items() if any(value > limit for value, limit in zip(cost, budget)))
            independent = {ability: value for ability, value in probabilities.items() if ability not in blocked}
            helper = resource_affordable_choices(probabilities, prices, *budget)
            assert independent == helper
            selected = max(independent, key=independent.get) if independent else None
            record = records[key]
            gold = row['label']['ability']
            assert record['filtered'] == selected and record['blocked'] == blocked and record['gold'] == gold
            assert record['original'] == max(probabilities, key=probabilities.get)
            building = names[gold].startswith('Build ')
            false_building = not building and selected is not None and names[selected].startswith('Build ')
            result.update({'events': 1, 'correct': int(selected == gold), 'nonworker': int(gold != 524),
                           'nonworker_correct': int(gold != 524 and selected == gold), 'building_events': int(building),
                           'building_correct': int(building and selected == gold), 'false_buildings': int(false_building),
                           'changed': int(selected != record['original'])})
        assert dict(result) == {key: value for key, value in next(row for row in report['games'] if row['game'] == game).items() if key != 'game'}
        totals.update(result)
    assert dict(totals) == report['totals']
    metrics = {'accuracy': totals['correct'] / totals['events'], 'nonworker_recall': totals['nonworker_correct'] / totals['nonworker'],
               'building_recall': totals['building_correct'] / totals['building_events'],
               'false_building_rate': totals['false_buildings'] / (totals['events'] - totals['building_events'])}
    assert metrics == report['metrics']
    control = read(ROOT / 'professional-choice-fit-04/evaluation.json')['metrics']
    passed = (metrics['accuracy'] > control['majority_accuracy'] and metrics['nonworker_recall'] >= control['old_nonworker_recall'] + .10
              and metrics['building_recall'] >= contract['gates']['building_recall']
              and metrics['false_building_rate'] <= contract['gates']['false_building_rate_max']
              and all(row['building_correct'] >= 1 for row in report['games']))
    assert passed == (report['status'] == 'resource_only_inference_gates_passed')
    assert not torch.cuda.is_initialized()
    paths = [Path(__file__), OUT / 'contract.json', OUT / 'report.json', model_path, historical,
             Path('src/learning/production_execution.py'), Path('src/learning/production_component.py'), Path('src/learning/entity_examples.py')]
    result = {'status': 'verified_resource_only_inference_gates_passed' if passed else 'verified_resource_only_inference_gates_failed',
              'predictions_recomputed': 289, 'metrics': metrics, 'totals': dict(totals),
              'optimizer': False, 'native': False, 'rl': False, 'bindings': {str(path): sha(path) for path in paths}}
    (OUT / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'bindings'}))


if __name__ == '__main__':
    main()
