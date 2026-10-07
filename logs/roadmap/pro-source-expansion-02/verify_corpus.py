"""Check rebuilt chronology, preserved observations and complete source bindings."""
import collections
import gzip
import hashlib
import json
from pathlib import Path

root = Path(__file__).parent
audit = json.loads((root/'audit.json').read_text())
results = []
for game in audit['games']:
    folder = Path('logs/roadmap/pro-demonstrations-09')/game['game']
    receipt = json.loads((folder/'dataset.json').read_text())
    for f, h in receipt['source_bindings'].items():
        assert hashlib.sha256(Path(f).read_bytes()).hexdigest() == h
    for f, h in receipt['corpus_bindings'].items():
        assert hashlib.sha256((folder/f).read_bytes()).hexdigest() == h
    with gzip.open(folder/'examples.jsonl.gz', 'rt') as stream:
        rows = [json.loads(line) for line in stream]
    old_rows = {}  # New games have no prior imported corpus.
    commands = {(r['loop'],r['sequence']):r['command'] for r in game['accepted']}
    by_key = {(r['action_loop'],r['source_sequence']):r for r in rows}
    assert set(by_key) == set(commands) and len(rows) == len(commands)
    assert list(by_key) == sorted(by_key)
    events = json.loads(Path(next(f for f in game['bindings'] if Path(f).name == f"raw-commands-{game['game']}.json")).read_text())
    keys = [(e['_gameloop'],e['m_sequence']) for e in events]
    mappings = {(r['loop'],r['sequence']):r for r in receipt['source_resource_mappings']}
    history, cache = [], {}
    prior_obs = 0
    for i, event in enumerate(events):
        key = keys[i]
        if key not in commands:
            history.append(dict(game_loop=key[0],unknown=True))
            history = history[-32:]
            continue
        row = by_key[key]; original = commands[key]
        assert row['original_command'] == original
        translated = dict(original)
        if key in mappings:
            m = mappings[key]
            assert original['target_unit'] == m['original_tag']
            translated['target_unit'] = m['source_tag']
        assert row['commands'] == [translated]
        expected_history = []
        for item in history[-32:]:
            remembered = dict(item)
            if not remembered.get('unknown'):
                remembered['target_unit'] = cache.get(remembered.get('target_unit'),remembered.get('target_unit'))
            expected_history.append(remembered)
        assert row['observation']['recent_commands'] == expected_history, (game['game'],key,'history')
        next_key = keys[i+1] if i+1 < len(keys) else None
        assert row['next_action_delay'] == (next_key[0]-key[0] if next_key in commands else None)
        assert row['observation']['game_loop'] == key[0]
        if key in old_rows:
            previous = {k:v for k,v in old_rows[key]['observation'].items() if k!='recent_commands'}
            current = {k:v for k,v in row['observation'].items() if k!='recent_commands'}
            assert previous == current, (game['game'],key,'observation changed')
            assert old_rows[key]['commands'] == row['commands']
            prior_obs += 1
        if key in mappings:
            cache[mappings[key]['original_tag']] = mappings[key]['source_tag']
        remembered = dict(original, game_loop=key[0],verified=True)
        if original['target_unit'] is not None:
            point = event['m_data']['TargetUnit']['m_snapshotPoint']
            remembered['target_position'] = [point[axis]/4096 for axis in ('x','y')]
        history.append(remembered)
        history = history[-32:]
    assert prior_obs == len(old_rows)
    assert receipt['disable_fog'] is False and receipt['alignment'] == 'state_at_issue_loop_before_effect'
    assert receipt['issued_command_audit'] == game['audit']
    results.append(dict(game=game['game'],verified_rows=len(rows),preserved_observations=prior_obs,
                        dataset_sha256=hashlib.sha256((folder/'dataset.json').read_bytes()).hexdigest()))
report = dict(games=results, verified_rows=sum(g['verified_rows'] for g in results),
              preserved_observations=sum(g['preserved_observations'] for g in results),
              exact_histories_and_delay_labels=True,
              verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              audit_sha256=hashlib.sha256((root/'audit.json').read_bytes()).hexdigest())
(root/'corpus-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
