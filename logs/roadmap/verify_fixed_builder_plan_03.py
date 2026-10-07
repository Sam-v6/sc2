"""Independent provenance checks; does not invoke either plan compiler."""
import hashlib
import json
from pathlib import Path
from src.learning.tournament_record import decode_record
root = Path('logs/roadmap')
out = root/'fixed-human-production-plan-03'
plan = json.loads((out/'plan.json').read_text())
parent = json.loads((root/'fixed-human-production-plan-02/plan.json').read_text())
accepted = {(r['loop'], r['sequence']): r for r in json.loads(
    (root/'human-refinery-snapshot-reimport-01/reconciliation.json').read_text())['games'][0]['accepted']}
events = {(e['_gameloop'], e['m_sequence']): e for e in json.loads(
    (root/'pro-preconverted-probe-01/raw-commands-870.json').read_text())}
record = decode_record((root/'pro-preconverted-probe-01/fall-record-870.bin').read_bytes())
f = record['units']['fields']
own = {(int(record['steps']['game_loop'][step]), int(f['id'][i])): int(f['unitType'][i])
       for i, step in enumerate(record['units']['step']) if f['alliance'][i] == 1}
n = record['neutral']['fields']
neutral = {int(tag): list(map(float, n['pos'][i][:2])) for i, tag in enumerate(n['id'])}
moves = [t for t in plan['tickets'] if t['name'] == 'Move builder']
assert len(moves) == 9 and len(plan['tickets']) == 212
assert [t for t in plan['tickets'] if t['name'] != 'Move builder'] == parent['tickets']
keys = [(t['loop'], t['sequence']) for t in plan['tickets']]
assert keys == sorted(set(keys))
for t in moves:
    key = t['loop'], t['sequence']
    source = accepted[key]['command']; event = events[key]; command = t['command']
    assert command['ability'] == source['ability'] and command['ability'] in (1, 16)
    assert command['units'] == source['units'] and len(command['units']) == 1
    assert own[(t['loop'], command['units'][0])] == 45
    assert command['queue'] == bool(event['m_cmdFlags'] & 2)
    p = event['m_data']['TargetPoint']
    assert command['target_point'] == [p['x']/4096, p['y']/4096]
    next_build = next(b for b in parent['tickets'] if (b['loop'], b['sequence']) > key
                      and b['name'].startswith('Build ') and b['command']['units'] == command['units'])
    assert t['source_build'] == dict(loop=next_build['loop'], sequence=next_build['sequence'])
    target = next_build['command'].get('target_point') or neutral[next_build['command']['target_unit']]
    assert sum((a-b)**2 for a,b in zip(target, command['target_point'])) <= 36
    assert t['evidence_is_label_only'] is True
for p, sha in plan['bindings'].items():
    path = Path(p)
    if path.suffix == '.py':
        path = out/'source-snapshot'/path.name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == sha, path
result = dict(status='verified_source_builder_movements', macro_instructions=203,
              builder_movements=9, total=212, original_queue_flags=True,
              future_build_used_only_for_label_provenance=True, training=False, rl=False,
              plan_sha256=hashlib.sha256((out/'plan.json').read_bytes()).hexdigest())
(out/'verification.json').write_text(json.dumps(result, indent=2)+'\n')
(out/'source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(result))
