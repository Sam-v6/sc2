import json,gzip,hashlib,mpyq
from pathlib import Path
from src.learning.replay_extract import load_protocol,replay_metadata
root=Path('logs/roadmap');results=[]
for number in (18,19):
 out=root/f'fixed-human-plan-native-{number:02d}';report=json.loads((out/'report.json').read_text());contract=json.loads((out/'contract.json').read_text());episode=json.loads((out/'episode/episode.json').read_text());rows=[json.loads(l) for l in gzip.open(out/'episode/trace.jsonl.gz','rt')]
 assert report['status']=='completed' and report['peak_cpu']<80 and len(rows)==episode['frames']
 for p,h in contract['bindings'].items():
  path=Path(p);rel=path.relative_to(Path.cwd()) if path.is_absolute() else path
  if path.suffix in ('.py','.json'):path=out/'source-snapshot'/rel
  assert hashlib.sha256(path.read_bytes()).hexdigest()==h,path
 warnings=[];fatal=[]
 for row in rows:
  for error in row['observation']['action_errors']:
   if error['result']==13:
    actor=next(u for u in row['observation']['units'] if u['tag']==error['unit_tag'] and u['alliance']==1)
    assert any(o['ability_id']==error['ability_id'] and o.get('progress',0)==0 for o in actor.get('orders',[]))
    warnings.append(dict(loop=row['loop'],error=error))
   else:fatal.append(dict(loop=row['loop'],error=error))
 assert len(warnings)==sum(h.get('event')=='production_waiting_for_supply' for h in episode['history'])
 if number==18:assert not fatal and episode['divergence']['reason']=='supply'
 else:
  assert len(fatal)==1 and fatal[0]['error']['result']==53
  binding=rows[-1]['bindings'].get('4392484873');assert binding is not None
  assert any(u['tag']==binding and u['unit_type']==27 and u['position'][:2]==[134.5,37.5] for r in rows for u in r['observation']['units'])
  assert episode['divergence']['submitted']['command']['units']==[binding]
 replay=out/'episode/game.SC2Replay';meta,_=replay_metadata(replay);protocol=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));init=protocol.decode_replay_initdata(mpyq.MPQArchive(str(replay)).read_file('replay.initData'));assert init['m_syncLobbyState']['m_userInitialData'][0]['m_randomSeed']==817501
 result=dict(status='verified_fixed_queue_diagnostic',native=number,resolved=episode['instructions_resolved'],total=243,supply_warnings_retaining_pending_orders=len(warnings),other_errors=len(fatal),recovered_source_factory_created=number==19,failure=episode['divergence'],peak_cpu=report['peak_cpu'],forced_leave=True,training=False,rl=False)
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(out/'source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes());results.append(result)
 if number==19:
  failure=episode['divergence'];target=failure['submitted']['command']['target_point'];loop=failure['loop'];near=[]
  for r in rows:
   if loop-32<=r['loop']<=loop:
    occupants=[{k:u.get(k) for k in ('tag','unit_type','alliance','position','radius','orders','is_flying','add_on_tag')} for u in r['observation']['units'] if abs(u['position'][0]-target[0])<3 and abs(u['position'][1]-target[1])<3]
    near.append(dict(loop=r['loop'],occupants=occupants,commands=r.get('commands',[])))
  (out/'landing-occupancy-audit.json').write_text(json.dumps(dict(failure=failure,frames=near),indent=2)+'\n')
print(json.dumps(results))
