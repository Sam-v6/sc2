"""Brute-force timing labels and direct chronological source-state verification."""
import base64,gzip,hashlib,json,math,struct,mpyq
from pathlib import Path
from collections import Counter,defaultdict
from src.learning.tournament_record import decode_record
from src.learning.replay_extract import replay_metadata,load_protocol
OUT=Path('logs/roadmap/production-decisions-01');ROOT=Path('logs/roadmap/human-command-cohort-02')
report=json.loads((OUT/'report.json').read_text());assert report['status']=='completed_actual_observation_preparation' and report['peak_cpu']<=80
for p,h in report['bindings'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
results=[]
for game in report['games']:
 folder=OUT/game['game'];contract=json.loads((folder/'windows.json').read_text());rows=list(map(json.loads,gzip.open(folder/'states.jsonl.gz','rt')));loops=contract['source_loops'];events=contract['production_events'];unknown=set(map(tuple,contract['unknown_keys']));expected=[];previous=None
 for index,loop in enumerate(loops):
  if previous is not None and loop-previous<44:continue
  previous=loop;possible=[e for e in events if loop<=e[0]<loop+44];event=possible[0] if possible else None
  barrier=tuple(event[:2]) if event else (loop+44,-1)
  reason='unknown_event' if any((loop,-1)<=key<barrier for key in unknown) else 'source_end' if event is None and loop+44>loops[-1] else None
  expected.append(dict(loop=loop,observation_index=index,act=None if reason else bool(event),ability=event[2] if event and not reason else None,target_key=event[:2] if event and not reason else None,censored=reason))
 assert expected==contract['windows']==[r['label'] for r in rows]
 assert len({tuple(r['label']['target_key']) for r in rows if r['label']['act']})==sum(r['label']['act'] is True for r in rows),'Nonoverlapping anchors must not duplicate future event identities'
 job=json.loads((ROOT/game['game']/'job.json').read_text());record=decode_record(Path(job['record']).read_bytes());assert list(map(int,record['steps']['game_loop']))==loops
 indices=defaultdict(list);fields=record['units']['fields']
 for i,step in enumerate(record['units']['step']):indices[int(step)].append(i)
 nindices=defaultdict(list);nf=record['neutral']['fields']
 for i,step in enumerate(record['neutral']['step']):nindices[int(step)].append(i)
 meta,_=replay_metadata(job['replay']);proto=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));tracker=list(proto.decode_replay_tracker_events(mpyq.MPQArchive(job['replay']).read_file('replay.tracker.events')))
 deaths=[(e['_gameloop'],(e['m_unitTagIndex']<<18)|e['m_unitTagRecycle']) for e in tracker if e['_event'].endswith('.SUnitDiedEvent')];death_index=0
 selected={r['label']['observation_index']:r for r in rows};enemy_memory={};own_memory={};checked=0
 for step,loop in enumerate(loops):
  grid=record['images']['visibility'][step];height,width=grid.shape;size=rows[0]['observation']['map_size'];scale=width/max(size);current={};visible_enemies=set()
  for i in indices[step]:
   if fields['is_blip'][i] or fields['observation'][i]==3:continue
   tag=int(fields['id'][i]);kind=int(fields['unitType'][i]);alliance=int(fields['alliance'][i]);display=int(fields['observation'][i]);pos=list(map(float,fields['pos'][i]));visible=display==1
   if alliance==4:
    x=math.floor(pos[0]*scale);y=math.floor((size[1]-pos[1])*scale);visible=visible and 0<=x<width and 0<=y<height and grid[y,x]==2
    if visible:enemy_memory[tag]=dict(tag=tag,unit_type=kind,position=pos,last_seen_loop=loop);visible_enemies.add(tag)
    elif display==2 and tag not in enemy_memory:enemy_memory[tag]=dict(tag=tag,unit_type=kind,position=pos,last_seen_loop=None)
   if not visible:continue
   if alliance==1:own_memory[tag]=dict(tag=tag,unit_type=kind,alliance=1,position=pos,last_seen_loop=loop,observed=False)
   current[tag]=dict(unit_type=kind,alliance=alliance,position=pos,health=float(fields['health'][i]))
  for i in nindices[step]:
   if nf['observation'][i]!=1:continue
   current[int(nf['id'][i])]=dict(unit_type=int(nf['unitType'][i]),alliance=3,position=list(map(float,nf['pos'][i])),health=float(nf['health'][i]))
  while death_index<len(deaths) and deaths[death_index][0]<loop:
   low=deaths[death_index][1]
   for tag in list(own_memory):
    if tag & 0xffffffff==low:own_memory.pop(tag)
   death_index+=1
  if step not in selected:continue
  st=selected[step]['observation'];assert st['game_loop']==loop and st['recent_commands']==[]
  assert not any(k in st for k in ('label','target_key','future_command','future_actor','source_repeat_provenance'))
  actual={u['tag']:u for u in st['units']};assert set(actual)==set(current),(game['game'],loop,'current source identities')
  for tag,u in current.items():
   assert all(actual[tag][f]==v for f,v in u.items() if f!='health')
   assert struct.pack('<f',actual[tag].get('health',0))==struct.pack('<f',u['health'])
  assert st['memory']==[v for tag,v in sorted(enemy_memory.items()) if tag not in visible_enemies]
  assert st['owned_memory']==[v for tag,v in sorted(own_memory.items()) if tag not in current],(game['game'],loop,st['owned_memory'],[v for tag,v in sorted(own_memory.items()) if tag not in current])
  for name,source in [('visibility','visibility'),('pathing_grid','pathable'),('placement_grid','buildable')]:
   image=st['map'][name];assert base64.b64decode(image['data'])==record['images'][source][step].astype('uint8').tobytes()
  for source,target in [('minerals','minerals'),('gas','vespene'),('cap','food_cap'),('army','food_army'),('workers','food_workers')]:assert st['player'].get(target,0)==int(record['steps'][source][step])
  checked+=1
 assert checked==len(rows)
 result=dict(game=game['game'],role=game['role'],checked_actual_states=checked,counts=dict(Counter(str(r['label']['act']) for r in rows)),maximum_actual_gap=game['maximum_actual_gap']);results.append(result);print(json.dumps(result),flush=True)
paths=[Path(__file__),OUT/'report.json']
result=dict(status='verified_causal_actual_observation_windows',games=results,training=False,rl=False,peak_preparation_cpu=report['peak_cpu'],bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},limits=['Sparse actual observation cadence and selectively censored timing labels are explicit; no uniform native observation stream is reconstructed.','Labels supervise first issued production requests, not successful production.','Diagnostics reused; reserved games untouched; no model fit.'])
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes())
