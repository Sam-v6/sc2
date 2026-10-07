"""Independent receipt, queue counterexample, and actual landing verification."""
import gzip,hashlib,json,math
from pathlib import Path
import mpyq
from src.learning.replay_extract import replay_metadata,load_protocol
from src.learning.tournament_record import decode_record
root=Path('logs/roadmap'); ppath=root/'fixed-human-production-plan-06/plan.json';plan=json.loads(ppath.read_text());parent=json.loads((root/'fixed-human-production-plan-05/plan.json').read_text());key=lambda t:(t['loop'],t['sequence']);current={key(t):t for t in plan['tickets']}
assert len(plan['tickets'])==247 and len(current)==247
for t in parent['tickets']:assert current[key(t)]==t
assert not plan['repeated_present_orders'] and len(plan['historical_repeat_candidates'])==4
for path,digest in plan['bindings'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
record=decode_record((root/'pro-preconverted-probe-01/fall-record-870.bin').read_bytes());fields=record['units']['fields'];loops=list(map(int,record['steps']['game_loop']));replay=root/'pro-preconverted-probe-01/2cda222081e80d9a1c188698ce9bcda6.SC2Replay';meta,_=replay_metadata(replay);protocol=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));tracker=list(protocol.decode_replay_tracker_events(mpyq.MPQArchive(str(replay)).read_file('replay.tracker.events')))
proofs=[]
for t in parent['repeated_present_orders']:
 restored=current[key(t)];step=loops.index(t['loop']);tag=t['command']['units'][0];indices=[next(i for i,s in enumerate(record['units']['step']) if s==st and int(fields['id'][i])==tag) for st in (step,step+1)];queues=[[fields['order'+str(k)][i] for k in range(4) if fields['order'+str(k)][i]['ability']==524 if t['name']=='Train SCV'] for i in indices] if t['name']=='Train SCV' else [[fields['order'+str(k)][i] for k in range(4) if fields['order'+str(k)][i]['ability']==t['command']['ability']] for i in indices]
 births=[e for e in tracker if e['_event'].endswith('.SUnitBornEvent') and e.get('m_upkeepPlayerId')==1 and e.get('m_unitTypeName')==t['name'].removeprefix('Train ').encode() and t['loop']<e['_gameloop']<=loops[step+1] and math.dist(list(map(float,fields['pos'][indices[0]][:2])),[e['m_x'],e['m_y']])<5]
 classification=restored['queue_effect_proof']['classification']
 if births:
  assert classification=='completion_inside_snapshot_window' and len(births)==1 and len(queues[0])==len(queues[1])==1 and queues[0][0]['progress']>.97 and queues[1][0]['progress']==0
 else:assert classification=='queue_censored_at_four_orders' and len(queues[0])==len(queues[1])==4
 assert restored['command']==t['command'] and not restored['queue_effect_proof']['paid_start_claim'];proofs.append({'loop':t['loop'],'sequence':t['sequence'],'classification':classification})
verified=[]
for n,expected,warnings_expected in [(21,179,20),(22,186,21)]:
 out=root/f'fixed-human-plan-native-{n}';report=json.loads((out/'report.json').read_text());contract=json.loads((out/'contract.json').read_text());ep=json.loads((out/'episode/episode.json').read_text());rows=[json.loads(l) for l in gzip.open(out/'episode/trace.jsonl.gz','rt')]
 assert report['status']=='completed' and report['peak_cpu']<=80 and len(rows)==ep['frames'] and ep['instructions_resolved']==expected and ep['total']==247
 for path,digest in contract['bindings'].items():
  original=Path(path);rel=original.relative_to(Path.cwd()) if original.is_absolute() else original;actual=out/'source-snapshot'/rel if original.suffix in ('.py','.json') else original
  assert hashlib.sha256(actual.read_bytes()).hexdigest()==digest,actual
 warnings=[]
 for row in rows:
  for error in row['observation']['action_errors']:
   assert error['result']==13
   actor=next(u for u in row['observation']['units'] if u['tag']==error['unit_tag'] and u['alliance']==1)
   assert any(o['ability_id']==error['ability_id'] and o.get('progress',0)==0 for o in actor.get('orders',[]));warnings.append(error)
 assert len(warnings)==warnings_expected
 meta,_=replay_metadata(out/'episode/game.SC2Replay');protocol=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));init=protocol.decode_replay_initdata(mpyq.MPQArchive(str(out/'episode/game.SC2Replay')).read_file('replay.initData'));assert init['m_syncLobbyState']['m_userInitialData'][0]['m_randomSeed']==817501
 item={'run':n,'resolved':expected,'total':247,'retained_supply_warnings':len(warnings),'other_errors':0,'peak_cpu':report['peak_cpu'],'forced_diagnostic_exit':True,'divergence':ep['divergence']}
 if n==22:
  assert {'event':'superseded_unsubmitted_landing','loop':9560,'ticket':169,'replacement_ticket':170} in ep['history']
  tag=rows[-1]['bindings']['4398252033'];landed=[row['loop'] for row in rows if any(u['tag']==tag and u['unit_type']==27 and not u.get('is_flying') and u['position'][:2]==[148.5,40.5] for u in row['observation']['units'])];assert landed
  item['corrected_factory_first_landed_loop']=min(landed);item['corrected_factory_position']=[148.5,40.5]
 verified.append(item)
result={'status':'verified_restored_issued_requests_and_corrected_landing','restored':proofs,'runs':verified,'training':False,'rl':False,'limitations':['Fixed source macro playback with scripted assistance against VeryEasy; forced exits are not natural losses or learned wins.','Restoring requests did not improve same-cutoff SCV births (45 vs source55). Queues and different combat attrition require reactive supply diagnosis.']}
(root/'fixed-human-production-plan-06/verification.json').write_text(json.dumps(result,indent=2)+'\n');(root/'fixed-human-production-plan-06/source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(result))
