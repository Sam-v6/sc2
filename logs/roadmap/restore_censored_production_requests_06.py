"""Retain issued requests; net queue count cannot prove repetition."""
import json,hashlib,mpyq,math
from pathlib import Path
from src.learning.tournament_record import decode_record
from src.learning.replay_extract import replay_metadata,load_protocol
root=Path('logs/roadmap');out=root/'fixed-human-production-plan-06';out.mkdir(exist_ok=False);parentpath=root/'fixed-human-production-plan-05/plan.json';plan=json.loads(parentpath.read_text());recordpath=root/'pro-preconverted-probe-01/fall-record-870.bin';replay=root/'pro-preconverted-probe-01/2cda222081e80d9a1c188698ce9bcda6.SC2Replay';r=decode_record(recordpath.read_bytes());f=r['units']['fields'];loops=list(map(int,r['steps']['game_loop']));meta,_=replay_metadata(replay);pr=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));tracker=list(pr.decode_replay_tracker_events(mpyq.MPQArchive(str(replay)).read_file('replay.tracker.events')));proofs=[];restored=[]
for t in plan['repeated_present_orders']:
 s=loops.index(t['loop']);tag=t['command']['units'][0];indices=[next(i for i,st in enumerate(r['units']['step']) if st==step and int(f['id'][i])==tag) for step in (s,s+1)];orders=[[f['order'+str(k)][i] for k in range(4) if f['order'+str(k)][i]['ability']==t['command']['ability']] for i in indices];point=list(map(float,f['pos'][indices[0]][:2]));unit=t['name'].removeprefix('Train ')
 births=[e for e in tracker if e['_event'].endswith('.SUnitBornEvent') and e.get('m_upkeepPlayerId')==1 and e.get('m_unitTypeName')==unit.encode() and t['loop']<e['_gameloop']<=loops[s+1] and math.dist(point,[e['m_x'],e['m_y']])<5]
 if births:
  status='completion_inside_snapshot_window';assert len(births)==1 and len(orders[0])==len(orders[1])==1 and orders[0][0]['progress']>.97 and orders[1][0]['progress']==0
 else:
  status='queue_censored_at_four_orders';assert len(orders[0])==len(orders[1])==4
 proof=dict(loop=t['loop'],sequence=t['sequence'],actor=tag,classification=status,before_loop=t['loop'],after_loop=loops[s+1],observed_counts=[len(o) for o in orders],before_progress=[float(o['progress']) for o in orders[0]],after_progress=[float(o['progress']) for o in orders[1]],nearby_births=[dict(loop=e['_gameloop'],kind=unit,point=[e['m_x'],e['m_y']]) for e in births],issued_command_retained=True,paid_start_claim=False)
 proofs.append(proof);restored.append(dict(t,existing_queue_evidence=[status],queue_effect_proof=proof))
assert len(restored)==4
plan['historical_repeat_candidates']=plan['repeated_present_orders'];plan['repeated_present_orders']=[];plan['tickets']=sorted(plan['tickets']+restored,key=lambda t:(t['loop'],t['sequence']));plan['limitations']=[text for text in plan['limitations'] if not text.startswith('Four source repeated/present orders')];plan['limitations'].append('Four previously omitted issued requests restored: two completion-window counterexamples and two queues censored at four orders. This does not infer exact payment/completion for the censored cases.')
paths=[Path(__file__),parentpath,recordpath,replay,Path('src/learning/tournament_record.py')];plan['bindings']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');(out/'queue-effect-audit.json').write_text(json.dumps(dict(status='counterexamples_to_repeat_classification',restored=proofs,total=247,training=False,rl=False),indent=2)+'\n');snap=out/'source-snapshot';snap.mkdir()
for p in paths:
 if p.suffix=='.py':(snap/p.name).write_bytes(p.read_bytes())
print(json.dumps(dict(total=len(plan['tickets']),restored=proofs)))
