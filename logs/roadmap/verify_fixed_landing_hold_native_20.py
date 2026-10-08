import json,gzip,hashlib,mpyq
from pathlib import Path
from src.learning.replay_extract import load_protocol,replay_metadata
root=Path('logs/roadmap');out=root/'fixed-human-plan-native-20';report=json.loads((out/'report.json').read_text());contract=json.loads((out/'contract.json').read_text());episode=json.loads((out/'episode/episode.json').read_text());rows=[json.loads(l) for l in gzip.open(out/'episode/trace.jsonl.gz','rt')]
assert report['status']=='completed' and report['peak_cpu']<=80 and len(rows)==episode['frames']==1154
for p,h in contract['bindings'].items():
 path=Path(p);rel=path.relative_to(Path.cwd()) if path.is_absolute() else path
 if path.suffix in ('.py','.json'):path=out/'source-snapshot'/rel
 assert hashlib.sha256(path.read_bytes()).hexdigest()==h,path
warnings=[]
for r in rows:
 for e in r['observation']['action_errors']:
  assert e['result']==13
  actor=next(u for u in r['observation']['units'] if u['tag']==e['unit_tag'] and u['alliance']==1)
  assert any(o['ability_id']==e['ability_id'] and o.get('progress',0)==0 for o in actor.get('orders',[]))
  warnings.append(e)
assert len(warnings)==8
source=4392484873;tag=rows[-1]['bindings'][str(source)];land=next(h for h in episode['history'] if h.get('name')=='Land Factory' and h['command']['units']==[tag]);assert land['command']['target_point']==[131.5,41.5]
attached=[]
for r in rows:
 units=r['observation']['units'];actor=next((u for u in units if u['tag']==tag),None)
 if actor and actor['unit_type']==27 and not actor.get('is_flying') and actor.get('add_on_tag'):
  assert actor['position'][:2]==[131.5,41.5]
  addon=next(u for u in units if u['tag']==actor['add_on_tag']);assert addon['position'][:2]==[134,41];attached.append(r['loop'])
assert attached and episode['divergence']['reason']=='earlier_resource_commitment' and episode['divergence']['name']=='Train Cyclone'
replay=out/'episode/game.SC2Replay';meta,_=replay_metadata(replay);pr=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));init=pr.decode_replay_initdata(mpyq.MPQArchive(str(replay)).read_file('replay.initData'));assert init['m_syncLobbyState']['m_userInitialData'][0]['m_randomSeed']==817501
result=dict(status='verified_recovered_factory_shared_addon_transfer',resolved=148,total=243,source_factory_tag=source,first_attached_loop=min(attached),supply_warnings_with_retained_queue=8,other_action_errors=0,latest_failure=episode['divergence'],peak_cpu=report['peak_cpu'],forced_leave=True,training=False,rl=False)
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(out/'source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(result))
