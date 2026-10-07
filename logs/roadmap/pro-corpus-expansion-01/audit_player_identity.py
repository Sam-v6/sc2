from pathlib import Path
from collections import defaultdict
import hashlib,json,mpyq
from src.learning.replay_extract import load_protocol
from src.learning.tournament_record import decode_record
from src.learning.tournament_import import replay_user_id,verify_owned_identity
from src.learning.tournament_tracker import CausalTracker
P=Path(__file__).parent;source=Path('logs/roadmap/pro-preconverted-probe-01');q=load_protocol(76052);catalog_path=Path('logs/roadmap/joint-frozen-native-wait-02/static.json');catalog=json.loads(catalog_path.read_text())['game_data'];rows=[];bindings={str(catalog_path):hashlib.sha256(catalog_path.read_bytes()).hexdigest()}
for item in json.loads((P/'record-range-plan.json').read_text())['records']:
 replay_path=P/item['raw_name'];record_path=P/f"fall-record-{item['idx']}.bin";a=mpyq.MPQArchive(str(replay_path));details=q.decode_replay_details(a.read_file('replay.details'));init=q.decode_replay_initdata(a.read_file('replay.initData'));player=item['teacher']['pid'];uid=replay_user_id(details,init,player)
 record=decode_record(record_path.read_bytes());u=record['units'];f=u['fields'];indices=[int(i) for i in __import__('numpy').flatnonzero((u['step']==0)&(f['alliance']==1))];tracker_events=list(q.decode_replay_tracker_events(a.read_file('replay.tracker.events')));tracker=CausalTracker(tracker_events,player,catalog);loop=int(record['steps']['game_loop'][0]);tracker.advance(loop);boundary=defaultdict(set);types={};native_names={v['name']:v['unit_id'] for v in catalog['units']}
 for e in tracker_events:
  if e['_gameloop']>loop:continue
  kind=e['_event'].rsplit('.',1)[-1]
  if kind in ('SUnitBornEvent','SUnitInitEvent','SUnitOwnerChangeEvent'):
   tag=(e['m_unitTagIndex']<<18)|e['m_unitTagRecycle'];boundary[(e['_gameloop'],tag)].add(e['m_upkeepPlayerId'])
   if kind!='SUnitOwnerChangeEvent':types[tag]=native_names.get(e['m_unitTypeName'].decode())
 failures=[];matched_types=0
 for i in indices:
  tag=int(f['id'][i])&0xffffffff
  try:verify_owned_identity(tracker,tag,loop,boundary)
  except ValueError as error:failures.append({'tag':tag,'reason':str(error)})
  if types.get(tag)==int(f['unitType'][i]):matched_types+=1
  else:failures.append({'tag':tag,'reason':'initial native unit type differs'})
 row={'idx':item['idx'],'teacher':item['teacher'],'player_id':player,'game_event_user_id':uid,'working_set_slot':details['m_playerList'][player-1]['m_workingSetSlotId'],'initial_self_units':len(indices),'matched_initial_native_types':matched_types,'failures':failures,'initial_identity_consistent':not failures,'split':item['split'],'scope':'Initial identity checks only; original-command reconciliation and full causal importer verification still required','training_eligible':False};rows.append(row);print(item['idx'],uid,matched_types,len(failures),flush=True)
 for path in (replay_path,record_path):bindings[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
for path in (Path(__file__),Path(q.__file__),Path('src/learning/tournament_import.py'),Path('src/learning/tournament_record.py'),Path('src/learning/tournament_tracker.py')):bindings[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
result={'games':rows,'bindings':bindings,'consistent_games':sum(r['initial_identity_consistent'] for r in rows),'excluded_indices':[r['idx'] for r in rows if not r['initial_identity_consistent']],'rl_updates':0};(P/'player-identity-audit-02.json').write_text(json.dumps(result,indent=2)+'\n')
