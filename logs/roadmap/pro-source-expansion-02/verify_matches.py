"""Rebuild the command correspondence graph without reconciliation helpers."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

p = Path(__file__).with_name('audit.json')
r = json.loads(p.read_text())
checked = 0
for g in r['games']:
    for f, h in g['bindings'].items():
        assert hashlib.sha256(Path(f).read_bytes()).hexdigest() == h
    events = json.loads(Path(next(f for f in g['bindings'] if Path(f).name == f"raw-commands-{g['game']}.json")).read_text())
    observations = json.loads(Path(next(f for f in g['bindings'] if Path(f).name == f"fall-actions-{g['game']}.json")).read_text())['actions']
    cat = json.loads(Path(next(f for f in g['bindings'] if Path(f).name == 'static.json')).read_text())['game_data']
    abilities = {a['ability_id']: a for a in cat['abilities']}
    names = {(n['link'], n['index']): n['name'] for n in g['verified_candidate_names']}
    selected = {(s['loop'], s['sequence']): s['tags'] for s in g['selections']}
    by_loop = defaultdict(list)
    for i, o in enumerate(observations):
        by_loop[o['loop']].extend(((i, j), a) for j, a in enumerate(o['actions']))
    matches, eligible = {}, {}
    for e in events:
        key = (e['_gameloop'], e['m_sequence'])
        selection = selected.get(key)
        raw = e['m_abil']
        name = names.get((raw['m_abilLink'], raw['m_abilCmdIndex'])) if raw else 'Smart'
        eligible[key] = selection is not None and bool(name) and bool(e['m_cmdFlags'] & 256) and e['m_cmdFlags'] & ~196874 == 0
        pairs = []
        for identity, a in by_loop[e['_gameloop']]:
            native = abilities.get(a['ability'])
            tags = [t & 0xffffffff for t in a['tags']]
            if not tags or len(tags) != len(set(tags)) or native is None:
                continue
            if selection is not None and not set(tags).issubset(selection):
                continue
            if raw is None:
                ability_ok = a['ability'] == 1 and native.get('friendly_name') == 'Smart'
            else:
                ability_ok = native.get('link_index') == raw['m_abilCmdIndex'] and (not name or name.replace(' ', '').lower() == native.get('friendly_name', '').replace(' ', '').lower())
            target = e['m_data']
            target_ok = ('None' in target and a['target_type'] == 0
                         or 'TargetPoint' in target and a['target_type'] == 2 and a['target'] == [int(target['TargetPoint'][axis]/4096) for axis in ('x', 'y')]
                         or 'TargetUnit' in target and a['target_type'] == 1 and a['target'] & 0xffffffff == target['TargetUnit']['m_tag'])
            if ability_ok and target_ok:
                pairs.append(identity)
        matches[key] = pairs
    usage = Counter(identity for values in matches.values() for identity in values)
    expected = {key: values[0] for key, values in matches.items() if eligible[key] and len(values) == 1 and usage[values[0]] == 1}
    actual = {(a['loop'], a['sequence']): tuple(a['converted_position']) for a in g['accepted']}
    assert expected == actual, (g['game'], len(expected), len(actual))
    events_by_key = {(e['_gameloop'], e['m_sequence']): e for e in events}
    for row in g['accepted']:
        key = (row['loop'], row['sequence']); e = events_by_key[key]; i, j = expected[key]
        action = observations[i]['actions'][j]; command = row['command']; target = e['m_data']
        assert command['ability'] == action['ability'] and command['units'] == action['tags']
        assert command['queue'] == bool(e['m_cmdFlags'] & 2) and command['autocast'] is False
        assert command.get('target_unit') == (action['target'] if action['target_type'] == 1 else None)
        assert command.get('target_point') == ([target['TargetPoint'][axis]/4096 for axis in ('x', 'y')] if 'TargetPoint' in target else None)
        checked += 1
out = dict(verified_commands=checked, audit_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
           verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), all_correspondences_reconstructed=True)
Path(__file__).with_name('match-verification.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps(out))
