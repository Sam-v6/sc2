"""Add explicit source-effect equivalence labels, leaving raw flags uninterpreted."""
from pathlib import Path
import hashlib,json,mpyq
import numpy as np
from src.learning.addon_conformance import in_place_addon_label
from src.learning.tournament_import import check_bindings,import_game
from src.learning.tournament_record import decode_record
from src.learning.tournament_tracker import CausalTracker
from src.learning.replay_extract import load_protocol,replay_metadata
SOURCE=Path('logs/roadmap/human-addon-reimport-01');OUT=Path('logs/roadmap/human-in-place-addon-reimport-01');OUT.mkdir(exist_ok=True)
parent_verification=SOURCE/'verification.json';check_bindings(json.loads(parent_verification.read_text()))
parent=SOURCE/'reconciliation.json';old=json.loads(parent.read_text());g=old['games'][0];check_bindings(g)
root=Path('logs/roadmap/pro-preconverted-probe-01');record_path=root/'fall-record-870.bin';record=decode_record(record_path.read_bytes());u=record['units']['fields'];loops=record['steps']['game_loop'];catalog_path=Path('logs/roadmap/joint-frozen-native-wait-02/static.json');data=json.loads(catalog_path.read_text())['game_data'];names={x['unit_id']:x['name'] for x in data['units']}
replay=root/'2cda222081e80d9a1c188698ce9bcda6.SC2Replay';meta,_=replay_metadata(replay);archive=mpyq.MPQArchive(str(replay));proto=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));events=list(proto.decode_replay_tracker_events(archive.read_file('replay.tracker.events')));tracker=CausalTracker(events,1,data);starts=[e for e in events if e['_event'].endswith(('SUnitBornEvent','SUnitInitEvent'))]
selected={(x['loop'],x['sequence']):x['tags'] for x in g['selections']};raw_names={(x['link'],x['index']):x['name'] for x in g['verified_candidate_names']};translations=[];accepted=list(g['accepted']);remaining=[]
for unresolved in g['audit']['unresolved_events']:
 event=unresolved['event'];loop=event['_gameloop'];tracker.advance(loop);index=int(np.searchsorted(loops,loop));results=[]
 if event['m_cmdFlags']==0x1000100 and index<len(loops) and int(loops[index])==loop:
  actors=[]
  for i in np.flatnonzero((record['units']['step']==index)&(u['alliance']==1)):
   tag=int(u['id'][i]);kind=int(u['unitType'][i]);original=tag & 0xFFFFFFFF
   if tracker.owners.get(original)!=1 or tracker.own_types.get(original)!=kind:continue
   actors.append(dict(tag=tag,name=names[kind],alliance=1,position=u['pos'][i][:2].tolist(),is_flying=bool(u['is_flying'][i]),build_progress=float(u['build_progress'][i])))
  abil=event['m_abil'];raw_name=raw_names.get((abil['m_abilLink'],abil['m_abilCmdIndex']),'') if abil else ''
  for j,wire in enumerate(record['actions'][index]):
   action=dict(ability=wire['ability'],tags=list(wire['units']),target_type=wire['target_type'],target=wire.get('target_point',wire.get('target_unit')))
   result=in_place_addon_label(event=event,action=action,actors=actors,selected=selected.get((loop,event['m_sequence'])),starts=starts,player=1,raw_name=raw_name)
   if result:results.append((j,result))
 if len(results)==1:
  j,(command,proof)=results[0];translations.append(dict(loop=loop,sequence=event['m_sequence'],proof=proof));accepted.append(dict(loop=loop,sequence=event['m_sequence'],command=command.as_dict(),converted_position=[index,j]))
 else:remaining.append(unresolved)
assert [t['loop'] for t in translations]==[2837,4000,5164];accepted.sort(key=lambda r:(r['loop'],r['sequence']));assert len(accepted)==842
new_game=dict(g,accepted=accepted,label_translations=translations,audit=dict(g['audit'],matched_issued_commands=842,unresolved_events=remaining,source_effect_equivalence_commands=3))
paths=[Path(__file__),parent,parent_verification,record_path,Path('src/learning/addon_conformance.py'),Path('src/learning/tournament_import.py'),Path('src/learning/tournament_tracker.py'),Path('logs/roadmap/addon-target-fixture-01/verification.json')]
receipt=dict(games=[new_game],training_eligible=False,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths});reconciliation=OUT/'reconciliation.json';reconciliation.write_text(json.dumps(receipt,indent=2)+'\n')
job=dict(record=str(record_path),replay=str(replay),map=str(root/'original-acropolis.s2ma'),catalog=str(catalog_path),reconciliation=str(reconciliation),phase=str(root/'issue-loop-phase-verification-01.json'),record_index=870,output=str(OUT/'corpus/870'))
(OUT/'audit.json').write_text(json.dumps(dict(status='source_effect_equivalence_labels_ready',old_labels=839,new_labels=842,translated_loops=[t['loop'] for t in translations],job=job,training=False,rl=False),indent=2)+'\n');print('three source-effect labels verified; importing',flush=True);import_game(job);print('import complete',flush=True)
