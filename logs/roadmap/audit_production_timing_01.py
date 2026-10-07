"""Descriptive human outcome timing and native scheduling audit; no fit or RL."""
from collections import Counter
import gzip,hashlib,json
from pathlib import Path
import numpy as np
from src.learning.production_execution import goal_catalog
ROOT=Path('logs/roadmap');OUT=ROOT/'production-timing-audit-01';DATA=ROOT/'human-production-goals-01'
prep=json.loads((DATA/'preparation.json').read_text());reaudit=json.loads((DATA/'label-reaudit.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha('src/learning/production_outcomes.py')==reaudit['current_labeler_sha256']
for p,h in prep['bindings'].items():
    if p!='src/learning/production_outcomes.py':assert sha(p)==h,p
bindings={str(p):sha(p) for p in [Path(__file__),DATA/'preparation.json',DATA/'label-reaudit.json']}
def summary(values):
    a=np.asarray(values,dtype=float)
    return dict(rows=len(a),p10=float(np.quantile(a,.1)),median=float(np.median(a)),p90=float(np.quantile(a,.9)),within5=float((a<=5).mean())) if len(a) else dict(rows=0)
roles={}
human={}
for role in ('teaching','development'):
    rows=json.loads((DATA/f'{role}-rows.json').read_text());times={};building_counts=[]
    for g in {r['game'] for r in rows}:
        path=DATA/f'{g}-outcomes.json';events=json.loads(path.read_text());bindings[str(path)]=sha(path)
        times[g]=events
        building_counts.append(dict(game=g,first600_depots=sum(n=='unit:SupplyDepot' and t<13440 for t,n in events),first600_workers=sum(n=='unit:SCV' and t<13440 for t,n in events)))
    delays={};matched=0
    truth=np.load(DATA/f'{role}-counts.npy');names=prep['names'];name_to_index={n:i for i,n in enumerate(names)}
    for i,row in enumerate(rows):
        counts=Counter();first={}
        for t,n in times[row['game']]:
            if row['loop']<=t<row['loop']+1008:
                counts[n]+=1;first.setdefault(n,(t-row['loop'])/22.4)
        assert np.array_equal(truth[i],[counts[n] for n in names])
        for n,time in first.items():delays.setdefault(n,[]).append(time);matched+=1
    human[role]=dict(verified_windows=len(rows),positive_family_windows=matched,delay_seconds={n:summary(v) for n,v in delays.items()},first600=sorted(building_counts,key=lambda x:x['game']))
native=[]
for panel in ('human-goal-native-01','human-goal-native-02'):
    verification=json.loads((ROOT/panel/'panel/verification.json').read_text())
    for g in verification['games']:
        directory=next(d for d in (ROOT/panel/'panel').iterdir() if d.is_dir() and d.name.endswith(g['race']+'-'+g['build']))
        with gzip.open(directory/'trace.jsonl.gz','rt') as f:rows=list(map(json.loads,f))
        static=json.loads((directory/'static.json').read_text());catalog=goal_catalog(static,prep['names'])
        units={u['unit_id']:u for u in static['units']}
        missed=[];depot_dispatch=[];max_spare=0
        for row in rows:
            state=row['observation'];player=state['player'];pending=row['pending']
            busy={p['actor'] for p in pending.values()}
            idle=[u for u in state['units'] if u['alliance']==1 and u['unit_type'] in (18,132)
                  and u.get('build_progress',0)>=1 and not u.get('orders') and u['tag'] not in busy]
            unfilled=row['goals'].get('unit:SCV',0)-row['queued'].get('unit:SCV',0)-sum(p['goal']=='unit:SCV' for p in pending.values())
            issued=[e['goal'] for e in row['execution']]
            spare=player.get('food_cap',0)-player.get('food_used',0);max_spare=max(max_spare,spare)
            if idle and unfilled>0 and player.get('minerals',0)>=50 and spare>=1 and 'unit:SCV' not in issued:
                spending=sum(catalog[e]['minerals'] for e in issued)
                missed.append(dict(loop=state['game_loop'],minerals=player['minerals'],idle_producers=len(idle),unfilled=int(unfilled),other_mineral_spending=spending,issued=issued,worker_cost_remaining_budget=player['minerals']-spending>=50))
            for e in row['execution']:
                if e['goal']=='unit:SupplyDepot':depot_dispatch.append(state['game_loop']/22.4)
        intervals=np.diff(depot_dispatch).tolist()
        item=dict(panel=panel,race=g['race'],build=g['build'],result=g['result'],actual_depots=g['actual_production'].get('unit:SupplyDepot',0),actual_workers=g['actual_production'].get('unit:SCV',0),maximum_spare_supply=max_spare,depot_dispatch_intervals=summary(intervals),affordable_idle_worker_goal_without_dispatch=len(missed),still_affordable_after_other_dispatches=sum(m['worker_cost_remaining_budget'] for m in missed),worker_opportunity_rows=missed,resource_reservations={k:v for k,v in json.loads((directory/'episode.json').read_text())['blocks'].items() if k.startswith('resource_reservation:')})
        native.append(item)
        bindings.update({str(p):sha(p) for p in [directory/'trace.jsonl.gz',directory/'episode.json',directory/'static.json']})
for p,h in bindings.items():assert sha(p)==h,p
report=dict(status='verified_descriptive_audit',rl=False,human=human,native=native,limitations=['Overlapping event-weighted human windows, not independent samples','Idle-worker opportunity is a physical proxy; native availability queries were not saved','No causal isolation of scheduling from model and placement changes','Outcome times are not human issue-command times'],bindings=bindings)
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(human={r:{n:human[r]['delay_seconds'][n] for n in ('unit:SupplyDepot','unit:CommandCenter','unit:Marine','unit:SCV')} for r in human},native=[{k:v for k,v in x.items() if k not in ('worker_opportunity_rows','resource_reservations')} for x in native])),flush=True)
