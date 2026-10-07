"""Reconstruct addon starts and producer movement from native traces/replays."""
import hashlib,json,math
from pathlib import Path
import mpyq
from src.learning.replay_extract import load_protocol,replay_metadata
ROOT=Path('logs/roadmap/addon-target-fixture-01');report=json.loads((ROOT/'report.json').read_text());assert report['status']=='completed' and len(report['results'])==4 and report['peak_cpu']<=80
for name,digest in report['bindings'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
checks=[];paths=[ROOT/'report.json',ROOT/'contract.json',Path(__file__)]
for receipt in report['results']:
 job=receipt['job'];assert receipt['status']=='completed';trace=Path(job['trace']);replay=Path(job['replay']);paths += [trace,replay];rows=list(map(json.loads,trace.read_text().splitlines()));issued=[r for r in rows if r['commands']];assert len(issued)==1;issue=issued[0];cmd=issue['commands'][0];actor=cmd['units'][0];assert cmd['ability']==3682 and issue['results']==[1];assert not any(r['delayed_errors'] for r in rows)
 for r in rows:assert len(r['commands'])==len(r['results'])
 target=issue['origin'] if job['case'] in ['no_target','own_point'] else issue['destination'];assert cmd['target_point']==(None if job['case']=='no_target' else target)
 final=rows[-1]['observation'];producer=next(u for u in final['units'] if u['tag']==actor);assert producer['unit_type']==21 and math.dist(producer['position'][:2],target)<.01
 addons=[u for u in final['units'] if u['alliance']==1 and u['unit_type']==37];assert len(addons)==1;addon=addons[0];expected=[target[0]+2.5,target[1]-.5];assert math.dist(addon['position'][:2],expected)<.01 and addon['build_progress']>0
 if addon['build_progress']==1:assert producer['add_on_tag']==addon['tag']
 meta,_=replay_metadata(replay);proto=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));archive=mpyq.MPQArchive(str(replay));starts=[]
 for event in proto.decode_replay_tracker_events(archive.read_file('replay.tracker.events')):
  if event['_event'].endswith(('SUnitInitEvent','SUnitBornEvent')) and event['m_upkeepPlayerId']==1 and event['m_unitTypeName']==b'BarracksTechLab':starts.append(event)
 assert len(starts)==1;start=starts[0];assert start['_gameloop']>=issue['loop'] and math.dist([start['m_x'],start['m_y']],expected)<1
 checks.append(dict(case=job['case'],accepted=1,action_errors=0,producer_destination=target,addon_position=addon['position'][:2],addon_progress=addon['build_progress'],tracker_start_loop=start['_gameloop']))
verification=dict(status='verified_native_addon_target_semantics',checks=checks,peak_cpu=report['peak_cpu'],training=False,rl=False,engineering_only=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},limitations=['Debug resources and producer creation isolate physical command behavior; no opponent strength claim.','Thirty-second cutoff proves relocated starts, not completion for every case.','Current native engine conformance does not prove semantics of unsupported historical replay flags.'])
(ROOT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n');print(json.dumps(verification))
