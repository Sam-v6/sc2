"""Independently recover one missing neutral target without inventing current visibility."""
from pathlib import Path
import gzip,hashlib,json,mpyq
import numpy as np
from src.learning.tournament_record import decode_record
from src.learning.replay_extract import load_protocol,replay_metadata
OUT=Path('logs/roadmap/human-refinery-snapshot-reimport-01');new=OUT/'corpus/870';old=Path('logs/roadmap/human-research-reimport-02/corpus/870');receipt=json.loads((new/'dataset.json').read_text());assert receipt['status']=='completed' and not receipt['disable_fog']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for mapping in [receipt['source_bindings'],receipt['code_bindings'],{str(new/n):h for n,h in receipt['corpus_bindings'].items()}]:
 for p,h in mapping.items():assert sha(p)==h,p
with gzip.open(old/'examples.jsonl.gz','rt') as f:before={(r['action_loop'],r['source_sequence']):r for r in map(json.loads,f)}
with gzip.open(new/'examples.jsonl.gz','rt') as f:after={(r['action_loop'],r['source_sequence']):r for r in map(json.loads,f)}
assert len(before)==850 and len(after)==851 and set(before)<=set(after)
for key,a in before.items():
 b=after[key];assert a['commands']==b['commands'] and a['original_command']==b['original_command'] and a.get('label_translation')==b.get('label_translation')
 for field in ['player','map','units','owned_memory','memory','unknown_fields']:assert a['observation'].get(field)==b['observation'].get(field),(key,field)
added=set(after)-set(before);assert added=={(13280,1382)};row=after[13280,1382];proof=row['label_translation'];cmd=row['original_command'];root=Path('logs/roadmap/pro-preconverted-probe-01');raw=next(e for e in json.loads((root/'raw-commands-870.json').read_text()) if e['_gameloop']==13280);assert proof['source_event']==raw and raw['m_data']['TargetUnit']['m_tag']==0 and raw['m_cmdFlags']==256
point=[raw['m_data']['TargetUnit']['m_snapshotPoint'][axis]/4096 for axis in ['x','y']];assert point==[113.5,53.5]
record=decode_record((root/'fall-record-870.bin').read_bytes());frame=int(np.searchsorted(record['steps']['game_loop'],13280));assert int(record['steps']['game_loop'][frame])==13280;wire=record['actions'][frame];assert len(wire)==1 and wire[0]['ability']==320 and wire[0]['target_type']==1 and wire[0]['target_unit']==cmd['target_unit'] and list(wire[0]['units'])==cmd['units']
n=record['neutral']['fields'];indices=np.flatnonzero(record['neutral']['step']==frame);near=[int(i) for i in indices if n['pos'][i][:2].tolist()==point];assert len(near)==1;i=near[0];assert int(n['id'][i])==cmd['target_unit'] and int(n['unitType'][i])==343 and int(n['observation'][i])==2
assert proof['resource']['position']==point and proof['resource']['tag']==cmd['target_unit'] and proof['resource']['display_type']==2 and not proof['target_observed'] and proof['target_requires_representation_check'] and proof['snapshot_type_link']=='uninterpreted'
assert not any(u['tag']==cmd['target_unit'] for u in row['observation']['units']) and 'label_translation' not in row['observation']
actor=next(u for u in row['observation']['units'] if u['tag']==cmd['units'][0]);assert actor['alliance']==1 and actor['unit_type']==45
replay=root/'2cda222081e80d9a1c188698ce9bcda6.SC2Replay';meta,_=replay_metadata(replay);archive=mpyq.MPQArchive(str(replay));events=list(load_protocol(int(meta['BaseBuild'].removeprefix('Base'))).decode_replay_tracker_events(archive.read_file('replay.tracker.events')));map_resources=[e for e in events if e['_gameloop']==0 and e['_event'].endswith('SUnitBornEvent') and e['m_upkeepPlayerId']==0 and [e['m_x'],e['m_y']]==[113,53]];assert len(map_resources)==1 and map_resources[0]['m_unitTypeName']==b'SpacePlatformGeyser';assert proof['map_resource']==dict(map_resources[0],m_unitTypeName='SpacePlatformGeyser')
g=json.loads((OUT/'reconciliation.json').read_text())['games'][0];selection=next(s['tags'] for s in g['selections'] if s['loop']==13280 and s['sequence']==1382);assert cmd['units'][0] & 0xFFFFFFFF in selection
paths=[Path(__file__),OUT/'reconciliation.json',new/'dataset.json',new/'examples.jsonl.gz',old/'examples.jsonl.gz']
v=dict(status='verified_snapshot_refinery_source_label',old_labels_preserved=850,new_labels=851,loop=13280,target=cmd['target_unit'],target_currently_available=False,observation_unchanged=True,training=False,rl=False,bindings={str(p):sha(p) for p in paths},limitations=['Snapshot geometry recovers label only; target remains unavailable to the current raw-command input representation.','No invented visibility, resource contents, enemy knowledge, payment or completion attribution.'])
(OUT/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
