"""Independent native bridge trace, history, replay and effect checks."""
import gzip,hashlib,json,mpyq
from collections import Counter
from pathlib import Path
from src.learning.teacher_states import remember_command
from src.learning.replay_extract import replay_metadata,load_protocol
ROOT=Path('logs/roadmap/broad-supply-canary-01')
report=json.loads((ROOT/'report.json').read_text());contract=json.loads((ROOT/'contract.json').read_text())
assert report['status']=='completed' and len(report['results'])==2 and report['peak_cpu']<=80
for p,h in report['bindings'].items():assert hashlib.sha256((ROOT/'source-snapshot'/p).read_bytes()).hexdigest()==h,p
results=[]
for job,receipt in zip(contract['jobs'],report['results'],strict=True):
 folder=Path(job['output']);rows=list(map(json.loads,gzip.open(folder/'trace.jsonl.gz','rt')))
 data=json.loads((folder/'static.json').read_text())['game_data'];names={a['ability_id']:a.get('friendly_name','') for a in data['abilities']}
 history=[];control=set();until=0;learned=Counter();assist=Counter();sent=0;assists=0;protected_frames=0;waits=0;delayed=0;mining=0
 for row in rows:
  st=row['observation'];loop=st['game_loop'];owned={u['tag'] for u in st['units'] if u['alliance']==1}
  assert st['recent_commands']==history[-32:],(folder,loop,'accepted-only learned history')
  delayed+=len(st['action_errors'])
  if loop>=until:control=set()
  command=row.get('issued_command');codes=row.get('results',[])
  if command is not None:
   assert len(codes)==1;sent+=1;learned.update(map(str,codes))
   assert row['accepted']==(codes[0]==1)
   if codes[0]==1:
    history.append(remember_command(command,st,loop));history=history[-32:];until=loop+max(1,row['delay']);control=set(command['units']) if job['primitive_assistance'] else set()
  else:assert not codes
  assert set(row['primitive_protected'])==control
  protected_frames+=bool(control)
  if row.get('phase')=='primitives':waits+=1
  commands=row.get('assistance',[]);codes=row.get('assistance_results',[])
  assert len(commands)==len(codes);actors=[t for c in commands for t in c['units']]
  assert len(actors)==len(set(actors)) and set(actors)<=owned and not set(actors)&control
  for c in commands:
   assert c['ability']==319 and job['reactive_supply'] or not names.get(c['ability'],'').startswith(('Build ','Train ','Research '))
   mining+=int(c['ability'] in (295,3666))
  assists+=len(commands);assist.update(map(str,codes))
 assert sent==receipt['commands'] and dict(learned)==receipt['action_results']
 assert assists==receipt['primitive_commands'] and dict(assist)==receipt['primitive_results']
 assert receipt['primitive_assistance']==job['primitive_assistance']
 if job['primitive_assistance']:assert assists>0 and waits>0 and max(map(int,receipt['scheduled_step_counts']))<=8
 else:assert assists==0
 assert not delayed and set(learned)<= {'1'} and set(assist)<= {'1'}
 meta,details=replay_metadata(folder/'game.SC2Replay');assert meta['BaseBuild']=='Base75689'
 protocol=load_protocol(int(meta['BaseBuild'].removeprefix('Base')))
 events=list(protocol.decode_replay_tracker_events(mpyq.MPQArchive(str(folder/'game.SC2Replay')).read_file('replay.tracker.events')))
 births=[e for e in events if e['_event'].endswith('.SUnitBornEvent') and e.get('m_controlPlayerId')==1 and e['m_unitTypeName']==b'SCV' and e['_gameloop']>0]
 stats=[e for e in events if e['_event'].endswith('.SPlayerStatsEvent') and e['m_playerId']==1]
 # No debug resources, salvage, or cancellation is requested. A larger bank plus
 # three paid SCV births independently establishes collected mineral income.
 last=receipt['final_player'];assert len(births)>=3 and last['food_workers']>=15
 depots=[e for e in events if e['_event'].endswith('.SUnitDoneEvent') and e.get('m_unitTagIndex') in {d['m_unitTagIndex'] for d in events if d['_event'].endswith('.SUnitInitEvent') and d.get('m_controlPlayerId')==1 and d.get('m_unitTypeName')==b'SupplyDepot'}]
 submitted_depots=[(r,c,code) for r in rows for c,code in zip(r.get('assistance',[]),r.get('assistance_results',[])) if c['ability']==319]
 assert receipt['reactive_supply']==job['reactive_supply']
 if job['reactive_supply']:
  assert len(submitted_depots)==1 and submitted_depots[0][2]==1
  assert len(depots)==1 and last['food_cap']==23
  assert any(e['event']=='observed' for r in rows for e in r['supply_events'])
  assert not any(e['event']=='unobserved_timeout' for r in rows for e in r['supply_events'])
 else:assert not submitted_depots and not depots and last['food_cap']==15
 result=dict(reactive_supply=job['reactive_supply'],completed_depots=len(depots),scripted_depot_submissions=len(submitted_depots),assisted=job['primitive_assistance'],result=receipt['result'],game_seconds=receipt['game_seconds'],frames=receipt['frames'],learned_submissions=sent,assistance_submissions=assists,mining_commands=mining,wait_trace_rows=waits,protected_trace_rows=protected_frames,action_errors=delayed,scv_births=len(births),final_player=last,replay_stat_samples=len(stats))
 results.append(result);print(json.dumps(result),flush=True)
assert all(r['result']=='Tie' for r in results)
paths=[Path(__file__),ROOT/'contract.json',ROOT/'report.json']
for job in contract['jobs']:paths.extend(Path(job['output'])/n for n in ('game.SC2Replay','episode.json','trace.jsonl.gz','static.json'))
result=dict(status='verified_native_supply_adapter_execution',games=results,peak_cpu=report['peak_cpu'],training=False,rl=False,limits=['Both games are 90-second horizon cutoffs, not victories.','Depot construction is separately attributed scripted supply; frozen old model has no army and macro learning remains failed.','No native combat strength claim; selected worker/army conflict behavior is exercised in regression tests.','Scripted Depot requests are excluded from learned history and learned production counts.'],bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
(ROOT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(ROOT/'source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes())
