"""Independent source-level checks for recovered actor-specific Lift/Land labels."""
from pathlib import Path
from collections import Counter
import base64,gzip,hashlib,json,math
import numpy as np
from src.learning.tournament_record import decode_record
OUT=Path('logs/roadmap/human-lift-land-reimport-02');report=json.loads((OUT/'audit.json').read_text());new=OUT/'corpus'/'870';old=Path('logs/roadmap/human-visibility-reimport-01/corpus/870')
receipt=json.loads((new/'dataset.json').read_text());assert receipt['status']=='completed' and receipt['disable_fog'] is False and receipt['alignment']=='state_at_issue_loop_before_effect'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for mapping in [receipt['source_bindings'],receipt['code_bindings'],{str(new/name):digest for name,digest in receipt['corpus_bindings'].items()}]:
 for path,digest in mapping.items():assert sha(path)==digest,path
with gzip.open(old/'examples.jsonl.gz','rt') as f:before={(r['action_loop'],r['source_sequence']):r for r in map(json.loads,f)}
with gzip.open(new/'examples.jsonl.gz','rt') as f:after={(r['action_loop'],r['source_sequence']):r for r in map(json.loads,f)}
assert len(before)==804 and len(after)==836 and set(before)<=set(after)
assert (old/'static.json').read_bytes()==(new/'static.json').read_bytes()
for key,a in before.items():
 b=after[key];assert a['original_command']==b['original_command'] and a['commands']==b['commands']
 for field in ['player','map','units','owned_memory','memory','unknown_fields']:
  assert a['observation'].get(field)==b['observation'].get(field),(key,field)
added=set(after)-set(before);assert len(added)==32
recon=json.loads((OUT/'reconciliation.json').read_text())['games'][0];selections={(s['loop'],s['sequence']):s['tags'] for s in recon['selections']};names={(s['link'],s['index']):s['name'] for s in recon['verified_candidate_names']}
source=Path('logs/roadmap/pro-preconverted-probe-01');events={(e['_gameloop'],e['m_sequence']):e for e in json.loads((source/'raw-commands-870.json').read_text())};record=decode_record((source/'fall-record-870.bin').read_bytes());u=record['units']['fields'];unit_names={x['unit_id']:x['name'] for x in json.loads((new/'static.json').read_text())['game_data']['units']};counts=Counter();fog_checks=0
for key in sorted(added):
 row=after[key];cmd=row['original_command'];event=events[key];name=names[event['m_abil']['m_abilLink'],event['m_abil']['m_abilCmdIndex']];operation='Lift' if cmd['ability']==3679 else 'Land';assert cmd['ability'] in (3678,3679) and name.startswith(operation);parent=name.removeprefix(operation).strip();assert event['m_abil']['m_abilCmdIndex']==0
 assert event['m_cmdFlags'] & 0x100 and not event['m_cmdFlags'] & ~(0x100|2|8|0x10000|0x20000)
 assert cmd['queue']==bool(event['m_cmdFlags'] & 2) and not cmd['autocast']
 selected=selections[key];assert selected is not None and {t & 0xFFFFFFFF for t in cmd['units']}<=set(selected)
 frame=int(np.searchsorted(record['steps']['game_loop'],key[0]));assert int(record['steps']['game_loop'][frame])==key[0]
 wire=[a for a in record['actions'][frame] if a['ability']==cmd['ability'] and list(a['units'])==cmd['units']];assert len(wire)==1
 for actor in cmd['units']:
  ix=np.flatnonzero((record['units']['step']==frame)&(u['id']==actor)&(u['alliance']==1));assert len(ix)==1
  assert unit_names[int(u['unitType'][ix[0]])].removesuffix('Flying')==parent
 if operation=='Lift':assert 'None' in event['m_data'] and cmd['target_point'] is None and wire[0]['target_type']==0
 else:
  point=[event['m_data']['TargetPoint'][axis]/4096 for axis in ['x','y']];assert cmd['target_point']==point and wire[0]['target_type']==2 and list(wire[0]['target_point'])==list(map(int,point))
 st=row['observation'];image=st['map']['visibility'];pixels=base64.b64decode(image['data']);width=image['width'];sx,sy=image['world_size'];scale=width/max(sx,sy)
 for enemy in st['units']:
  if enemy['alliance']!=4:continue
  x,y=enemy['position'][:2];ix,iy=math.floor(x*scale),math.floor((sy-y)*scale);assert 0<=ix<width and 0<=iy<image['height'] and pixels[iy*width+ix]==2;fog_checks+=1
 counts[operation]+=1
assert counts=={'Lift':16,'Land':16}
paths=[OUT/'audit.json',OUT/'reconciliation.json',new/'dataset.json',new/'examples.jsonl.gz',old/'examples.jsonl.gz',Path(__file__)]
verification=dict(status='verified_source_lift_land_reimport',old_labels_preserved=804,added_labels=32,added_by_operation=dict(counts),new_labels=836,new_visible_enemy_checks=fog_checks,training=False,rl=False,bindings={str(p):sha(p) for p in paths},limitations=['Only this teaching game is reimported; no development games or previous corpora changed.','Addon flags/targets and attachment reconstruction remain unresolved.','This verifies source command identity and current observations, not production acceptance or native strength.'])
(OUT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n');print(json.dumps(verification))
