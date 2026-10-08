"""Reconstruct learned choices and observed effects of the failed canary."""
import gzip,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np,torch,mpyq
from src.learning.production_request import ProductionRequest
from src.learning.replay_extract import replay_metadata,load_protocol
from src.learning.entity_execution import project_observation
from src.learning.entity_examples import state_inputs
from src.learning.actor_selection import construction_products
from src.learning.production_component import ProductionComponent
from src.learning.production_execution import command_cost,resource_affordable_choices,canonical,eligible_actors
ROOT=Path('logs/roadmap/professional-choice-native-06')
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 torch.set_num_threads(2);torch.set_num_interop_threads(2)
 contract=read(ROOT/'contract.json');report=read(ROOT/'report.json')
 for p,h in contract['bindings'].items():assert sha(ROOT/'source-snapshot'/p)==h,p
 assert report['result']['status'] in ('completed','truncated') and report['peak_cpu']<=80
 rows=[json.loads(line) for line in gzip.open(ROOT/'Zerg/trace.jsonl.gz','rt')];static=read(ROOT/'Zerg/static.json');data=static['game_data'];catalog={a['ability_id']:a for a in data['abilities']};types={u['unit_id']:u for u in data['units']}
 counts=[max(u[k] for u in data[n])+1 for n,k in (('units','unit_id'),('abilities','ability_id'),('upgrades','upgrade_id'))];products=construction_products(data)
 model,_=ProductionComponent.load('logs/roadmap/professional-choice-fit-04/choice.npz');profile=read(contract['job']['observation_profile']);prices={}
 for a in model.abilities:
  try:prices[a]=command_cost(a,data)
  except ValueError:pass
 first=rows[0]['observation'];initial={u['tag'] for u in first['units'] if u['alliance']==1};new=defaultdict(set);complete=set();predictions=0;accepted=Counter();assist=Counter();errors=0;last_pending=None;pending_loop=None;last_actor=None;near_foundation=False
 for row in rows:
  state=row['observation'];loop=state['game_loop']
  if row.get('phase')=='production_choice':
   for u in state['units']:
    if u['alliance']==1 and u['tag'] not in initial:new[u['unit_type']].add(u['tag'])
    if u['alliance']==1 and u['unit_type'] in (21,27,28) and u.get('build_progress',0)>=1:complete.add(u['tag'])
   choice=row['choice']
   if 'probabilities' in choice:
    x=state_inputs(project_observation(dict(state,recent_commands=[]),profile),*counts,products=products,missing_fields=True);assert not len(x['encoder'][4]) and not np.any(x['encoder'][0][:,30:94])
    scores=model.predict(x);assert all(abs(p-choice['probabilities'][str(a)])<1e-7 for a,p in scores.items());funded=resource_affordable_choices(scores,prices,state['player']['minerals'],state['player']['vespene']);assert set(funded)==set(choice['funded']);predictions+=1
    cmd=choice.get('selected')
    if cmd:
     assert cmd['ability']==max(choice['eligible'],key=scores.get)
     assert cmd['ability'] in funded and cmd['ability'] in prices
     for tag in cmd['units']:
      actors=eligible_actors(state,cmd['ability'],{int(k):v for k,v in choice['available'].items()},catalog,{k:u['name'] for k,u in types.items()},max_train_orders=contract['max_train_orders'])
      assert tag in {u['tag'] for u in actors}
      actor=next(u for u in actors if u['tag']==tag)
      assert cmd.get('queue',False)==(catalog[cmd['ability']].get('friendly_name','').startswith('Train ') and bool(actor.get('orders')))
      assert canonical(cmd['ability'],catalog) in {canonical(a,catalog) for a in choice['available'][str(tag)]}
   if choice.get('accepted_pending'):last_pending=choice['accepted_pending'];pending_loop=loop
   if last_pending and loop>=pending_loop:
    last_actor=next((u for u in state['units'] if u['tag'] in last_pending['units']),None)
    if last_pending.get('target_point'):
     near_foundation|=any(u['alliance']==1 and u['unit_type'] in products.get(str(last_pending['ability']),[]) and np.linalg.norm(np.array(u['position'][:2])-last_pending['target_point'])<1 for u in state['units'])
  else:
   errors+=len(state['action_errors']);cmd=row.get('issued_command');codes=row.get('results',[])
   if cmd:
    assert codes==[1];accepted[catalog[cmd['ability']].get('friendly_name','')]+=1
   for c,code in zip(row.get('assistance',[]),row.get('assistance_results',[]),strict=True):
    assist[catalog[c['ability']].get('friendly_name','')]+=1;errors+=code!=1
    assert c['ability'] not in (524,560,321,328,329)
 worker=len(new[45]);military=sum(len(new[k]) for k in (48,49,53));g=contract['gates']
 parents={r['observation']['game_loop']:r for r in rows if r.get('phase')!='production_choice'};pending={};protected_frames=0;retries=0;concurrent_choices=0
 for row in rows:
  if row.get('phase')!='production_choice':continue
  state=row['observation'];event=row['choice']
  statuses={str(tag):request.status(state) for tag,request in pending.items()}
  assert event['pending_status']==statuses
  for tag,request in list(pending.items()):
   if statuses[str(tag)]=='pending':
    assert tag in parents[state['game_loop']]['primitive_protected'];protected_frames+=1
   else:del pending[tag]
  if event.get('selected'):
   assert not set(event['selected']['units']) & set(pending)
   if pending:concurrent_choices+=1
  if event.get('retry_intent'):retries+=1
  if event.get('accepted_pending'):
   c=event['accepted_pending'];assert c==parents[state['game_loop']]['issued_command']
   from src.learning.gameplay import Command
   cmd=Command(c['ability'],tuple(c['units']),target_unit=c.get('target_unit'),target_point=tuple(c['target_point']) if c.get('target_point') else None,queue=c.get('queue',False))
   pending[c['units'][0]]=ProductionRequest(cmd,state,data)
  if event.get('builder_paths') and event.get('selected'):
   routes=[(r['distance'],r['tag']) for r in event['builder_paths'] if r['distance']>0]
   assert event['selected']['units']==[min(routes)[1]]
   assert event['travel_allowance']==__import__('math').ceil(min(routes)[0]/types[45]['movement_speed']*22.4)
 meta,_=replay_metadata(ROOT/'Zerg/game.SC2Replay');assert meta['BaseBuild']=='Base75689'
 protocol=load_protocol(75689);events=list(protocol.decode_replay_tracker_events(mpyq.MPQArchive(str(ROOT/'Zerg/game.SC2Replay')).read_file('replay.tracker.events')))
 births=Counter(e['m_unitTypeName'].decode() for e in events if e['_event'].endswith('.SUnitBornEvent') and e.get('m_controlPlayerId')==1 and e['_gameloop']>0)
 army_names={u['name'] for u in data['units'] if u.get('race')==1 and u.get('food_required',0)>0 and u['name']!='SCV'}
 military=sum(n for name,n in births.items() if name in army_names);worker=births['SCV']
 tags={(e['m_unitTagIndex'],e['m_unitTagRecycle']) for e in events if e['_event'].endswith('.SUnitInitEvent') and e.get('m_controlPlayerId')==1 and e.get('m_unitTypeName') in (b'Barracks',b'Factory',b'Starport')}
 completions=sum((e['m_unitTagIndex'],e['m_unitTagRecycle']) in tags for e in events if e['_event'].endswith('.SUnitDoneEvent'))
 checks=dict(worker_births=worker>=g['worker_births'],military_births=military>=g['military_births'],completed_production_buildings=completions>=g['completed_production_buildings'],action_errors=errors==0,normal_completion=True)
 paths=[Path(__file__),ROOT/'contract.json',ROOT/'report.json',ROOT/'Zerg/trace.jsonl.gz',ROOT/'Zerg/static.json',ROOT/'Zerg/game.SC2Replay']
 result=dict(status='verified_native_choice_canary_passed' if all(checks.values()) else 'verified_failed_native_choice_canary',checks=checks,gate_pass=all(checks.values()),predictions_recomputed=predictions,accepted_commands=sum(accepted.values()),accepted_by_ability=dict(accepted),assistance_by_ability=dict(assist),replay_births=dict(births),replay_scv_births=worker,replay_military_births=military,replay_completed_production_buildings=completions,pending_protected_frames=protected_frames,concurrent_choices=concurrent_choices,retry_frames=retries,peak_cpu=report['peak_cpu'],last_loop=rows[-1]['observation']['game_loop'],last_player=rows[-1]['observation']['player'],last_pending=last_pending,last_actor=last_actor,delayed_action_errors=errors,training=False,rl=False,bindings={str(p):sha(p) for p in paths},limits=['Normal600second cutoff and Tie; no victory or Hard competence. Military birth gate remains frozen at20.','Replay military counts are Terran non-SCV supply-using units, including support units; MULEs excluded.','Offline model plus native availability; cadence and actor/placement primitives explicitly scripted.'])
 (ROOT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('last_actor','assistance_by_ability','bindings')}))
if __name__=='__main__':main()
