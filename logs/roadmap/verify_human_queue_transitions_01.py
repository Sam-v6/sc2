"""Independently reconstruct queue counts and original tracker addon starts."""
from pathlib import Path
from collections import Counter
import json,hashlib,gzip
import mpyq
import numpy as np
from src.learning.tournament_record import decode_record
from src.learning.replay_extract import load_protocol,replay_metadata
ROOT=Path('logs/roadmap/human-queue-transitions-01');p=ROOT/'audit.json';a=json.loads(p.read_text())
for path,digest in a['bindings'].items(): assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
r=decode_record(Path('logs/roadmap/pro-preconverted-probe-01/fall-record-870.bin').read_bytes());u=r['units']['fields'];steps=r['units']['step'];loops=r['steps']['game_loop']
c=Path('logs/roadmap/human-visibility-reimport-01/corpus/870');catalog={x['ability_id']:x for x in json.loads((c/'static.json').read_text())['game_data']['abilities']}
with gzip.open(c/'examples.jsonl.gz','rt') as f:rows={(x['action_loop'],x['source_sequence']):x for x in map(json.loads,f)}
counts=Counter()
for e in a['entries']:
 row=rows[e['loop'],e['sequence']];assert row['original_command']==e['command'] and e['actor'] in e['command']['units']
 index=int(np.searchsorted(loops,e['loop'])); assert int(loops[index+1])==e['next_loop']
 queues=[]
 for frame in [index,index+1]:
  ix=np.flatnonzero((steps==frame)&(u['id']==e['actor'])&(u['alliance']==1));assert len(ix)==1
  queues.append([dict(ability=int(u[f'order{k}']['ability'][ix[0]]),progress=float(u[f'order{k}']['progress'][ix[0]]),target=int(u[f'order{k}']['target_unit'][ix[0]]),point=[int(u[f'order{k}'][axis][ix[0]]) for axis in ['x','y']]) for k in range(4) if u[f'order{k}']['ability'][ix[0]]])
 assert queues==[e['before'],e['after']]
 wanted=catalog[e['command']['ability']].get('remaps_to_ability_id') or e['command']['ability']
 n=[sum((catalog.get(o['ability'],{}).get('remaps_to_ability_id') or o['ability'])==wanted for o in q) for q in queues]
 assert not e['intervening_sequences'] and not e['unresolved_sequences']
 status='observed_queue_count_increase' if n[1]>n[0] else 'already_present_no_count_increase' if min(n)>0 else 'no_observed_count_increase'
 assert status==e['status'];counts[status]+=1
assert dict(counts)==a['counts'] and len(a['entries'])==224
replay=Path('logs/roadmap/pro-preconverted-probe-01/2cda222081e80d9a1c188698ce9bcda6.SC2Replay');metadata,details=replay_metadata(replay);proto=load_protocol(int(metadata['BaseBuild'].removeprefix('Base')));archive=mpyq.MPQArchive(str(replay));starts=[]
for event in proto.decode_replay_tracker_events(archive.read_file('replay.tracker.events')):
 if event['_event'].endswith(('SUnitBornEvent','SUnitInitEvent')) and event['m_upkeepPlayerId']==1:
  name=event['m_unitTypeName'].decode()
  if 'TechLab' in name or 'Reactor' in name: starts.append(dict(loop=event['_gameloop'],type=name,tag=(event['m_unitTagIndex']<<18)|event['m_unitTagRecycle'],point=[event['m_x'],event['m_y']]))
assert a['matched_addon_commands']==0 and starts
v=dict(status='verified_descriptive_queue_audit',entries=len(a['entries']),counts=dict(counts),matched_addon_commands=0,tracker_addon_starts=starts,limitations=a['limitations']+['Tracker addon starts prove omitted production exists, not command identity or attachment.'],bindings={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [p,Path(__file__),replay]})
(ROOT/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
