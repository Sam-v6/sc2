"""Native replay truth, frozen predictions, accounting and useful-start gates."""
from collections import Counter
import gzip,hashlib,json,pickle,shutil
from pathlib import Path
import numpy as np
import mpyq
from src.learning.actor_selection import construction_products
from src.learning.production_goal_policy import current_features,predict_goals
from src.learning.production_outcomes import production_outcomes
from src.learning.replay_extract import load_protocol,replay_metadata
OUT=Path('logs/roadmap/human-goal-native-01/panel')
r=json.loads((OUT/'report.json').read_text());contract=json.loads((OUT/'contract.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert r['status']=='completed' and len(r['results'])==6 and not r['rl']
archive=OUT/'source-snapshot';archive.mkdir(exist_ok=True)
for p,h in r['bindings'].items():
    assert sha(p)==h,p
    if p.startswith('src/'):
        shutil.copyfile(p,archive/Path(p).name)
results=[];bindings={str(OUT/'report.json'):sha(OUT/'report.json'),str(OUT/'contract.json'):sha(OUT/'contract.json')}
for job,result in zip(contract['jobs'],r['results'],strict=True):
    d=Path(job['output']);episode=json.loads((d/'episode.json').read_text());static=json.loads((d/'static.json').read_text());units={u['unit_id']:u for u in static['units']}
    model=pickle.loads(Path(job['model']).read_bytes());profile=json.loads(Path(job['profile']).read_text());products=construction_products(static)
    with gzip.open(d/'trace.jsonl.gz','rt') as f:rows=list(map(json.loads,f))
    ack=Counter();codes=Counter();prediction_rows=0
    for row in rows:
        goals,counts=predict_goals(model,current_features(row['observation'],job['vocabulary'],products,profile))
        assert goals==row['goals'] and np.allclose(counts,row['raw_counts'],rtol=0,atol=1e-12)
        assert len(row['results'])==len(row['execution'])+len(row['assistance'])
        for item,code in zip(row['execution'],row['results'],strict=False):
            assert goals.get(item['goal'],0)>0
            if code==1:ack[item['goal']]+=1
        codes.update(map(str,row['results']));prediction_rows+=1
    assert dict(ack)==episode['acknowledged'] and dict(codes)==episode['results']
    meta,_=replay_metadata(d/'game.SC2Replay');mpq=mpyq.MPQArchive(str(d/'game.SC2Replay'));protocol=load_protocol(int(meta['BaseBuild'][4:]));events=list(protocol.decode_replay_tracker_events(mpq.read_file('replay.tracker.events')))
    header=protocol.decode_replay_header(mpq.header['user_data_header']['content']);end=header['m_elapsedGameLoops']
    outcomes=production_outcomes(events,rows[0]['observation']['player']['player_id'],{n[5:] for n in model['names'] if n.startswith('unit:')},{'OrbitalCommand','PlanetaryFortress'},{n[8:] for n in model['names'] if n.startswith('upgrade:')})
    actual=Counter(n for _,n in outcomes)
    military={'unit:'+u['name'] for u in static['units'] if u.get('race')==1 and 8 not in u.get('attributes',[]) and u['name'] not in ('SCV','MULE')}
    phases={label:dict(workers=sum(n=='unit:SCV' for t,n in outcomes if low*22.4<=t<high*22.4),military=sum(n in military for t,n in outcomes if low*22.4<=t<high*22.4)) for label,low,high in [('120-300',120,300),('300-600',300,600)]}
    joint=False;supply_seconds=idle_seconds=bank_seconds=0
    for i,row in enumerate(rows):
        state=row['observation'];own=[u for u in state['units'] if u['alliance']==1];workers=state['player'].get('food_workers',0)
        army=sum('unit:'+units[u['unit_type']]['name'] in military for u in own)
        barracks=sum(u['unit_type']==21 and u.get('build_progress',0)>=1 for u in own)
        joint |= workers>=30 and army>=8 and barracks>=1
        dt=(min(rows[i+1]['observation']['game_loop'] if i+1<len(rows) else end,end)-state['game_loop'])/22.4
        supply_seconds+=max(dt,0)*(state['player'].get('food_used',0)>=state['player'].get('food_cap',1))
        bank_seconds+=max(dt,0)*(state['player'].get('minerals',0)>=500)
        idle_seconds+=max(dt,0)*sum(u['unit_type'] in (21,27,28) and u.get('build_progress',0)>=1 and not u.get('orders') for u in own)
    first=phases['120-300']['workers']>=3 and phases['120-300']['military']>=5
    second=phases['300-600']['workers']>=3 and phases['300-600']['military']>=5
    full=end/22.4>=599 or result['result']=='Victory'
    useful=bool(joint and first and (second or result['result']=='Victory') and full)
    surplus={n:c-actual[n] for n,c in ack.items() if c>actual[n]}
    item=dict(race=job['race'],build=job['build'],seed=job['seed'],result=result['result'],seconds=end/22.4,prediction_rows=prediction_rows,acknowledged=dict(ack),actual_production=dict(actual),acknowledged_not_produced=surplus,phases=phases,joint_economy_army_gate=bool(joint),useful_start=useful,peak_workers=max(x['player'].get('food_workers',0) for x in episode['snapshots']),peak_army=max(x['army'] for x in episode['snapshots']),supply_blocked_seconds=supply_seconds,idle_production_structure_seconds=idle_seconds,bank_500_seconds=bank_seconds,action_errors=sum(len(x['observation'].get('action_errors',[])) for x in rows))
    results.append(item);print(json.dumps(item),flush=True)
    bindings.update({str(p):sha(p) for p in [d/'episode.json',d/'trace.jsonl.gz',d/'game.SC2Replay']})
bindings.update({str(p):sha(p) for p in archive.glob('*.py')})
receipt=dict(status='verified',rl=False,wins=sum(x['result']=='Victory' for x in results),all_race_useful_start=all(x['useful_start'] for x in results),games=results,peak_cpu=r['peak_cpu'],bindings=bindings)
(OUT/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(status='verified',wins=receipt['wins'],all_race_useful_start=receipt['all_race_useful_start'])),flush=True)
