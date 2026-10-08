"""Measure native SCV queue stalls without treating sampled source data as continuous."""
import gzip, hashlib, json
from pathlib import Path
import mpyq
from src.learning.replay_extract import replay_metadata, load_protocol
from src.learning.tournament_record import decode_record
root = Path('logs/roadmap')
out = root / 'worker-queue-stalls-22'
out.mkdir(exist_ok=False)
trace = root / 'fixed-human-plan-native-22/episode/trace.jsonl.gz'
source = root / 'pro-preconverted-probe-01/2cda222081e80d9a1c188698ce9bcda6.SC2Replay'
native = root / 'fixed-human-plan-native-22/episode/game.SC2Replay'
record = root / 'pro-preconverted-probe-01/fall-record-870.bin'
rows = [json.loads(l) for l in gzip.open(trace, 'rt')]
cutoff = 9224
births = {}
for name, path in [('source', source), ('native', native)]:
    meta, _ = replay_metadata(path)
    protocol = load_protocol(int(meta['BaseBuild'].removeprefix('Base')))
    events = protocol.decode_replay_tracker_events(mpyq.MPQArchive(str(path)).read_file('replay.tracker.events'))
    births[name] = [e['_gameloop'] for e in events if e['_gameloop'] < cutoff and e['_event'].endswith('.SUnitBornEvent') and e.get('m_upkeepPlayerId') == 1 and e.get('m_unitTypeName') == b'SCV']
stalls = {}
for row, following in zip(rows, rows[1:]):
    if following['loop'] >= cutoff:
        break
    obs = row['observation']
    if obs['player']['food_used'] < obs['player']['food_cap']:
        continue
    for unit in obs['units']:
        orders = unit.get('orders', [])
        if unit['alliance'] != 1 or unit['unit_type'] not in (18,132) or not orders or orders[0]['ability_id'] != 524 or orders[0].get('progress', 0) != 0:
            continue
        subsequent = next((u for u in following['observation']['units'] if u['tag'] == unit['tag']), {})
        queue = subsequent.get('orders', [])
        if not queue or queue[0]['ability_id'] != 524 or queue[0].get('progress', 0) != 0:
            continue
        groups = stalls.setdefault(str(unit['tag']), [])
        if groups and groups[-1]['end'] == row['loop']:
            groups[-1]['end'] = following['loop']
        else:
            groups.append({'start': row['loop'], 'end': following['loop']})
r = decode_record(record.read_bytes())
f = r['units']['fields']
comparisons = []
for loop in (824,1152,2000,6000,6720,8800,9216):
    si = max(i for i,l in enumerate(r['steps']['game_loop']) if l <= loop)
    row = next(row for row in rows if row['loop'] == loop)
    source_units = []
    for i in (r['units']['step'] == si).nonzero()[0]:
        if f['alliance'][i] == 1 and f['unitType'][i] in (18,132):
            orders = [{'ability': int(f[f'order{k}'][i]['ability']), 'progress': float(f[f'order{k}'][i]['progress'])} for k in range(4) if f[f'order{k}'][i]['ability']]
            source_units.append({'tag': int(f['id'][i]), 'orders': orders})
    comparisons.append({'loop': loop, 'source_loop': int(r['steps']['game_loop'][si]), 'source': {k:int(r['steps'][k][si]) for k in ('cap','army','workers','minerals')}, 'source_producers':source_units, 'native':row['observation']['player'], 'native_producers':[{'tag':u['tag'],'orders':u.get('orders',[])} for u in row['observation']['units'] if u['alliance']==1 and u['unit_type'] in (18,132)]})
assert len(births['source']) == 55 and len(births['native']) == 45
assert any(g['end']-g['start'] >= 200 for groups in stalls.values() for g in groups)
result = {'status':'verified_native_worker_supply_stalls','cutoff_exclusive':cutoff,'births':births,'stalls':stalls,'producer_seconds_stalled':sum(g['end']-g['start'] for groups in stalls.values() for g in groups)/22.4,'comparisons':comparisons,'training':False,'rl':False,'limitations':['Stall intervals require consecutive native samples showing the same zero-progress head and full supply. They omit unsampled transitions and do not measure every possible cause of production delay.','Source snapshots are irregular and truncate queues at four; food_used is unavailable. Source cap/army/workers cannot prove exact source supply use.','Different combat attrition and delayed construction both change supply; descriptive evidence does not assign all ten missing births to one cause.'], 'bindings':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),trace,source,native,record)}}
(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'auditor.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({k:v for k,v in result.items() if k not in ('bindings','comparisons','births')}))
for c in comparisons:
    print(c['loop'],'source',c['source'],'native',{k:c['native'][k] for k in ('food_cap','food_army','food_workers','minerals')})
