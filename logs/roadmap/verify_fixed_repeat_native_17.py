import json,gzip,hashlib,mpyq
from pathlib import Path
from src.learning.replay_extract import load_protocol,replay_metadata
root=Path('logs/roadmap');results=[]
for number in (14,15,16,17):
 out=root/f'fixed-human-plan-native-{number:02d}';contract=json.loads((out/'contract.json').read_text());report=json.loads((out/'report.json').read_text());episode=json.loads((out/'episode/episode.json').read_text());rows=[json.loads(l) for l in gzip.open(out/'episode/trace.jsonl.gz','rt')]
 assert report['status']=='completed' and report['peak_cpu']<=80 and len(rows)==episode['frames']>0
 for p,h in contract['bindings'].items():
  path=Path(p);rel=path.relative_to(Path.cwd()) if path.is_absolute() else path
  if path.suffix in ('.py','.json'):path=out/'source-snapshot'/rel
  assert hashlib.sha256(path.read_bytes()).hexdigest()==h,path
 assert not any(r['observation']['action_errors'] for r in rows)
 assert rows[-1]['loop']==episode['divergence']['loop']<=13440 and episode['status']=='diverged'
 replay=out/'episode/game.SC2Replay';meta,_=replay_metadata(replay);protocol=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));init=protocol.decode_replay_initdata(mpyq.MPQArchive(str(replay)).read_file('replay.initData'));assert init['m_syncLobbyState']['m_userInitialData'][0]['m_randomSeed']==817501
 target=[136,69];found=[u for u in rows[-1]['observation']['units'] if u['alliance']==1 and u['unit_type'] in (19,47) and u['position'][:2]==target]
 assert bool(found)==(number!=14)
 if found:assert found[0]['build_progress']==1
 submitted=[h['loop'] for h in episode['history'] if h.get('name')=='Build SupplyDepot' and h['command']['target_point']==[153,56]]
 assert len(submitted)==1
 expected={15:6528,16:6520,17:6488}
 if number in expected:assert submitted[0]==expected[number]
 if number==17:
  assert episode['divergence']['name']=='Train Liberator' and rows[-1]['observation']['player']['food_workers']==36
 result=dict(status='verified_terminal_fixed_repeat_diagnostic',native=number,resolved=episode['instructions_resolved'],total=episode['total'],action_errors=0,source_depot_recovered=bool(found),next_depot_submitted=submitted[0],failure=episode['divergence'],peak_cpu=report['peak_cpu'],forced_leave=True,training=False,rl=False)
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(out/'source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes());results.append(result)
print(json.dumps(results))
