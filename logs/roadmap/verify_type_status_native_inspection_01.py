"""Read-only reconstruction of both frozen native opening traces."""
import collections
import gzip
import hashlib
import json
from pathlib import Path
import torch
from google.protobuf.json_format import ParseDict
from s2clientprotocol import query_pb2
from src.learning.actor_selection import construction_products
from src.learning.entity_execution import JointCommandAgent, command_available
from src.learning.entity_play import load_policy

ROOT=Path('logs/roadmap/type-status-native-inspection-01')
def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
torch.set_num_threads(2)
torch.set_num_interop_threads(2)
telemetry=read(ROOT/'telemetry.json')
assert telemetry['status']=='completed' and telemetry['stop_reason'] is None
for p,h in telemetry['code_bindings'].items(): assert sha(p)==h
assert sha('docs/superpowers/plans/2026-10-06-type-status-native-inspection.md')==telemetry['plan_sha256']
comparison=read('logs/roadmap/type-status-imitation-01/comparison.json')
result=dict(status='verified_frozen_native_openings',training=False,arms={},bindings={})
for arm in ('baseline','type_status'):
 directory=ROOT/arm
 episode=read(directory/'episode.json')
 assert episode['status']=='truncated' and episode['training'] is False
 assert 180 <= episode['game_seconds'] < 182
 assert episode['policy_sha256']==sha(episode['policy'])==comparison['arm_bindings'][arm]['policy.npz']
 policy,_=load_policy(episode['policy'],'goal-first')
 static=read(directory/'static.json')
 data=static['game_data']
 vocab=tuple(max(r[k] for r in data[n])+1 for n,k in [('units','unit_id'),('abilities','ability_id'),('upgrades','upgrade_id')])
 assert vocab==policy.engine_vocabulary
 agent=JointCommandAgent(policy,vocab,construction_products(data),static['terrain'])
 catalog={a['ability_id']:a for a in data['abilities']}
 rows=[json.loads(line) for line in gzip.open(directory/'trace.jsonl.gz','rt')]
 abilities=collections.Counter(); actors=collections.Counter(); targets=collections.Counter(); responses=collections.Counter(); counts=collections.defaultdict(list)
 worker_tags=set(); types={u['unit_id']:u.get('name',str(u['unit_id'])) for u in data['units']}
 for row in rows:
  state=row['observation']
  assert state['recent_commands']==agent.history
  command,delay=agent.decide(state)
  assert command.as_dict()==row['command'] and delay==row['delay']
  response=ParseDict(dict(abilities=row['available']),query_pb2.ResponseQuery())
  assert command_available(command,response,catalog)==row['issued']
  if row['issued']: agent.record_issued(command,state,delay)
  responses.update(map(str,row['results']))
  abilities[catalog.get(command.ability,{}).get('friendly_name',str(command.ability))]+=1
  units={u['tag']:u for u in state['units']}
  actors.update(types[units[tag]['unit_type']] for tag in command.units)
  if command.target_unit: targets.update([types[units[command.target_unit]['unit_type']]])
  own=[u for u in state['units'] if u['alliance']==1]
  worker_tags.update(u['tag'] for u in own if u['unit_type']==45)
  for kind in (45,19,21): counts[types[kind]].append(sum(u['unit_type']==kind for u in own))
 assert len(rows)==episode['decisions']
 assert sum(r['issued'] for r in rows)==episode['commands']
 assert responses==collections.Counter(episode['action_results'])
 initial={u['tag'] for u in rows[0]['observation']['units'] if u['alliance']==1 and u['unit_type']==45}
 result['arms'][arm]=dict(decisions=len(rows),abilities=dict(abilities),actor_types=dict(actors),target_types=dict(targets),observed_counts={k:dict(min=min(v),max=max(v)) for k,v in counts.items()},new_observed_worker_tags=len(worker_tags-initial),final_player=episode['final_player'],action_results=dict(responses),peak_whole_cpu_percent=max(s['whole_cpu_percent'] for s in telemetry['arms'][arm]['samples']))
 for p in directory.iterdir(): result['bindings'][str(p)]=sha(p)
 result['bindings'][episode['policy']]=sha(episode['policy'])
result['bindings'][str(ROOT/'telemetry.json')]=sha(ROOT/'telemetry.json')
result['bindings'][__file__]=sha(__file__)
assert all(sha(p)==h for p,h in result['bindings'].items())
(ROOT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result['arms'],indent=2))
