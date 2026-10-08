import json,hashlib,mpyq
from pathlib import Path
from src.learning.replay_extract import load_protocol,replay_metadata
root=Path('logs/roadmap');checks=[]
for number in (1,2):
 out=root/f'supply-queue-fixture-{number:02d}';report=json.loads((out/'report.json').read_text());contract=json.loads((out/'contract.json').read_text());rows=[json.loads(l) for l in (out/'trace.jsonl').read_text().splitlines()];assert report['status']=='failed' and len(report['results'])==1 and report['results'][0]['status']=='completed' and report['results'][0]['frames']==len(rows) and report['peak_cpu']<80
 for p,h in contract['bindings'].items():
  path=Path(p);rel=path.relative_to(Path.cwd()) if path.is_absolute() else path
  if path.suffix in ('.py','.json'):path=out/'source-snapshot'/rel
  assert hashlib.sha256(path.read_bytes()).hexdigest()==h,path
 first=next(r for r in rows if r['commands']);assert first['results']==[1] and first['observation']['player']['food_used']==first['observation']['player']['food_cap']==15
 assert (626 in first['available'])==(number==2)
 tag=first['commands'][0]['units'][0];waiting=[];progress=[];birth=None
 for r in rows:
  assert not r['observation']['action_errors']
  actor=next((u for u in r['observation']['units'] if u['tag']==tag),None)
  if actor is None:continue
  for order in actor.get('orders',[]):
   if order['ability_id']==626:
    if r['loop']<=224:waiting.append(order.get('progress',0))
    elif r['loop']<1192:progress.append(order.get('progress',0))
  if any(u['alliance']==1 and u['unit_type']==689 for u in r['observation']['units']) and birth is None:birth=r['loop']
 assert waiting and not any(waiting) and max(progress)>.9 and birth==1192
 assert sum(bool(r['commands']) for r in rows if r['loop']<birth)==1
 replay=out/'game.SC2Replay';meta,_=replay_metadata(replay);pr=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));init=pr.decode_replay_initdata(mpyq.MPQArchive(str(replay)).read_file('replay.initData'));assert init['m_syncLobbyState']['m_userInitialData'][0]['m_randomSeed']==820001
 result=dict(status='verified_supply_blocked_training_queue',fixture=number,ignore_resource_query=number==2,ability_queried=626,available=number==2,accepted=1,retained_zero_progress_before_supply_freed=True,completed_without_resubmission=True,birth_loop=birth,action_errors=0,peak_cpu=report['peak_cpu'],debug_resources_and_units=True,supervisor_status='failed',supervisor_reason='fixture completed receipt is outside reused fixed-plan status vocabulary',training=False,rl=False)
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(out/'source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes());checks.append(result)
print(json.dumps(checks))
