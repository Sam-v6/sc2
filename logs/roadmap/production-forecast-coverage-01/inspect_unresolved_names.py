"""Diagnostic name matching only: do not change labels or command eligibility."""
import collections
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


out = []
for game in ('294', '870', '955', '839', '991', '523'):
    root = Path('logs/roadmap/pro-demonstrations-07') / game
    receipt_path = root / 'dataset.json'
    static_path = root / 'static.json'
    receipt = json.loads(receipt_path.read_text())
    reconciliation = next(p for p in receipt['source_bindings'] if 'command-reconciliation' in p)
    assert digest(reconciliation) == receipt['source_bindings'][reconciliation]
    assert digest(static_path) == receipt['corpus_bindings']['static.json']
    reconciled = json.loads(Path(reconciliation).read_text())
    source = next(g for g in reconciled['games'] if str(g['idx']) == game)
    for path, expected in source['bindings'].items():
        assert digest(path) == expected, path
    names = {(n['link'], n['index']): n['name'] for n in source['replay_names']}
    catalog = json.loads(static_path.read_text())['game_data']['abilities']
    reasons, matches, named = collections.Counter(), collections.Counter(), collections.Counter()
    for row in receipt['issued_command_audit']['unresolved_events']:
        event = row['event']
        raw = event['m_abil']
        name = names.get((raw['m_abilLink'], raw['m_abilCmdIndex'])) if raw else 'Smart'
        candidates = [a for a in catalog if name
                      and a.get('friendly_name', '').replace(' ', '').lower() == name.replace(' ', '').lower()
                      and (raw is None or a.get('link_index') == raw['m_abilCmdIndex'])]
        reasons[row['reason']] += 1
        matches['unique' if len(candidates) == 1 else 'no_match' if not candidates else 'ambiguous'] += 1
        named[name or '<unknown>'] += 1
    out.append(dict(game=game, reasons=dict(reasons), exact_name_match=dict(matches),
                    unresolved_replay_names=dict(named),
                    source_sha256={str(p): digest(p) for p in (receipt_path, static_path, reconciliation)},
                    no_command_recovered=True))
report = dict(kind='unresolved_replay_name_diagnostic',
              source_sha256=digest(__file__), games=out, training=False, rl=False,
              caution='Names alone do not establish raw ability identity, selection, flags, targets or observation coverage.')
Path(__file__).with_name('unresolved-names.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(dict(reasons=dict(sum((collections.Counter(g['reasons']) for g in out), collections.Counter())),
                     exact_name_match=dict(sum((collections.Counter(g['exact_name_match']) for g in out), collections.Counter())))))
