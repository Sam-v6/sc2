import pathlib,json,time,hashlib
from src.learning.tournament_record import decode_record
from src.learning.tournament_observation import partial_observation
from src.learning.gameplay import PlayerView
P=pathlib.Path(__file__).parent
upgrades=json.loads((P/'own-upgrade-recovery-audit-01.json').read_text());out=[]
for idx,size in ((294,(200,184)),(774,(200,184)),(870,(176,184))):
 f=P/f'fall-record-{idx}.bin';record=decode_record(f.read_bytes());view=PlayerView();start=time.perf_counter();visible=memory=0;known=[u for g in upgrades['games'] if g['idx']==idx for u in g['own_upgrade_events'] if u['native_id'] is not None]
 for i,loop in enumerate(record['steps']['game_loop']):
  ids=sorted({u['native_id'] for u in known if u['loop']<=loop});state=partial_observation(record,i,size,view,ids)
  assert state['upgrades']==ids and state['unknown_fields']
  assert all(u['display_type']==1 and not u.get('is_blip') and 'energy' not in u for u in state['units'])
  assert all(set(m)<={'tag','unit_type','position','last_seen_loop'} for m in state['memory'])
  assert 'food_used' not in state['player'] and 'energy' in state['unknown_fields']['units']
  assert state['map_size']==list(size)
  visible+=len(state['units']);memory+=len(state['memory'])
 out.append({'idx':idx,'record_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'observations_projected':len(record['steps']['game_loop']),'visible_unit_rows':visible,'memory_rows':memory,'seconds':time.perf_counter()-start,'training_eligible':False});print(out[-1],flush=True)
 del record
code=[pathlib.Path('src/learning/tournament_observation.py'),pathlib.Path('src/learning/entity_examples.py'),pathlib.Path('src/learning/gameplay.py'),P/'own-upgrade-recovery-audit-01.json',P/'historical-observer-implementation-binding.json',pathlib.Path(__file__)]
receipt={'bindings':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in code},'records':out,'energy':'Current energy omitted: confirmed upstream capacity-copy bug','training_eligible':False}
(P/'partial-observation-verification-02.json').write_text(json.dumps(receipt,indent=2)+'\n')
