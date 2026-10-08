"""Independently verify source-effect addon labels and absence of effect leakage."""
from pathlib import Path
import base64,gzip,hashlib,json,math,mpyq
import numpy as np
from src.learning.tournament_record import decode_record
from src.learning.replay_extract import load_protocol,replay_metadata
OUT=Path('logs/roadmap/human-in-place-addon-reimport-01');new=OUT/'corpus/870';old=Path('logs/roadmap/human-addon-reimport-01/corpus/870');receipt=json.loads((new/'dataset.json').read_text());assert receipt['status']=='completed' and receipt['disable_fog'] is False
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for mapping in [receipt['source_bindings'],receipt['code_bindings'],{str(new/n):h for n,h in receipt['corpus_bindings'].items()}]:
 for p,h in mapping.items():assert sha(p)==h,p
with gzip.open(old/'examples.jsonl.gz','rt') as f:before={(r['action_loop'],r['source_sequence']):r for r in map(json.loads,f)}
with gzip.open(new/'examples.jsonl.gz','rt') as f:after={(r['action_loop'],r['source_sequence']):r for r in map(json.loads,f)}
assert len(before)==839 and len(after)==842 and set(before)<=set(after)
for key,a in before.items():
 b=after[key];assert a['original_command']==b['original_command'] and a['commands']==b['commands'] and 'label_translation' not in b
 for field in ['player','map','units','owned_memory','memory','unknown_fields']:assert a['observation'].get(field)==b['observation'].get(field),(key,field)
source=Path('logs/roadmap/pro-preconverted-probe-01');raw=json.loads((source/'raw-commands-870.json').read_text());events={(e['_gameloop'],e['m_sequence']):e for e in raw};record=decode_record((source/'fall-record-870.bin').read_bytes());u=record['units']['fields'];replay=source/'2cda222081e80d9a1c188698ce9bcda6.SC2Replay';meta,_=replay_metadata(replay);archive=mpyq.MPQArchive(str(replay));tracker=list(load_protocol(int(meta['BaseBuild'].removeprefix('Base'))).decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
g=json.loads((OUT/'reconciliation.json').read_text())['games'][0];selections={(s['loop'],s['sequence']):s['tags'] for s in g['selections']};used=[tuple(r['converted_position']) for r in g['accepted']];assert len(used)==len(set(used))
added=set(after)-set(before);assert {k[0] for k in added}=={2837,4000,5164};checks=[]
for key in sorted(added):
 row=after[key];proof=row['label_translation'];event=events[key];cmd=row['original_command'];assert proof['source_event']==event and event['m_cmdFlags']==0x1000100 and proof['flag_semantics']=='uninterpreted' and proof['effect_is_label_only']
 assert len([e for e in raw if e['_gameloop']==key[0]])==1
 assert cmd['ability']==(3683 if key[0]==2837 else 3682) and cmd['target_point'] is None and not cmd['queue'] and not cmd['autocast']
 assert cmd['units']==[proof['actor']['tag']] and proof['selected']==sorted(selections[key])
 frame=int(np.searchsorted(record['steps']['game_loop'],key[0]));assert int(record['steps']['game_loop'][frame])==key[0];wire=record['actions'][frame];assert len(wire)==1 and wire[0]['ability']==cmd['ability'] and list(wire[0]['units'])==cmd['units'] and wire[0]['target_type']==0
 ix=np.flatnonzero((record['units']['step']==frame)&(u['id']==cmd['units'][0])&(u['alliance']==1));assert len(ix)==1;i=int(ix[0]);assert int(u['unitType'][i])==21 and not u['is_flying'][i] and u['build_progress'][i]==1
 point=[event['m_data']['TargetPoint'][axis]/4096 for axis in ['x','y']];assert point==u['pos'][i][:2].tolist()==proof['actor']['position']
 st=row['observation'];own={x['tag']:x for x in st['units'] if x['alliance']==1};assert own[cmd['units'][0]]['position'][:2]==point
 # Every selected matching producer is actually observed; no multi-producer expansion.
 selected_actors=[x for x in st['units'] if x['alliance']==1 and x['tag'] & 0xFFFFFFFF in selections[key] and x['unit_type'] in [21,46]];assert [x['tag'] for x in selected_actors]==cmd['units']
 starts=[e for e in tracker if e['_gameloop']==key[0] and e['_event'].endswith(('SUnitInitEvent','SUnitBornEvent')) and e['m_upkeepPlayerId']==1 and e['m_unitTypeName']==(b'BarracksReactor' if key[0]==2837 else b'BarracksTechLab') and [e['m_x'],e['m_y']]==[point[0]+2.5,point[1]-.5]];assert len(starts)==1
 expected=dict(starts[0],m_unitTypeName=starts[0]['m_unitTypeName'].decode());assert expected==proof['addon_start']
 new_tag=(starts[0]['m_unitTagIndex']<<18)|starts[0]['m_unitTagRecycle'];assert not any(x['tag'] & 0xFFFFFFFF==new_tag for x in st['units'] if x['alliance']==1)
 assert 'label_translation' not in st and 'addon_start' not in st
 image=st['map']['visibility'];pixels=base64.b64decode(image['data']);w=image['width'];sx,sy=image['world_size'];scale=w/max(sx,sy)
 for enemy in st['units']:
  if enemy['alliance']!=4:continue
  x,y=enemy['position'][:2];ix,iy=math.floor(x*scale),math.floor((sy-y)*scale);assert 0<=ix<w and 0<=iy<image['height'] and pixels[iy*w+ix]==2
 checks.append(dict(loop=key[0],ability=cmd['ability'],source_target=point,canonical_target=None,new_addon_absent_from_input=True))
assert {14686,14692}<= {r['event']['_gameloop'] for r in receipt['issued_command_audit']['unresolved_events']}
paths=[Path(__file__),OUT/'reconciliation.json',new/'dataset.json',new/'examples.jsonl.gz',old/'examples.jsonl.gz',Path('logs/roadmap/addon-target-fixture-01/verification.json')]
v=dict(status='verified_source_effect_addon_labels',old_labels_preserved=839,new_labels=842,checks=checks,training=False,rl=False,bindings={str(p):sha(p) for p in paths},limitations=['Three narrow canonical execution labels; unknown replay flags remain uninterpreted.','Remote/grouped later commands remain excluded; no full-game plan or exact payment claim.'])
(OUT/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
