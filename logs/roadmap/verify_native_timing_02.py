"""Independent native issuance proofs, interval labels and observation accounting."""
import base64,gzip,hashlib,json
from pathlib import Path
import mpyq,sc2reader
ROOT=Path('logs/roadmap/dense-timing-cohort-01');OUT=Path('logs/roadmap/native-production-timing-02')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return list(map(json.loads,gzip.open(p,'rt')))
def norm(s):return s.replace(' ','').lower()
def main():
 from src.learning.replay_extract import load_protocol
 report=json.loads((OUT/'report.json').read_text());manifest=json.loads((ROOT/'manifest.json').read_text())
 for p,h in report['bindings'].items():assert sha(p)==h,p
 checks=[]
 for g in manifest['games']:
  parent=Path(g['output']);folder=OUT/g['game'];receipt=json.loads((parent/'dataset.json').read_text());assert receipt['status']=='completed' and not receipt['disable_fog'];assert receipt['last_loop']+1==receipt['counts']['observations']
  raw=read(parent/'examples.jsonl.gz');states=read(parent/'observations.jsonl.gz');examples=read(folder/'examples.jsonl.gz');events=json.loads((folder/'events.json').read_text());bykey={tuple(e['key']):e for e in events}
  assert len(bykey)==len(events);assert len(states)==len(examples)==receipt['recorded_observations'];assert [s['game_loop'] for s in states]==list(range(0,receipt['last_loop']+1,44))
  data=json.loads((parent/'static.json').read_text())['game_data'];cat={a['ability_id']:a for a in data['abilities']};reader=sc2reader.load_replay(g['replay'],load_level=2,load_map=False)
  archive=mpyq.MPQArchive(g['replay']);protocol=load_protocol(75689);init=protocol.decode_replay_initdata(archive.read_file('replay.initData'));user=next(s['m_userId'] for s in init['m_syncLobbyState']['m_lobbyState']['m_slots'] if s['m_workingSetSlotId']==g['player']-1 and s['m_userId'] is not None)
  original={(e['_gameloop'],e['m_sequence']):e for e in protocol.decode_replay_game_events(archive.read_file('replay.game.events')) if e['_event'].endswith('.SCmdEvent') and e['_userid']['m_userId']==user};assert set(original)==set(bykey)
  used=set()
  for key,item in bykey.items():
   event=original[key];assert event==item['event']
   if item['proof']!='unique_native_target_queue_ability_own_actor':continue
   position=tuple(item['native_position']);assert position not in used;used.add(position);row=raw[position[0]];command=row['commands'][position[1]];assert row['action_loop']==key[0] and command['ability']==item['ability'];assert set(command['units'])<={u['tag'] for u in row['observation']['units'] if u['alliance']==1}
   flags=event['m_cmdFlags'];assert flags & 0x100 and not flags & ~(0x100|2|8|0x10000|0x20000);assert command['queue']==bool(flags & 2)
   target=event['m_data']
   if 'None' in target:assert command['target_point'] is None and command['target_unit'] is None
   elif 'TargetUnit' in target:assert command['target_unit'] & 0xffffffff==target['TargetUnit']['m_tag']
   else:assert all(abs(command['target_point'][i]-target['TargetPoint'][axis]/4096)<1e-5 for i,axis in enumerate(('x','y')))
   native=cat[item['ability']];ability=event['m_abil']
   if ability is None:assert item['ability']==1 and native['friendly_name']=='Smart';continue
   meta=reader.datapack.abilities[(ability['m_abilLink']<<5)|ability['m_abilCmdIndex']];name=meta.name
   if meta.build_unit:
    kind='VikingFighter' if meta.build_unit.name=='Viking' else meta.build_unit.name
    units=[u for u in data['units'] if u.get('name')==kind and 'ability_id' in u]
    if len(units)==1 and cat[units[0]['ability_id']].get('link_index')==ability['m_abilCmdIndex']:name=cat[units[0]['ability_id']]['friendly_name']
   upgrade_name = name.removeprefix('Research').replace(' ', '') if name.startswith('Research') else 'TerranVehicleWeaponsLevel' + name[-1] if name in ('UpgradeVehicleWeapons1','UpgradeVehicleWeapons2','UpgradeVehicleWeapons3') else None
   upgrades=[u for u in data['upgrades'] if u['name']==upgrade_name and 'ability_id' in u]
   if len(upgrades)==1:
    referenced=cat[upgrades[0]['ability_id']]
    if referenced.get('link_index')==ability['m_abilCmdIndex']:name=referenced['friendly_name']
   if norm(name)==norm(native['friendly_name']):assert native['link_index']==ability['m_abilCmdIndex'];continue
   # Independent catalogue proof for basic/effect aliases; production aliases
   # must retain the existing strict producer/upgrade reconciliation instead.
   nonproduction=not native['friendly_name'].startswith(('Build ','Train ','Research ','Morph '))
   alias=norm(name)==norm(native.get('button_name','')) or (name in ('Attack','Move','Stop','HoldPosition','Patrol') and native['friendly_name'].split(' ')[0]==name)
   if nonproduction and alias:assert native['link_index']==ability['m_abilCmdIndex'];continue
   from src.learning.tournament_commands import ability_matches
   types={u['tag']:next(t['name'] for t in data['units'] if t['unit_id']==u['unit_type']) for u in row['observation']['units'] if u['alliance']==1}
   assert ability_matches(dict(ability=item['ability'],tags=command['units']),event,cat,{(ability['m_abilLink'],ability['m_abilCmdIndex']):name},types),key
  for key,item in bykey.items():
   if item['proof'] not in ('verified_numeric_nonproduction_identity','regular_user_numeric_production_identity'):continue
   for ref in item['reference_keys']:
    reference=bykey[tuple(ref)];assert reference['proof']=='unique_native_target_queue_ability_own_actor'
    assert original[key]['m_abil']==reference['event']['m_abil'] or all(original[key]['m_abil'][k]==reference['event']['m_abil'][k] for k in ('m_abilLink','m_abilCmdIndex'))
    assert reference['classification']==item['classification']
  counts={};covered=set()
  for state,example in zip(states,examples,strict=True):
   assert example['observation']==dict(state,recent_commands=[]);loop=state['game_loop'];label=example['label'];assert label['loop']==loop
   positive=[list(k) for k,e in bykey.items() if loop<k[0]<=loop+44 and e['classification']=='production'];unknown=[list(k) for k,e in bykey.items() if loop<k[0]<=loop+44 and e['classification']=='unknown']
   act=True if positive else None if unknown or loop+44>receipt['last_loop'] else False
   assert label==dict(loop=loop,act=act,production_keys=positive,unknown_keys=unknown)
   counts[str(act)]=counts.get(str(act),0)+1
   if loop+44<=receipt['last_loop']:covered.update(range(loop,loop+44))
   for u in state['units']:
    if u['alliance']!=4:continue
    grid=state['map']['visibility'];x,y=map(round,u['position'][:2]);assert grid['bits_per_pixel']==8 and base64.b64decode(grid['data'])[y*grid['width']+x]==2
  checks.append(dict(game=g['game'],role=g['role'],counts=counts,verified_native_proofs=len(used),covered_elapsed_loops=len(covered),total_elapsed_loops=receipt['last_loop']))
 for p,h in report['bindings'].items():assert sha(p)==h,p
 bindings={str(p):sha(p) for p in [Path(__file__),OUT/'report.json',ROOT/'manifest.json']}
 (OUT/'verification.json').write_text(json.dumps(dict(status='verified_native_issuance_proofs_and_current_timing_labels',games=checks,bindings=bindings),indent=2)+'\n')
 snapshot=OUT/'source-snapshot';snapshot.mkdir()
 for p in (Path(__file__),Path('logs/roadmap/prepare_native_timing_02.py'),Path('src/learning/production_gate.py'),Path('src/learning/native_ability_identity.py')):
  dest=snapshot/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 print(json.dumps(checks),flush=True)
if __name__=='__main__':main()
