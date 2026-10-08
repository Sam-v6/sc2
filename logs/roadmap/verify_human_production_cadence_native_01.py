"""Reconstruct forecasts and verify native starts, births and intent attribution."""
import gzip
import hashlib
import json
import pickle
from collections import Counter
from pathlib import Path
import mpyq
import numpy as np
from src.learning.actor_selection import construction_products
from src.learning.production_goal_policy import current_features, predict_goals
from src.learning.production_execution import goal_catalog
from src.learning.production_outcomes import production_outcomes
from src.learning.replay_extract import load_protocol, replay_metadata

OUT = Path('logs/roadmap/human-production-cadence-native-01')
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol = json.loads((OUT/'protocol.json').read_text())
for path, checksum in protocol['bindings'].items():
    assert sha(path) == checksum, path
reports = []
for job in protocol['jobs']:
    d = Path(job['output'])
    episode = json.loads((d/'episode.json').read_text())
    supervision = json.loads((OUT/f'{d.name}.supervision.json').read_text())
    assert supervision['result']['status'] in ('completed', 'truncated')
    model = pickle.loads(Path(job['model']).read_bytes())
    prior = json.loads(Path(job['prior']).read_text())
    profile = json.loads(Path(job['profile']).read_text())
    static = json.loads((d/'static.json').read_text())
    products = construction_products(static)
    catalog = goal_catalog(static, model['names'])
    units = {u['unit_id']: u for u in static['units']}
    with gzip.open(d/'trace.jsonl.gz', 'rt') as stream:
        rows = list(map(json.loads, stream))
    origins, observed, accepted, ack, codes = {}, set(), set(), Counter(), Counter()
    forecast_count = 0
    recent = []
    for row in rows:
        loop = row['observation']['game_loop']
        assert len(row['results']) == len(row['execution'])+len(row['assistance'])
        actors = [t for c in [e['command'] for e in row['execution']]+row['assistance'] for t in c['units']]
        assert len(actors) == len(set(actors)), ('actor overwritten', loop)
        protected = {p['actor'] for p in row['pending'].values()}
        assert not protected.intersection(t for c in row['assistance'] for t in c['units'])
        codes.update(map(str, row['results']))
        if row['phase'] == 'micro':
            assert not row['execution']
            continue
        forecast_count += 1
        predicted, counts = predict_goals(model, current_features(row['observation'], job['vocabulary'], products, profile))
        assert predicted == row['goals'] and np.allclose(counts, row['raw_counts'], atol=1e-12, rtol=0)
        candidates = list(row['priority'])
        for a in candidates:
            probabilities = []
            for b in candidates:
                if a == b:
                    continue
                i, j = prior['names'].index(a), prior['names'].index(b)
                weights = prior['teacher_prior'].get(f'{min(i,j)},{max(i,j)}', [0,0])
                probability = weights[1]/sum(weights) if sum(weights) else .5
                probabilities.append(probability if i<j else 1-probability)
            assert abs(row['priority'][a]-sum(probabilities)/max(1,len(probabilities))) < 1e-12
        for event in row['intent_events']:
            ticket = event['ticket']
            if event['event'] == 'admitted':
                assert ticket not in origins and predicted[event['goal']] > row['effective_queued'].get(event['goal'], 0)
                assert event['admitted'] == loop and event['expires'] == loop+1008
                origins[ticket] = event
            elif event['event'] == 'observed_order':
                assert ticket not in observed
                observed.add(ticket)
                recent.append((loop, origins[ticket]['goal']))
            elif event['event'] == 'unobserved_timeout':
                accepted.discard(ticket)
        recent = [(time, goal) for time, goal in recent if loop-time < 1008]
        assert [list(pair) for pair in recent] == row['recent_fulfilments']
        recent_counts = Counter(goal for _,goal in recent)
        effective = {g:max(row['queued'].get(g,0),recent_counts[g]) for g in set(row['queued'])|set(recent_counts)}
        assert effective == row['effective_queued']
        for allocation in row['allocations']:
            m, g = allocation['before']; cm, cg = allocation['cost']
            assert allocation['affordable'] == (m>=cm and g>=cg)
            expected = [max(0,m-cm), max(0,g-cg)] if allocation['outcome'] == 'reserved' else ([m-cm,g-cg] if allocation['outcome'] == 'submitted' else [m,g])
            assert allocation['after'] == expected
        for item, code in zip(row['execution'], row['results'], strict=False):
            goal, ticket = item['goal'], item['ticket']
            assert item['command']['ability'] == catalog[goal]['ability']
            if job['intent_execution']:
                assert ticket in origins and origins[ticket]['goal'] == goal
                assert loop < origins[ticket]['expires']
                assert ticket not in observed and ticket not in accepted
                if code == 1:
                    accepted.add(ticket)
            else:
                assert predicted.get(goal,0)>0
            if code == 1:
                ack[goal] += 1
    assert dict(ack) == episode['acknowledged'] and dict(codes) == episode['results']
    assert forecast_count == episode['frames']
    metadata, _ = replay_metadata(d/'game.SC2Replay')
    archive = mpyq.MPQArchive(str(d/'game.SC2Replay'))
    decoder = load_protocol(int(metadata['BaseBuild'][4:]))
    events = list(decoder.decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
    player = rows[0]['observation']['player']['player_id']
    outcomes = production_outcomes(events, player, {n[5:] for n in model['names'] if n.startswith('unit:')}, {'OrbitalCommand','PlanetaryFortress'}, {n[8:] for n in model['names'] if n.startswith('upgrade:')})
    barracks = [loop/22.4 for loop,name in outcomes if name=='unit:Barracks']
    military = {'unit:'+u['name'] for u in static['units'] if u.get('race')==1 and 8 not in u.get('attributes',[]) and u['name'] not in ('SCV','MULE')}
    births = sum(name in military for loop,name in outcomes)
    workers = sum(u['alliance']==1 and units[u['unit_type']]['name']=='SCV' for u in rows[-1]['observation']['units'])
    passed = bool(barracks and min(barracks)<=90 and births>=4 and workers>=20)
    depot_orders = [e['loop'] for r in rows if r['phase']=='forecast' for e in r['intent_events'] if e['event']=='observed_order' and e.get('goal')=='unit:SupplyDepot']
    single_depot_forecasts = all(r['goals'].get('unit:SupplyDepot',0)<=1 for r in rows if r['phase']=='forecast')
    cadence_pass = bool(single_depot_forecasts and all(b-a>=1008 for a,b in zip(depot_orders,depot_orders[1:])))
    reports.append(dict(arm=d.name, cadence_gate_passed=cadence_pass, depot_orders=len(depot_orders), result=episode['result'], barracks_first_start_seconds=min(barracks) if barracks else None, military_births=births, living_workers=workers, gate_passed=passed, actual_production=dict(Counter(n for _,n in outcomes)), intents=len(origins), observed_intents=len(observed), forecast_frames=forecast_count, peak_cpu=supervision['peak_cpu']))
    print(json.dumps(reports[-1]), flush=True)
receipt = dict(status='verified_native_diagnostic', games=reports, rl=False, training=False,
    bindings={str(p):sha(p) for p in [Path(__file__), OUT/'protocol.json']+list(OUT.glob('*/episode.json'))+list(OUT.glob('*/trace.jsonl.gz'))+list(OUT.glob('*/game.SC2Replay'))})
(OUT/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
