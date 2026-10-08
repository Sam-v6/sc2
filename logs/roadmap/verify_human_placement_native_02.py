"""Independent stock/retrieval/intent reconstruction and replay comparison."""
import gzip,hashlib,json,pickle,math
from collections import Counter
from pathlib import Path
import mpyq
import numpy as np
from src.learning.production_goal_policy import current_features,predict_goals
from src.learning.actor_selection import construction_products
from src.learning.replay_extract import replay_metadata,load_protocol
from src.learning.production_outcomes import production_outcomes
ROOT=Path('logs/roadmap');OUT=ROOT/'human-placement-native-02'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((OUT/'protocol.json').read_text())
for p,h in protocol['bindings'].items():assert sha(p)==h,p
library=ROOT/'human-goal-retrieval-01';audit=json.loads((library/'audit.json').read_text());lr=json.loads((library/'library-rows.json').read_text())
with np.load(library/'library.npz') as a:descriptors=a['descriptor'];targets=a['targets'];scale=a['scale']
source=ROOT/'human-inventory-targets-03';names=json.loads((source/'preparation.json').read_text())['names']
races={g['game']:g['opponent_selected_race'] for g in json.loads((source/'opponent-race-audit.json').read_text())['games']}
reports=[]
placement_reports=[]
for job in protocol['jobs']:
 d=Path(job['output']);episode=json.loads((d/'episode.json').read_text());supervision=json.loads((OUT/f'{d.name}.supervision.json').read_text())
 assert supervision['result']['status'] in ('completed','truncated')
 inventory=bool(job.get('goal_library'));static=json.loads((d/'static.json').read_text());byid={u['unit_id']:u for u in static['units']};upgradeids={u['upgrade_id']:u['name'] for u in static['upgrades']};abilities={a['ability_id']:a for a in static['abilities']}
 aliases={}
 for u in byid.values():
  parent=u
  while parent.get('unit_alias'):parent=byid[parent['unit_alias']]
  aliases[u['name']]=parent['name']
 aliases['HellionTank']='Hellion'
 nativegoals={}
 upgrades={u['name']:u for u in static['upgrades']};unitbyname={u['name']:u for u in static['units']}
 for n in names:
  category,name=n.split(':',1);u=(unitbyname if category=='unit' else upgrades)[name];nativegoals[n]=(u['ability_id'],u.get('unit_id'),abilities[u['ability_id']])
 def canonical(a):return abilities.get(a,{}).get('remaps_to_ability_id') or a
 def stock(state):
  own={u['tag']:u for u in state.get('owned_memory',[])};own.update({u['tag']:u for u in state['units'] if u['alliance']==1})
  counts=Counter('unit:'+aliases.get(byid[u['unit_type']]['name'],byid[u['unit_type']]['name']) for u in own.values())
  counts['unit:CommandCenter']+=counts['unit:OrbitalCommand']+counts['unit:PlanetaryFortress']
  for u in state['upgrades']:counts['upgrade:'+upgradeids[u]]=1
  return +counts,own
 def queues(state):
  own={u['tag']:u for u in state['units'] if u['alliance']==1};foundations=dict(own)
  if inventory:
   foundations={u['tag']:u for u in state.get('owned_memory',[])};foundations.update(own)
  queued=Counter();active=set()
  for u in own.values():
   for o in u.get('orders',[]):
    matches=[n for n,(a,_,_) in nativegoals.items() if canonical(a)==canonical(o['ability_id'])]
    if len(matches)>1:
     parent=byid[u['unit_type']]['name'].removesuffix('Flying');matches=[n for n in matches if nativegoals[n][2].get('friendly_name','').endswith(' '+parent)]
    if len(matches)!=1:continue
    n=matches[0];active.add((u['tag'],n));_,product,descriptor=nativegoals[n]
    if descriptor.get('friendly_name','').startswith('Build '):
     point=o.get('target_world_space_pos');radius=1 if point else 6
     target=next((v for v in state['units'] if v['tag']==o.get('target_unit_tag')),None)
     if target:point=dict(zip(('x','y'),target['position'][:2]));radius=1
     point=[point['x'],point['y']] if point else u['position'][:2]
     if any(v['unit_type']==product and math.dist(v['position'][:2],point)<radius for v in foundations.values()):continue
    queued[n]+=1
  return dict(queued),active
 with gzip.open(d/'trace.jsonl.gz','rt') as f:rows=list(map(json.loads,f))
 metadata,_=replay_metadata(d/'game.SC2Replay');player=rows[0]['observation']['player']['player_id'];race=next(p['SelectedRace'] for p in metadata['Players'] if p['PlayerID']!=player)
 ids=np.array([i for i,r in enumerate(lr) if race=='Rand' or races[r['game']]==race]);held=None;expires=-1
 model=pickle.loads(Path(job['model']).read_bytes());profile=json.loads(Path(job['profile']).read_text());products=construction_products(static)
 intents={};pending={};expired={};sequence=0;recent=[];codes=Counter();ack=Counter();forecasts=0;blocked=0.;lastloop=None;demand={};supported=[];failures=Counter();reasons=Counter();rejections=[]
 for row in rows:
  state=row['observation'];loop=state['game_loop'];ownstock,known=stock(state)
  if lastloop is not None:
   p=previous['player'];foodblocked=p.get('food_used',0)>=p.get('food_cap',0) and p.get('food_cap',0)<200
   fooddemand=any(unitbyname.get(n.removeprefix('unit:'),{}).get('food_required',0)>0 for n in demand)
   if foodblocked and fooddemand:blocked+=(loop-lastloop)/22.4
  lastloop=loop;previous=state
  assert len(row['results'])==len(row['execution'])+len(row['assistance'])
  actors=[tag for c in [e['command'] for e in row['execution']]+row['assistance'] for tag in c['units']]
  assert len(actors)==len(set(actors)),('actor overwritten',d.name,loop)
  codes.update(map(str,row['results']))
  assert not set(row['scouting']['protected']).intersection(tag for e in row['execution'] for tag in e['command']['units'])
  if row['phase']=='micro':continue
  forecasts+=1
  for check in row['placement_checks']:
   if check['resolved']:continue
   failures[check['goal']]+=1
   assert not any(e['goal']==check['goal'] and check['actor'] in e['command']['units'] for e in row['execution'])
   for diagnostic in check['diagnostics']:
    if diagnostic.get('source')=='owned_base_probe':
     bases={u['tag']:u for u in state['units'] if u['alliance']==1 and u['unit_type'] in (18,132,130) and u.get('build_progress',1)==1 and not u.get('is_flying')}
     assert diagnostic['base'] in bases
     for cmd in diagnostic['commands']:
      assert cmd['ability']==check['command']['ability'] and cmd['units']==check['command']['units']
      assert cmd not in [e['command'] for e in row['execution']]
     for trace_probe in diagnostic['diagnostics']:
      if trace_probe.get('source')=='production_clearance':assert sum(trace_probe.get('placement_results',{}).values())==trace_probe.get('checked',0)
     continue
    if diagnostic.get('source')!='production_clearance':continue
    codes_placement=diagnostic.get('placement_results',{})
    assert sum(codes_placement.values())==diagnostic.get('checked',0)
    if diagnostic['rejected']=='native_placement':assert diagnostic['legal_sites']==0
    if diagnostic['rejected']=='unreachable':assert diagnostic['legal_sites']>0 and diagnostic['pathing_checked']>0
    reasons[(check['goal'],diagnostic['rejected'])]+=1
   rejections.append(dict(loop=loop,**check))
  queued,active=queues(state);assert queued==row['queued'],(d.name,loop,queued,row['queued'])
  if inventory:
   if held is None or loop>=expires:
    descriptor=[loop/22.4,ownstock['unit:SCV'],ownstock['unit:CommandCenter']]
    dd=np.sum((descriptors[ids]/scale-np.array(descriptor)/scale)**2,axis=1);held=int(ids[np.argmin(dd)]);expires=loop+1008
    distance=float(np.sqrt(dd.min()));is_supported=distance<=audit['thresholds'].get(race,audit['thresholds']['unknown'])
   target={n:int(v) for n,v in zip(names,targets[held],strict=True) if v>0}
   source_goal=row['source_goal'];assert all(source_goal[k]==lr[held][k] for k in ['game','row','loop'])
   assert source_goal['expires']==expires and source_goal['future_loop']==lr[held]['loop']+1008 and source_goal['distance']==distance and source_goal['supported']==is_supported
   assert source_goal['inventory_sha256']==sha(source/'teaching-inventory.npy')
   assert row['inventory_target']==target and np.array_equal(row['raw_counts'],targets[held])
   assert row['inventory_stock']==dict(ownstock)
   demand={n:v-ownstock[n] for n,v in target.items() if v>ownstock[n]} if is_supported else {}
   supported.append(is_supported)
  else:
   demand,counts=predict_goals(model,current_features(state,job['vocabulary'],products,profile));assert np.allclose(row['raw_counts'],counts,atol=1e-12,rtol=0)
  assert demand==row['goals']
  # Reconstruct lifecycle before planning/submission, including omitted events.
  expected=[];tags={u['tag'] for u in state['units'] if u['alliance']==1}
  for ticket,item in list(intents.items()):
   pend=pending.get(ticket)
   if pend and pend['acknowledged'] and (pend['actor'],item['goal']) in active:status='observed_order';recent.append((loop,item['goal']));del intents[ticket]
   elif loop>=item['expires']:status='expired';expired[item['goal']]=loop;del intents[ticket]
   elif pend and pend['actor'] not in tags:status='actor_lost'
   elif pend and pend['acknowledged'] and loop-pend['loop']>=128:status='unobserved_timeout'
   else:continue
   pending.pop(ticket,None);expected.append(dict(event=status,ticket=ticket,loop=loop,goal=item['goal']))
  if inventory:
   for ticket,item in list(intents.items()):
    if ticket not in pending and demand.get(item['goal'],0)<=queued.get(item['goal'],0):
     del intents[ticket];expected.append(dict(event='retired',ticket=ticket,goal=item['goal'],loop=loop))
   recent=[]
  recent=[(t,g) for t,g in recent if loop-t<1008];fulfilled=Counter(g for _,g in recent)
  effective={g:max(queued.get(g,0),fulfilled[g]) for g in set(queued)|set(fulfilled)}
  assert row['effective_queued']==effective and row['recent_fulfilments']==[list(x) for x in recent]
  for goal,count in demand.items():
   if count<=effective.get(goal,0) or any(i['goal']==goal for i in intents.values()):continue
   if goal in expired:
    if loop<=expired[goal]:continue
    del expired[goal]
   sequence+=1;item=dict(goal=goal,admitted=loop,expires=loop+1008,origin_count=count);intents[sequence]=item;expected.append(dict(event='admitted',ticket=sequence,**item))
  for e in row['execution']:
   goal,ticket=e['goal'],e['ticket'];command=e['command'];assert ticket in intents and intents[ticket]['goal']==goal
   assert command['ability']==nativegoals[goal][0] and ticket not in pending and loop<intents[ticket]['expires']
   if inventory:assert demand.get(goal,0)>queued.get(goal,0)
   actor=command['units'][0];assert actor in tags and not any(p['actor']==actor for p in pending.values())
   pending[ticket]=dict(goal=goal,actor=actor,loop=loop,acknowledged=False);expected.append(dict(event='submitted',ticket=ticket,**pending[ticket]))
  for e,code in zip(row['execution'],row['results'],strict=False):
   ticket=e['ticket'];expected.append(dict(event='acknowledged' if code==1 else 'rejected',ticket=ticket))
   if code==1:pending[ticket]['acknowledged']=True;ack[e['goal']]+=1
   else:del pending[ticket]
  assert row['intent_events']==expected,(d.name,loop,'events',row['intent_events'],expected)
  assert {int(k):v for k,v in row['intents'].items()}==intents and {int(k):v for k,v in row['pending'].items()}==pending
 assert dict(failures)=={g.removeprefix('placement:'):v for g,v in episode['blocks'].items() if g.startswith('placement:')}
 placement_reports.append(dict(arm=d.name,failures=dict(failures),reasons=[dict(goal=g,reason=r,count=c) for (g,r),c in reasons.items()],rejections=rejections))
 assert forecasts==episode['frames'] and dict(ack)==episode['acknowledged'] and dict(codes)==episode['results']
 archive=mpyq.MPQArchive(str(d/'game.SC2Replay'));decoder=load_protocol(int(metadata['BaseBuild'][4:]));events=list(decoder.decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
 outcomes=production_outcomes(events,player,{n[5:] for n in names if n.startswith('unit:')},{'OrbitalCommand','PlanetaryFortress'},{n[8:] for n in names if n.startswith('upgrade:')})
 military={'unit:'+u['name'] for u in static['units'] if u.get('race')==1 and 8 not in u.get('attributes',[]) and u['name'] not in ('SCV','MULE')}
 finalstock,finalown=stock(rows[-1]['observation'])
 tracked={}
 for event in events:
  if event['_gameloop']>=rows[-1]['observation']['game_loop']:break
  if 'm_unitTagIndex' not in event:continue
  tag=(event['m_unitTagIndex'],event['m_unitTagRecycle']);kind=event['_event'].rsplit('.',1)[-1]
  if kind in ('SUnitInitEvent','SUnitBornEvent'):tracked[tag]=dict(name=event['m_unitTypeName'].decode(),owner=event['m_upkeepPlayerId'],complete=kind=='SUnitBornEvent')
  elif kind=='SUnitDoneEvent':tracked[tag]['complete']=True
  elif kind=='SUnitTypeChangeEvent':tracked[tag]['name']=event['m_unitTypeName'].decode()
  elif kind=='SUnitOwnerChangeEvent':tracked[tag]['owner']=event['m_upkeepPlayerId']
  elif kind=='SUnitDiedEvent':tracked.pop(tag)
 living_workers=sum(u['owner']==player and u['name']=='SCV' for u in tracked.values())
 capacity=sum(u['owner']==player and u['complete'] and aliases.get(u['name'],u['name']) in ('Barracks','Factory','Starport') for u in tracked.values())
 assert living_workers==finalstock['unit:SCV'],(d.name,'living workers',living_workers,finalstock['unit:SCV'])
 assert capacity==sum(aliases[byid[u['unit_type']]['name']] in ('Barracks','Factory','Starport') and u.get('build_progress',1)==1 for u in finalown.values()),(d.name,'completed capacity')
 reports.append(dict(arm=d.name,result=episode['result'],forecasts=forecasts,supported_fraction=float(np.mean(supported)) if supported else None,completed_production_capacity=capacity,military_births=sum(n in military for _,n in outcomes),living_workers=finalstock['unit:SCV'],final_minerals=rows[-1]['observation']['player']['minerals'],supply_blocked_seconds=blocked,actual_production=dict(Counter(n for _,n in outcomes)),peak_cpu=supervision['peak_cpu']))
 print(json.dumps(reports[-1]),flush=True)
receipt=dict(status='verified_live_placement_diagnostic',games=reports,placement=placement_reports,training=False,rl=False,bindings={str(p):sha(p) for p in [Path(__file__),OUT/'protocol.json']+list(OUT.glob('*/episode.json'))+list(OUT.glob('*/trace.jsonl.gz'))+list(OUT.glob('*/game.SC2Replay'))})
(OUT/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(status=receipt['status'],failures=placement_reports[0]['failures'],reasons=placement_reports[0]['reasons'])))
