"""Compare matched runs at shared cutoffs; verify assistance actually builds Depots."""
import gzip,hashlib,json,math
from pathlib import Path
import mpyq
from src.learning.replay_extract import load_protocol,replay_metadata
root=Path('logs/roadmap');out=root/'fixed-human-plan-native-25';contract=json.loads((out/'contract.json').read_text());report=json.loads((out/'report.json').read_text());ep=json.loads((out/'episode/episode.json').read_text());rows=[json.loads(line) for line in gzip.open(out/'episode/trace.jsonl.gz','rt')]
assert report['status']=='completed' and len(rows)==ep['frames'] and report['peak_cpu']<=80 and contract['jobs'][0]['reactive_supply'] is True
for path,digest in contract['bindings'].items():
 p=Path(path);rel=p.relative_to(Path.cwd()) if p.is_absolute() else p
 actual=out/'source-snapshot'/rel if p.suffix in ('.py','.json') else p
 assert hashlib.sha256(actual.read_bytes()).hexdigest()==digest,actual
replay=out/'episode/game.SC2Replay';meta,_=replay_metadata(replay);protocol=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));init=protocol.decode_replay_initdata(mpyq.MPQArchive(str(replay)).read_file('replay.initData'));assert init['m_syncLobbyState']['m_userInitialData'][0]['m_randomSeed']==817501
assistance=[]
for h in ep['history']:
 if h.get('event')!='reactive_supply_assistance':continue
 assert h['result']==1 and h['command']['ability']==319
 row=next(row for row in rows if row['loop']==h['loop']);worker=h['command']['units'][0]
 assert worker not in row['worker_bindings'].values()
 assert sum(worker in c['units'] for c in row['commands'])==1
 point=h['command']['target_point'];before={u['tag'] for u in row['observation']['units']};found=[(row['loop'],u['tag']) for row in rows if row['loop']>h['loop'] for u in row['observation']['units'] if u['alliance']==1 and u['unit_type'] in (19,47) and u['tag'] not in before and math.dist(u['position'][:2],point)<1]
 complete=[row['loop'] for row in rows if row['loop']>h['loop'] and any(u['alliance']==1 and u['unit_type'] in (19,47) and u['tag'] not in before and math.dist(u['position'][:2],point)<1 and u['build_progress']==1 for u in row['observation']['units'])]
 assert len({tag for _,tag in found}) == 1
 assistance.append(dict(loop=h['loop'],worker=worker,point=point,first_foundation=min(found)[0] if found else None,first_completed=min(complete) if complete else None))
assert assistance and all(h['first_foundation'] is not None for h in assistance)
comparisons=[]
for n in (22,25):
 folder=root/f'fixed-human-plan-native-{n}';tr=[json.loads(line) for line in gzip.open(folder/'episode/trace.jsonl.gz','rt')];meta,_=replay_metadata(folder/'episode/game.SC2Replay');protocol=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));events=list(protocol.decode_replay_tracker_events(mpyq.MPQArchive(str(folder/'episode/game.SC2Replay')).read_file('replay.tracker.events')))
 cutoffs=[]
 for cutoff in (6000,8800,9224):
  if tr[-1]['loop']<cutoff:continue
  births=sum(e['_gameloop']<cutoff and e['_event'].endswith('.SUnitBornEvent') and e.get('m_upkeepPlayerId')==1 and e.get('m_unitTypeName')==b'SCV' for e in events)
  seconds=0
  for row,nxt in zip(tr,tr[1:]):
   if nxt['loop']>=cutoff:break
   if row['observation']['player']['food_used']<row['observation']['player']['food_cap']:continue
   for u in row['observation']['units']:
    orders=u.get('orders',[])
    if u['alliance']!=1 or u['unit_type'] not in (18,132) or not orders or orders[0]['ability_id']!=524 or orders[0].get('progress',0)!=0:continue
    following=next((v for v in nxt['observation']['units'] if v['tag']==u['tag']),{}).get('orders',[])
    if following and following[0]['ability_id']==524 and following[0].get('progress',0)==0:seconds+=(nxt['loop']-row['loop'])/22.4
  state=max((row for row in tr if row['loop']<cutoff),key=lambda r:r['loop'])
  cutoffs.append(dict(cutoff_exclusive=cutoff,scv_births=births,stalled_producer_seconds=seconds,loop=state['loop'],player=state['observation']['player']))
 comparisons.append(dict(run=n,last_loop=tr[-1]['loop'],cutoffs=cutoffs))
errors=[e for row in rows for e in row['observation']['action_errors']];retained=[];other=[]
for row in rows:
 for e in row['observation']['action_errors']:
  own=next((u for u in row['observation']['units'] if u['tag']==e['unit_tag'] and u['alliance']==1),{})
  (retained if e['result']==13 and any(o['ability_id']==e['ability_id'] and o.get('progress',0)==0 for o in own.get('orders',[])) else other).append(e)
result=dict(status='verified_reactive_supply_ablation',resolved=ep['instructions_resolved'],total=ep['total'],divergence=ep['divergence'],assistance=assistance,comparisons=comparisons,retained_supply_warnings=len(retained),other_action_errors=other,peak_cpu=report['peak_cpu'],forced_exit=ep['divergence'] is not None,training=False,rl=False,limitations=['Fixed human plan plus explicit scripted supply, mining and combat; no learned policy or win claim.','Full fixed-plan completion and later source timing may fail despite improved supply. Compare at shared cutoffs only.'])
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(out/'source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(result))
