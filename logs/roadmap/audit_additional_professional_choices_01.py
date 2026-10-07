"""Measure additional professional labels and actual observation limitations."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path('logs/roadmap/human-command-cohort-03')
OUT = Path('logs/roadmap/additional-professional-choice-audit-01.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not OUT.exists()
    verification = json.loads((ROOT / 'verification.json').read_text())
    assert verification['status'] == 'verified_additional_professional_command_cohort'
    for path, digest in verification['bindings'].items():
        assert sha(Path(path)) == digest
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    games = []
    totals = Counter()
    bindings = dict(verification['bindings'])
    for game in manifest['games']:
        folder = ROOT / game['game'] / 'corpus'
        data = json.loads((folder / 'static.json').read_text())['game_data']
        names = {ability['ability_id']: ability.get('friendly_name', '') for ability in data['abilities']}
        counts = Counter()
        missing = Counter()
        seen = set()
        current_fields = Counter()
        for line in gzip.open(folder / 'examples.jsonl.gz', 'rt'):
            row = json.loads(line)
            assert len(row['commands']) == 1
            name = names[row['commands'][0]['ability']]
            if not (name.startswith(('Build ', 'Train ', 'Research ')) or name in ('Morph OrbitalCommand', 'Morph PlanetaryFortress')):
                continue
            key = row['action_loop'], row['source_sequence']
            assert key not in seen
            seen.add(key)
            state = row['observation']
            assert state['game_loop'] == row['action_loop']
            counts[name] += 1
            for section, fields in state['unknown_fields'].items():
                missing.update(section + '.' + field for field in fields)
            current_fields.update(key for key in ('minerals', 'vespene', 'food_cap', 'food_army', 'food_workers') if key in state['player'])
        totals.update(counts)
        games.append({'game': game['game'], 'human_result_code': game['human_result_code'],
                      'production_events': len(seen), 'building_events': sum(count for name, count in counts.items() if name.startswith('Build ')),
                      'counts': dict(counts), 'unknown_fields': dict(missing), 'available_player_fields': dict(current_fields)})
        for path in (folder / 'dataset.json', folder / 'static.json', folder / 'examples.jsonl.gz'):
            bindings[str(path)] = sha(path)
    for path in (Path(__file__), ROOT / 'verification.json'):
        bindings[str(path)] = sha(path)
    result = {'status': 'audited_additional_professional_choices', 'games': games,
              'production_events': sum(totals.values()),
              'building_events': sum(count for name, count in totals.items() if name.startswith('Build ')),
              'counts': dict(totals), 'bindings': bindings, 'training': False, 'rl': False,
              'limits': ['Previously used in broad imitation; additional to the current six-game choice teaching set only.',
                         'Same partial observation contract; not fully observed human games or fresh evaluation.',
                         'Four human wins and one loss, no additional TvT teaching game.',
                         'No model, native game, download or engine installation in this audit.']}
    OUT.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ('bindings', 'games')}))


if __name__ == '__main__':
    main()
