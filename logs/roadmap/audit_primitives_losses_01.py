"""Describe saved planning-frame evidence; do not infer native availability."""
import gzip
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path

root = Path('logs/roadmap/human-goal-native-02/panel')
reports, bindings = [], {}
for path in sorted(root.glob('*/trace.jsonl.gz')):
    folder = path.parent
    static = json.loads((folder/'static.json').read_text())
    episode = json.loads((folder/'episode.json').read_text())
    names = {u['unit_id']: u['name'] for u in static['units']}
    frames, orders, army_targets = [], Counter(), Counter()
    for line in gzip.open(path, 'rt'):
        row = json.loads(line)
        state = row['observation']
        player = state['player']
        workers = [u for u in state['units'] if u['alliance'] == 1 and names[u['unit_type']] == 'SCV']
        idle = sum(not u.get('orders') for u in workers)
        gather = sum(any(o['ability_id'] in (295, 296, 3666, 3667) for o in u.get('orders', []))
                     for u in workers)
        for unit in workers:
            orders.update(o['ability_id'] for o in unit.get('orders', []))
        for command in row['assistance']:
            if command['ability'] == 23:
                army_targets.update(['point' if command.get('target_point') else
                                     'unit' if command.get('target_unit') else 'none'])
        frames.append(dict(seconds=state['game_loop']/22.4, workers=len(workers),
                           idle=idle, gather=gather, minerals=player['minerals'],
                           gas=player['vespene'], spare=player['food_cap']-player['food_used']))
    late = [f for f in frames if f['seconds'] >= 120]
    worker_frames = max(1, sum(f['workers'] for f in late))
    metrics = dict(game=folder.name, result=episode['result'], sampled_frames=len(frames),
                   late_frames=len(late), max_workers=max(f['workers'] for f in frames),
                   max_idle_workers=max(f['idle'] for f in frames),
                   late_idle_worker_frame_fraction=sum(f['idle'] for f in late)/worker_frames,
                   late_mining_order_worker_frame_fraction=sum(f['gather'] for f in late)/worker_frames,
                   late_supply_blocked_frame_fraction=sum(f['spare'] == 0 for f in late)/max(1, len(late)),
                   max_spare_supply=max(f['spare'] for f in frames),
                   max_minerals=max(f['minerals'] for f in frames), max_gas=max(f['gas'] for f in frames),
                   late_median_minerals=statistics.median(f['minerals'] for f in late),
                   late_median_gas=statistics.median(f['gas'] for f in late),
                   attack_target_counts=dict(army_targets), worker_order_ids=dict(orders),
                   blocks=episode['blocks'])
    reports.append(metrics)
    for source in (path, folder/'static.json', folder/'episode.json'):
        bindings[str(source)] = hashlib.sha256(source.read_bytes()).hexdigest()
notes = ['Planning-frame samples approximately every 2.14 seconds; fractions are sampled worker-frames, not exact durations.',
         'Mining-order presence does not prove income or successful travel; idle workers may be between tasks.',
         'Attack command counts cover assistance only; no claim about all replay actions.']
out = Path('logs/roadmap/primitives-reference-01/loss-audit.json')
out.write_text(json.dumps(dict(reports=reports, bindings=bindings, notes=notes), indent=2)+'\n')
for report in reports:
    print(json.dumps({k: v for k, v in report.items() if k not in ('blocks', 'worker_order_ids')}))
