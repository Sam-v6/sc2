"""Inspect original addon target fields without accepting unknown flags."""
from pathlib import Path
import hashlib,json,math,mpyq
import numpy as np
from src.learning.tournament_record import decode_record
from src.learning.replay_extract import load_protocol,replay_metadata
ROOT=Path('logs/roadmap/pro-preconverted-probe-01');OUT=Path('logs/roadmap/human-addon-targets-01');OUT.mkdir(exist_ok=True)
record_path=ROOT/'fall-record-870.bin';record=decode_record(record_path.read_bytes());u=record['units']['fields'];loops=record['steps']['game_loop'];reconcile_path=Path('logs/roadmap/human-lift-land-reimport-02/reconciliation.json');g=json.loads(reconcile_path.read_text())['games'][0];names={(x['link'],x['index']):x['name'] for x in g['verified_candidate_names']};selected={(x['loop'],x['sequence']):x['tags'] for x in g['selections']};raw_path=ROOT/'raw-commands-870.json';raw=json.loads(raw_path.read_text());cat_path=Path('logs/roadmap/joint-frozen-native-wait-02/static.json');cat=json.loads(cat_path.read_text())['game_data'];units={x['unit_id']:x['name'] for x in cat['units']}
replay=ROOT/'2cda222081e80d9a1c188698ce9bcda6.SC2Replay';meta,_=replay_metadata(replay);proto=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));archive=mpyq.MPQArchive(str(replay));tracker=list(proto.decode_replay_tracker_events(archive.read_file('replay.tracker.events')));starts=[e for e in tracker if e['_event'].endswith(('SUnitInitEvent','SUnitBornEvent')) and e['m_upkeepPlayerId']==1 and any(w in e['m_unitTypeName'].decode() for w in ['TechLab','Reactor'])]
entries=[]
for e in raw:
 abil=e['m_abil'];name=names.get((abil['m_abilLink'],abil['m_abilCmdIndex']),'') if abil else ''
 if not any(w in name for w in ['TechLab','Reactor']):continue
 loop=e['_gameloop'];index=int(np.searchsorted(loops,loop));frame=int(loops[index]);actions=record['actions'][index] if frame==loop else [];candidates=[a for a in actions if a['ability'] in [3682,3683]];actors=[]
 for a in candidates:
  for tag in a['units']:
   ix=np.flatnonzero((record['units']['step']==index)&(u['id']==tag)&(u['alliance']==1));assert len(ix)==1;i=int(ix[0]);actors.append(dict(tag=tag,type=units[int(u['unitType'][i])],position=u['pos'][i][:2].tolist(),flying=bool(u['is_flying'][i]),selected=tag & 0xFFFFFFFF in (selected.get((loop,e['m_sequence'])) or [])))
 point=[e['m_data']['TargetPoint'][axis]/4096 for axis in ['x','y']] if 'TargetPoint' in e['m_data'] else None
 nearby=[dict(loop=t['_gameloop'],type=t['m_unitTypeName'].decode(),point=[t['m_x'],t['m_y']]) for t in starts if loop<=t['_gameloop']<=loop+224]
 entries.append(dict(loop=loop,sequence=e['m_sequence'],raw_name=name,flags=hex(e['m_cmdFlags']),raw_point=point,frame_loop=frame,converted=candidates,actors=actors,distance_to_actor=[math.dist(point,a['position']) for a in actors] if point else [],nearby_addon_starts=nearby))
paths=[Path(__file__),record_path,reconcile_path,raw_path,cat_path,replay,Path('src/learning/tournament_record.py')]
report=dict(status='descriptive_addon_target_audit',entries=entries,training=False,rl=False,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},limitations=['Temporal proximity of tracker start is descriptive, not command attribution.','Unknown flags and point/no-target differences remain excluded from accepted labels.'])
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
for row in entries: print(json.dumps(row),flush=True)
