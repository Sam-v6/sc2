"""Verify three relocated addon labels without interpreting unsupported flags."""
from pathlib import Path
from collections import Counter
import base64,gzip,hashlib,json,math
import numpy as np
from src.learning.tournament_record import decode_record
OUT=Path('logs/roadmap/human-addon-reimport-01');new=OUT/'corpus/870';old=Path('logs/roadmap/human-lift-land-reimport-02/corpus/870');receipt=json.loads((new/'dataset.json').read_text());assert receipt['status']=='completed' and receipt['disable_fog'] is False and receipt['alignment']=='state_at_issue_loop_before_effect'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for mapping in [receipt['source_bindings'],receipt['code_bindings'],{str(new/n):h for n,h in receipt['corpus_bindings'].items()}]:
 for p,h in mapping.items():assert sha(p)==h,p
with gzip.open(old/'examples.jsonl.gz','rt') as f:before={(r['action_loop'],r['source_sequence']):r for r in map(json.loads,f)}
with gzip.open(new/'examples.jsonl.gz','rt') as f:after={(r['action_loop'],r['source_sequence']):r for r in map(json.loads,f)}
assert len(before)==836 and len(after)==839 and set(before)<=set(after)
for key,a in before.items():
 b=after[key];assert a['original_command']==b['original_command'] and a['commands']==b['commands']
 for field in ['player','map','units','owned_memory','memory','unknown_fields']:assert a['observation'].get(field)==b['observation'].get(field),(key,field)
assert (old/'static.json').read_bytes()==(new/'static.json').read_bytes()
expected={7534:(3682,'Barracks',0),7976:(3683,'Starport',1),8112:(3683,'Barracks',1)}
added=set(after)-set(before);assert {k[0] for k in added}==set(expected)
source=Path('logs/roadmap/pro-preconverted-probe-01');record=decode_record((source/'fall-record-870.bin').read_bytes());u=record['units']['fields'];raw={(e['_gameloop'],e['m_sequence']):e for e in json.loads((source/'raw-commands-870.json').read_text())};g=json.loads((OUT/'reconciliation.json').read_text())['games'][0];selections={(s['loop'],s['sequence']):s['tags'] for s in g['selections']};names={(s['link'],s['index']):s['name'] for s in g['verified_candidate_names']};unit_names={x['unit_id']:x['name'] for x in json.loads((new/'static.json').read_text())['game_data']['units']};checks=[]
for key in sorted(added):
 r=after[key];cmd=r['original_command'];event=raw[key];ability,parent,index=expected[key[0]];product='TechLab' if ability==3682 else 'Reactor';assert cmd['ability']==ability and event['m_abil']['m_abilCmdIndex']==index
 assert names[event['m_abil']['m_abilLink'],index]=='Build'+parent+product and event['m_cmdFlags']==0x100
 assert not cmd['queue'] and not cmd['autocast'] and cmd['target_unit'] is None
 point=[event['m_data']['TargetPoint'][axis]/4096 for axis in ['x','y']];assert cmd['target_point']==point
 frame=int(np.searchsorted(record['steps']['game_loop'],key[0]));assert int(record['steps']['game_loop'][frame])==key[0]
 candidates=[a for a in record['actions'][frame] if a['ability']==ability and list(a['units'])==cmd['units']];assert len(candidates)==1 and candidates[0]['target_type']==2 and list(candidates[0]['target_point'])==list(map(int,point))
 assert {t & 0xFFFFFFFF for t in cmd['units']}<=set(selections[key])
 for actor in cmd['units']:
  ix=np.flatnonzero((record['units']['step']==frame)&(u['id']==actor)&(u['alliance']==1));assert len(ix)==1 and unit_names[int(u['unitType'][ix[0]])].removesuffix('Flying')==parent
 st=r['observation'];image=st['map']['visibility'];pixels=base64.b64decode(image['data']);width=image['width'];sx,sy=image['world_size'];scale=width/max(sx,sy)
 for enemy in st['units']:
  if enemy['alliance']!=4:continue
  x,y=enemy['position'][:2];ix,iy=math.floor(x*scale),math.floor((sy-y)*scale);assert 0<=ix<width and 0<=iy<image['height'] and pixels[iy*width+ix]==2
 checks.append(dict(loop=key[0],ability=ability,parent=parent,target=point))
assert all(e['reason']=='Unsupported human command flags' for e in receipt['issued_command_audit']['unresolved_events'] if e['event']['_gameloop'] in [2837,4000,5164,14686,14692])
paths=[Path(__file__),OUT/'reconciliation.json',new/'dataset.json',new/'examples.jsonl.gz',old/'examples.jsonl.gz',Path('logs/roadmap/addon-target-fixture-01/verification.json')]
v=dict(status='verified_relocated_human_addon_labels',old_labels_preserved=836,new_labels=839,added=checks,unsupported_flags_still_excluded=True,training=False,rl=False,bindings={str(p):sha(p) for p in paths},limitations=['Three regular-flag point commands only; five flagged addon commands and grouped-start attribution remain unresolved.','Command identity is verified; no exact paid/start attribution or native-policy competence claimed.'])
(OUT/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
