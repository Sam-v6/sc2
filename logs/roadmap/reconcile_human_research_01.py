"""Recover only catalogue-backed Lift/Land aliases with observed own actors."""
from pathlib import Path
from collections import Counter
import hashlib,json,mpyq
from src.learning.tournament_record import decode_record
from src.learning.tournament_commands import reconcile_commands
from src.learning.tournament_tracker import CausalTracker
from src.learning.production_identity import producer_ability,research_ability
import sc2reader
from src.learning.replay_extract import load_protocol,replay_metadata
from src.learning.tournament_import import check_bindings,import_game
ROOT=Path('logs/roadmap/pro-preconverted-probe-01');OUT=Path('logs/roadmap/human-research-reimport-01');OUT.mkdir(exist_ok=True)
old_path=Path('logs/roadmap/human-in-place-addon-reimport-01/reconciliation.json');old=json.loads(old_path.read_text());g=next(x for x in old['games'] if x['idx']==870);check_bindings(g)
record_path=ROOT/'fall-record-870.bin';record=decode_record(record_path.read_bytes());actions_path=ROOT/'fall-actions-870.json';wire=json.loads(actions_path.read_text());assert wire['record_sha256']==hashlib.sha256(record_path.read_bytes()).hexdigest()
source_catalog=Path('logs/roadmap/joint-frozen-native-wait-02/static.json');data=json.loads(source_catalog.read_text())['game_data'];catalog={a['ability_id']:a for a in data['abilities']};names={u['unit_id']:u['name'] for u in data['units']}
replay=ROOT/'2cda222081e80d9a1c188698ce9bcda6.SC2Replay';metadata,_=replay_metadata(replay);archive=mpyq.MPQArchive(str(replay));proto=load_protocol(int(metadata['BaseBuild'].removeprefix('Base')));events=list(proto.decode_replay_tracker_events(archive.read_file('replay.tracker.events')));tracker=CausalTracker(events,1,data)
boundary={(e['_gameloop'],(e['m_unitTagIndex']<<18)|e['m_unitTagRecycle']):{u['name']:u['unit_id'] for u in data['units']}.get(e['m_unitTypeName'].decode()) for e in events if e['_event'].endswith('.SUnitTypeChangeEvent')}
u=record['units']['fields'];frames=[{} for _ in record['steps']['game_loop']]
for i,step in enumerate(record['units']['step']):
 if u['alliance'][i]==1:frames[int(step)][int(u['id'][i])]=int(u['unitType'][i])
verified=0
for i,row in enumerate(wire['actions']):
 loop=int(record['steps']['game_loop'][i]);assert row['loop']==loop;tracker.advance(loop);types={}
 for command in row['actions']:
  for tag in command['tags']:
   kind=frames[i].get(tag);original=tag & 0xFFFFFFFF
   if kind is None or tracker.owners.get(original)!=1:continue
   expected=tracker.own_types.get(original)
   if kind not in (expected,boundary.get((loop,original))):raise ValueError((loop,tag,kind,expected))
   types[tag]=names[kind];verified+=1
 row['unit_types']=types
raw_path=ROOT/'raw-commands-870.json';raw=json.loads(raw_path.read_text());selections={(x['loop'],x['sequence']):x['tags'] for x in g['selections']};replay_names={(x['link'],x['index']):x['name'] for x in g['verified_candidate_names']}
reader=sc2reader.load_replay(str(replay),load_level=2,load_map=False)
metadata_mappings=[]
for event in raw:
 original=event['m_abil']
 if original is None:continue
 key=(original['m_abilLink'],original['m_abilCmdIndex']);metadata=reader.datapack.abilities.get((key[0]<<5)|key[1])
 if metadata is None:continue
 candidate=producer_ability(metadata.build_unit.name,key[1],data) if metadata.build_unit else research_ability(metadata.name,key[1],data)
 if candidate is not None:
  replay_names[key]=catalog[candidate]['friendly_name'];metadata_mappings.append(dict(link=key[0],index=key[1],reader_name=metadata.name,native_specific=candidate,native_name=replay_names[key]))
accepted,audit=reconcile_commands(raw,wire['actions'],selections,catalog,replay_names)
translated={(t['loop'],t['sequence']) for t in g['label_translations']}
accepted += [dict(r,command=__import__('src.learning.gameplay',fromlist=['Command']).Command(**dict(r['command'],units=tuple(r['command']['units'])))) for r in g['accepted'] if (r['loop'],r['sequence']) in translated]
accepted.sort(key=lambda r:(r['loop'],r['sequence']))
audit['unresolved_events']=[e for e in audit['unresolved_events'] if (e['event']['_gameloop'],e['event']['m_sequence']) not in translated]
audit['matched_issued_commands']=len(accepted);audit['source_effect_equivalence_commands']=len(translated)

new={(x['loop'],x['sequence']):x['command'].as_dict() for x in accepted};previous={(x['loop'],x['sequence']):x['command'] for x in g['accepted']}
assert all(new.get(k)==v for k,v in previous.items()),'Old accepted command changed or lost'
added=[dict(loop=k[0],sequence=k[1],command=v) for k,v in new.items() if k not in previous]
assert added and all(x['command']['ability'] in (624,769,3700,3701) for x in added)
paths=[Path(__file__),old_path,record_path,Path('src/learning/tournament_commands.py'),Path('src/learning/tournament_record.py'),Path('src/learning/tournament_tracker.py'),Path('src/learning/production_identity.py')]
receipt=dict(games=[dict(g,accepted=[dict(x,command=x['command'].as_dict()) for x in accepted],audit=audit,verified_candidate_names=[dict(link=k[0],index=k[1],name=v) for k,v in replay_names.items()],metadata_mappings=metadata_mappings)],training_eligible=False,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
reconciliation=OUT/'reconciliation.json';reconciliation.write_text(json.dumps(receipt,indent=2)+'\n')
job=dict(record=str(record_path),replay=str(replay),map=str(ROOT/'original-acropolis.s2ma'),catalog=str(source_catalog),reconciliation=str(reconciliation),phase=str(ROOT/'issue-loop-phase-verification-01.json'),record_index=870,output=str(OUT/'corpus'/'870'))
report=dict(status='reconciled_actor_verified_lift_land_aliases',old_commands=len(previous),new_commands=len(new),added=added,actor_type_checks=verified,added_counts=dict(Counter(x['command']['ability'] for x in added)),training=False,rl=False,job=job)
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','old_commands','new_commands','actor_type_checks','added_counts']}),flush=True)
import_game(job);print('import complete',flush=True)
