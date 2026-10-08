"""Reconcile source manager repeats with converted actions and observed own actors."""
import hashlib,json,mpyq
from pathlib import Path
from collections import Counter
from src.learning.replay_command_events import command_events
from src.learning.tournament_record import decode_record
from src.learning.tournament_commands import reconcile_commands
from src.learning.tournament_tracker import CausalTracker
from src.learning.replay_extract import load_protocol,replay_metadata
root=Path('logs/roadmap');out=root/'human-command-repeats-01';out.mkdir(exist_ok=False)
previous_path=root/'human-refinery-snapshot-reimport-01/reconciliation.json';old=json.loads(previous_path.read_text());g=old['games'][0]
source=root/'pro-preconverted-probe-01';replay=source/'2cda222081e80d9a1c188698ce9bcda6.SC2Replay';recordpath=source/'fall-record-870.bin';wirepath=source/'fall-actions-870.json';catalogpath=root/'joint-frozen-native-wait-02/static.json'
meta,_=replay_metadata(replay);proto=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));archive=mpyq.MPQArchive(str(replay))
original=list(proto.decode_replay_game_events(archive.read_file('replay.game.events')));events,excluded=command_events(original,0)
record=decode_record(recordpath.read_bytes());f=record['units']['fields'];wire=json.loads(wirepath.read_text());assert wire['record_sha256']==hashlib.sha256(recordpath.read_bytes()).hexdigest()
data=json.loads(catalogpath.read_text())['game_data'];catalog={a['ability_id']:a for a in data['abilities']};names={u['unit_id']:u['name'] for u in data['units']}
tracker_events=list(proto.decode_replay_tracker_events(archive.read_file('replay.tracker.events')));tracker=CausalTracker(tracker_events,1,data)
boundary={(e['_gameloop'],(e['m_unitTagIndex']<<18)|e['m_unitTagRecycle']):{u['name']:u['unit_id'] for u in data['units']}.get(e['m_unitTypeName'].decode()) for e in tracker_events if e['_event'].endswith('.SUnitTypeChangeEvent')}
own=[{} for _ in record['steps']['game_loop']]
for i,step in enumerate(record['units']['step']):
 if f['alliance'][i]==1:own[int(step)][int(f['id'][i])]=int(f['unitType'][i])
verified=0
for i,row in enumerate(wire['actions']):
 loop=int(record['steps']['game_loop'][i]);assert row['loop']==loop;tracker.advance(loop);types={}
 for command in row['actions']:
  for tag in command['tags']:
   kind=own[i].get(tag);low=tag&0xffffffff
   if kind is None or tracker.owners.get(low)!=1:continue
   assert kind in (tracker.own_types.get(low),boundary.get((loop,low)))
   types[tag]=names[kind];verified+=1
 row['unit_types']=types
selected={(s['loop'],s['sequence']):s['tags'] for s in g['selections']}
repeats=[e for e in events if e.get('source_manager')]
for e in repeats:
 origin=e['source_command'];selected[e['_gameloop'],e['m_sequence']]=selected.get((origin['loop'],origin['sequence']))
accepted,audit=reconcile_commands(events,wire['actions'],selected,catalog,{(s['link'],s['index']):s['name'] for s in g['verified_candidate_names']})
oldkeys={(a['loop'],a['sequence']) for a in g['accepted']};used={tuple(a['converted_position']) for a in g['accepted']}
added=[dict(a,command=a['command'].as_dict()) for a in accepted if (a['loop'],a['sequence']) not in oldkeys and tuple(a['converted_position']) not in used and (a['loop'],a['sequence']) in {(e['_gameloop'],e['m_sequence']) for e in repeats}]
assert any(a['loop']==7171 and a['sequence']==637 and a['command']['ability']==328 and a['command']['units']==[4357619713] and a['command']['target_point']==[134.5,37.5] for a in added)
new=dict(g,accepted=sorted(g['accepted']+added,key=lambda a:(a['loop'],a['sequence'])),
 selections=[dict(loop=k[0],sequence=k[1],tags=v) for k,v in selected.items()],audit=audit)
paths=[Path(__file__),previous_path,replay,recordpath,wirepath,catalogpath,Path('src/learning/replay_command_events.py'),Path('src/learning/tournament_commands.py'),Path('src/learning/tournament_tracker.py'),Path('src/learning/tournament_record.py')]
result=dict(status='reconciled_original_command_manager_repeats',old_commands=len(g['accepted']),new_commands=len(new['accepted']),added=added,added_counts=dict(Counter(a['command']['ability'] for a in added)),expanded_events=len(events),manager_repeats=len(repeats),excluded_contexts=len(excluded),actor_type_checks=verified,training=False,rl=False,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
(out/'reconciliation.json').write_text(json.dumps(dict(games=[new],training_eligible=False,bindings=result['bindings']),indent=2)+'\n');(out/'events.json').write_text(json.dumps(events,indent=2)+'\n');(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');(out/'excluded-contexts.json').write_text(json.dumps(excluded,indent=2)+'\n')
snap=out/'source-snapshot';snap.mkdir()
for p in paths:
 if p.suffix=='.py':(snap/p.name).write_bytes(p.read_bytes())
print(json.dumps({k:v for k,v in result.items() if k not in ('added','bindings')}))
