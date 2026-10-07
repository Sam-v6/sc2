"""Frozen resource-only inference audit; no fitting or native legality claims."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

from src.learning.production_execution import command_cost

ROOT = Path('logs/roadmap')
OUT = ROOT / 'professional-resource-filter-01'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    OUT.mkdir(exist_ok=False)
    catalog = ROOT / 'dense-timing-cohort-01/51574/static.json'
    evaluation_path = ROOT / 'professional-choice-fit-04/evaluation.json'
    verification_path = ROOT / 'professional-choice-fit-04/verification.json'
    verified = read(verification_path)
    assert verified['status'] == 'verified_failed_professional_choice_fit'
    for path, digest in verified['bindings'].items():
        assert sha(Path(path)) == digest
    data = read(catalog)['game_data']
    names = {row['ability_id']: row.get('friendly_name', '') for row in data['abilities']}
    types = {row['unit_id']: row for row in data['units']}
    evaluation = read(evaluation_path)
    prices = {}
    unknown = []
    for ability in map(int, evaluation['predictions'][0]['probabilities']):
        try:
            prices[ability] = command_cost(ability, data)
        except ValueError:
            unknown.append(ability)
    bindings = {str(path): sha(path) for path in (Path(__file__), catalog, evaluation_path, verification_path, Path('src/learning/production_execution.py'))}
    contract = {
        'rule': 'Remove only abilities whose single-product known native mineral/gas cost exceeds current recorded resources. Keep unknown prices; do not guess research tier.',
        'gates': {'building_recall': .40, 'false_building_rate_max': 37 / 235, 'nonworker_margin': .10, 'correct_building_per_game': 1},
        'unknown_prices': unknown, 'optimizer': False, 'native': False, 'rl': False,
        'scope': 'Conditional immediate issuance only. Resource-saving plans must be separate; this is not full native legality.',
        'bindings': bindings,
    }
    write(OUT / 'contract.json', contract)
    stored = {(row['game'], str(row['key'])): row for row in evaluation['predictions']}
    games = []
    records = []
    false_building_context = Counter()
    for game in ('887', '920', '851'):
        path = ROOT / 'professional-production-choice-02' / game / 'examples.jsonl.gz'
        bindings[str(path)] = sha(path)
        counts = Counter()
        for line in gzip.open(path, 'rt'):
            source = json.loads(line)
            state = source['observation']
            key = source['label']['source_key']
            original = stored[game, str(key)]
            gold = original['gold']
            assert gold == source['label']['ability']
            player = state['player']
            blocked = {ability for ability, (minerals, gas) in prices.items()
                       if player['minerals'] < minerals or player['vespene'] < gas}
            eligible = {int(ability): probability for ability, probability in original['probabilities'].items()
                        if int(ability) not in blocked}
            assert gold not in blocked  # Label audit only; never used in selection.
            selected = max(eligible, key=eligible.get) if eligible else None
            building = names[gold].startswith('Build ')
            predicted_building = selected is not None and names[selected].startswith('Build ')
            counts['events'] += 1
            counts['correct'] += selected == gold
            counts['nonworker'] += gold != 524
            counts['nonworker_correct'] += gold != 524 and selected == gold
            counts['building_events'] += building
            counts['building_correct'] += building and selected == gold
            counts['false_buildings'] += not building and predicted_building
            counts['changed'] += selected != original['predicted']
            if not building and names[original['predicted']].startswith('Build '):
                ability = original['predicted']
                product = next(unit for unit in data['units'] if unit.get('ability_id') == ability)
                ready = {alias for unit in state['units'] if unit['alliance'] == 1 and unit.get('build_progress', 0) >= 1
                         for alias in [unit['unit_type'], *types[unit['unit_type']].get('tech_alias', [])]}
                prerequisite = product.get('tech_requirement')
                false_building_context['original_false_buildings'] += 1
                false_building_context['resource_shortfall'] += ability in blocked
                false_building_context['no_observed_ready_scv'] += 45 not in ready
                false_building_context['no_observed_ready_prerequisite'] += bool(prerequisite and prerequisite not in ready)
            records.append({'game': game, 'key': key, 'gold': gold, 'original': original['predicted'], 'filtered': selected, 'blocked': sorted(blocked)})
        games.append(dict(game=game, **counts))
    totals = Counter()
    for game in games:
        totals.update({key: value for key, value in game.items() if key != 'game'})
    metrics = {'accuracy': totals['correct'] / totals['events'], 'nonworker_recall': totals['nonworker_correct'] / totals['nonworker'],
               'building_recall': totals['building_correct'] / totals['building_events'],
               'false_building_rate': totals['false_buildings'] / (totals['events'] - totals['building_events'])}
    passed = (metrics['accuracy'] > evaluation['metrics']['majority_accuracy']
              and metrics['nonworker_recall'] >= evaluation['metrics']['old_nonworker_recall'] + .10
              and metrics['building_recall'] >= .40 and metrics['false_building_rate'] <= 37 / 235
              and all(game['building_correct'] >= 1 for game in games))
    write(OUT / 'report.json', {'status': 'resource_only_inference_gates_passed' if passed else 'resource_only_inference_gates_failed',
                              'metrics': metrics, 'totals': dict(totals), 'games': games, 'records': records,
                              'original_false_building_context': dict(false_building_context), 'bindings': bindings,
                              'limits': 'Observed ready prerequisites are diagnostic only; absent/stale observations do not prove native illegality. No actor, queue, attachment, supply or placement availability checks. Original fit04 remains failed; no promotion.'})
    print(json.dumps({'passed': passed, 'metrics': metrics, 'context': dict(false_building_context)}))


if __name__ == '__main__':
    main()
