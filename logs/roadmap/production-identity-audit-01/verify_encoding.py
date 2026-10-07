"""Verify source eligibility and raw-label representability; no model predictions."""
import collections
import gzip
import hashlib
import json
from pathlib import Path
from src.learning.actor_selection import construction_products
from src.learning.entity_examples import replay_examples
from src.learning.entity_train import DELAYS, validate_datasets

root = Path(__file__).parent
paths = [Path('logs/roadmap/pro-demonstrations-production-08')/g for g in ('294','870','955','839','991','523')]
validate_datasets(paths, [], missing_fields=True)
results = []
for path in paths:
    static = json.loads((path/'static.json').read_text())['game_data']
    counts = [max(a[k] for a in static[n])+1 for n,k in (('units','unit_id'),('abilities','ability_id'),('upgrades','upgrade_id'))]
    receipt = json.loads((path/'dataset.json').read_text())
    with gzip.open(Path('logs/roadmap/pro-demonstrations-07')/path.name/'examples.jsonl.gz','rt') as stream:
        old_keys = {(r['action_loop'],r['source_sequence']) for r in map(json.loads,stream)}
    total = representable = timed = recovered_representable = 0; exclusions = collections.Counter()
    with gzip.open(path/'examples.jsonl.gz','rt') as stream:
        encoded = replay_examples(path,*counts,DELAYS,construction_products(static),missing_fields=True)
        for row, (_, label, _, reason) in zip(map(json.loads,stream),encoded,strict=True):
            total += 1; representable += label is not None; timed += label is not None and label['delay'] is not None
            recovered_representable += label is not None and (row['action_loop'],row['source_sequence']) not in old_keys
            if reason: exclusions[reason] += 1
    assert total == receipt['issued_command_audit']['matched_issued_commands']
    results.append(dict(game=path.name,commands=total,representable=representable,recovered_representable=recovered_representable,timed=timed,exclusions=dict(exclusions),vocabulary=counts))
report = dict(games=results,source_validation=True,training=False,rl=False,
              verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              audit_sha256=hashlib.sha256((root/'audit.json').read_bytes()).hexdigest())
(root/'encoding-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
