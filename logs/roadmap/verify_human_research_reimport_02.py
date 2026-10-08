"""Independent original-reader/catalogue checks for recovered research and Viking labels."""
from pathlib import Path
from collections import Counter
import base64,gzip,hashlib,json,math,sc2reader
import numpy as np
from src.learning.tournament_record import decode_record
OUT=Path('logs/roadmap/human-research-reimport-02');new=OUT/'corpus/870';old=Path('logs/roadmap/human-in-place-addon-reimport-01/corpus/870');receipt=json.loads((new/'dataset.json').read_text());assert receipt['status']=='completed' and not receipt['disable_fog']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for mapping in [receipt['source_bindings'],receipt['code_bindings'],{str(new/n):h for n,h in receipt['corpus_bindings'].items()}]:
 for p,h in mapping.items():assert sha(p)==h,p
with gzip.open(old/'examples.jsonl.gz','rt') as f:before={(r['action_loop'],r['source_sequence']):r for r in map(json.loads,f)}
with gzip.open(new/'examples.jsonl.gz','rt') as f:after={(r['action_loop'],r['source_sequence']):r for r in map(json.loads,f)}
assert len(before)==842 and len(after)==850 and set(before)<=set(after)
for key,a in before.items():
 b=after[key];assert a['original_command']==b['original_command'] and a['commands']==b['commands'] and a.get('label_translation')==b.get('label_translation')
 for field in ['player','map','units','owned_memory','memory','unknown_fields']:assert a['observation'].get(field)==b['observation'].get(field),(key,field)
root=Path('logs/roadmap/pro-preconverted-probe-01');record=decode_record((root/'fall-record-870.bin').read_bytes());raw={(e['_gameloop'],e['m_sequence']):e for e in json.loads((root/'raw-commands-870.json').read_text())};reader=sc2reader.load_replay(str(root/'2cda222081e80d9a1c188698ce9bcda6.SC2Replay'),load_level=2,load_map=False);data=json.loads((new/'static.json').read_text())['game_data'];abilities={a['ability_id']:a for a in data['abilities']};unit_names={u['unit_id']:u['name'] for u in data['units']};g=json.loads((OUT/'reconciliation.json').read_text())['games'][0];selected={(x['loop'],x['sequence']):x['tags'] for x in g['selections']};added=set(after)-set(before);counts=Counter();checks=[]
for key in sorted(added):
 row=after[key];cmd=row['original_command'];event=raw[key];source=event['m_abil'];index=source['m_abilCmdIndex'];metadata=reader.datapack.abilities[(source['m_abilLink']<<5)|index];ability=cmd['ability'];assert event['m_cmdFlags']==256 and not cmd['queue'] and not cmd['autocast'] and cmd['target_point'] is None and cmd['target_unit'] is None
 if ability==624:
  assert metadata.build_unit.name=='Viking' and metadata.name=='TrainViking' and index==4
  unit=next(u for u in data['units'] if u['name']=='VikingFighter');assert unit['ability_id']==624 and abilities[624]['link_index']==index;parent='Starport'
 elif ability==769:
  assert metadata.name=='ResearchCycloneLockOnDamageUpgrade' and index==9
  upgrade=next(u for u in data['upgrades'] if u['name']=='CycloneLockOnDamageUpgrade');assert upgrade['ability_id']==769 and abilities[769]['link_index']==index;parent='FactoryTechLab'
 elif ability==3701:
  level=index-4;assert level in [1,2,3] and metadata.name=='UpgradeVehicleWeapons'+str(level)
  upgrade=next(u for u in data['upgrades'] if u['name']=='TerranVehicleWeaponsLevel'+str(level));a=abilities[upgrade['ability_id']];assert a['link_index']==index and a['remaps_to_ability_id']==3701;parent='Armory'
 else:
  assert ability==3700;level=index-13;assert level in [1,2,3] and metadata.name=='ResearchTerranVehicleAndShipArmorsLevel'+str(level)
  upgrade=next(u for u in data['upgrades'] if u['name']=='TerranVehicleAndShipArmorsLevel'+str(level));legacy=abilities[upgrade['ability_id']];assert legacy['available'] is False
  candidates=[a for a in data['abilities'] if a.get('friendly_name')==legacy['friendly_name'] and a.get('link_index')==index and a.get('available') is True];assert len(candidates)==1 and candidates[0]['remaps_to_ability_id']==3700;parent='Armory'
 frame=int(np.searchsorted(record['steps']['game_loop'],key[0]));assert int(record['steps']['game_loop'][frame])==key[0];wire=[a for a in record['actions'][frame] if a['ability']==ability and list(a['units'])==cmd['units']];assert len(wire)==1 and wire[0]['target_type']==0
 assert {t & 0xFFFFFFFF for t in cmd['units']}<=set(selected[key])
 for tag in cmd['units']:
  u=record['units']['fields'];ix=np.flatnonzero((record['units']['step']==frame)&(u['id']==tag)&(u['alliance']==1));assert len(ix)==1 and unit_names[int(u['unitType'][ix[0]])]==parent
 st=row['observation'];image=st['map']['visibility'];pixels=base64.b64decode(image['data']);w=image['width'];sx,sy=image['world_size'];scale=w/max(sx,sy)
 for enemy in st['units']:
  if enemy['alliance']!=4:continue
  x,y=enemy['position'][:2];ix,iy=math.floor(x*scale),math.floor((sy-y)*scale);assert 0<=ix<w and 0<=iy<image['height'] and pixels[iy*w+ix]==2
 counts[ability]+=1;checks.append(dict(loop=key[0],ability=ability,index=index,reader_name=metadata.name,parent=parent))
assert counts=={624:1,769:1,3700:3,3701:3}
paths=[Path(__file__),OUT/'reconciliation.json',new/'dataset.json',new/'examples.jsonl.gz',old/'examples.jsonl.gz']
v=dict(status='verified_human_research_and_viking_reimport',old_labels_preserved=842,new_labels=850,checks=checks,training=False,rl=False,bindings={str(p):sha(p) for p in paths},limitations=['Source command identity, not exact payment/completion attribution or policy competence.','Only one teaching game; historical corpora and development games unchanged.'])
(OUT/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
