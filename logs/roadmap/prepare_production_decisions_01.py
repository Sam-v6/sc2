"""Build act/wait examples from real converted observations; no fitting or RL."""
import base64,gzip,hashlib,json,mpyq,threading
from pathlib import Path
from collections import Counter,defaultdict
import psutil
from src.learning.entity_train import validate_datasets
from src.learning.gameplay import PlayerView
from src.learning.production_decisions import decision_windows
from src.learning.replay_extract import replay_metadata,load_protocol
from src.learning.tournament_record import decode_record
from src.learning.tournament_observation import partial_observation
from src.learning.tournament_tracker import CausalTracker
from src.learning.tournament_import import verify_owned_identity
ROOT=Path('logs/roadmap/human-command-cohort-02');OUT=Path('logs/roadmap/production-decisions-01')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 OUT.mkdir(exist_ok=False);manifest=json.loads((ROOT/'manifest.json').read_text());verification=json.loads((ROOT/'verification.json').read_text())
 assert verification['status']=='verified_existing_command_cohort_expansion'
 for p,h in verification['bindings'].items():assert sha(p)==h,p
 validate_datasets([ROOT/g['game']/'corpus' for g in manifest['games'] if g['role']=='teaching'],[ROOT/g['game']/'corpus' for g in manifest['games'] if g['role']=='diagnostic'],missing_fields=True)
 code=[Path(__file__),*[Path('src/learning')/(n+'.py') for n in ('production_decisions','tournament_record','tournament_observation','tournament_tracker','tournament_import','gameplay')]];bindings={str(p):sha(p) for p in code+[ROOT/'manifest.json',ROOT/'verification.json']};games=[];samples=[];stop=threading.Event();done=threading.Event()
 def watch():
  while not done.is_set():
   cpu=psutil.cpu_percent(interval=1);samples.append(cpu)
   if cpu>80:stop.set()
   done.wait(1)
 thread=threading.Thread(target=watch,daemon=True);thread.start()
 try:
  for game in manifest['games']:
   assert not stop.is_set(),'CPU guard'
   parent=ROOT/game['game'];job=json.loads((parent/'job.json').read_text());receipt=json.loads((parent/'corpus/dataset.json').read_text())
   for p,h in receipt['source_bindings'].items():assert sha(p)==h,p
   for p,h in receipt['corpus_bindings'].items():assert sha(parent/'corpus'/p)==h,p
   record=decode_record(Path(job['record']).read_bytes());data=json.loads(Path(job['catalog']).read_text())['game_data'];names={a['ability_id']:a.get('friendly_name','') for a in data['abilities']};rows=list(map(json.loads,gzip.open(parent/'corpus/examples.jsonl.gz','rt')));known={(r['action_loop'],r['source_sequence']) for r in rows};same_loop={}
   for r in rows:same_loop.setdefault(r['action_loop'],r['observation'])
   events=[(r['action_loop'],r['source_sequence'],r['commands'][0]['ability']) for r in rows if names[r['commands'][0]['ability']].startswith(('Build ','Train ','Research ')) or names[r['commands'][0]['ability']] in ('Morph OrbitalCommand','Morph PlanetaryFortress')]
   recon=json.loads((parent/'reconciliation.json').read_text())['games'][0];unknown={(e['event']['_gameloop'],e['event']['m_sequence']) for e in recon['audit']['unresolved_events']}-known
   unknown|={(e['event']['_gameloop'],e['event']['m_sequence']) for e in json.loads((parent/'unknown.json').read_text())}-known
   windows=decision_windows(record['steps']['game_loop'],events,unknown);selected={w['observation_index']:w for w in windows}
   meta,_=replay_metadata(job['replay']);protocol=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));tracker_events=list(protocol.decode_replay_tracker_events(mpyq.MPQArchive(job['replay']).read_file('replay.tracker.events')));tracker=CausalTracker(tracker_events,receipt['player']['player_info']['player_id'],data);owners=defaultdict(set)
   for e in tracker_events:
    if e['_event'].endswith(('.SUnitBornEvent','.SUnitInitEvent','.SUnitOwnerChangeEvent')):owners[(e['_gameloop'],(e['m_unitTagIndex']<<18)|e['m_unitTagRecycle'])].add(e['m_upkeepPlayerId'])
   view=PlayerView();size=rows[0]['observation']['map_size'];folder=OUT/game['game'];folder.mkdir();shared=0;counts=Counter();anchor_loops=[]
   with gzip.open(folder/'states.jsonl.gz','xt') as out:
    for step,rawloop in enumerate(record['steps']['game_loop']):
     loop=int(rawloop);dead=tracker.advance(loop);deaths=[tag for tag in view.owned if tag & 0xffffffff in dead]
     state=partial_observation(record,step,size,view,sorted(tracker.upgrades),deaths)
     if tracker.unmapped_upgrades:state['unknown_fields']['world'].append('upgrade_absence');state['unmapped_own_upgrades']=sorted(tracker.unmapped_upgrades)
     for u in state['units']:
      if u['alliance']==1:verify_owned_identity(tracker,u['tag'] & 0xffffffff,loop,owners)
     for source,target in (('pathable','pathing_grid'),('buildable','placement_grid')):
      grid=record['images'][source][step];state['map'][target]=dict(width=grid.shape[1],height=grid.shape[0],bits_per_pixel=8,data=base64.b64encode(grid.astype('uint8').tobytes()).decode(),coordinate_system='feature_minimap',world_size=size,transform='world_y_flip_then_uniform_max_dimension_scale')
     if step not in selected:continue
     prior=same_loop.get(loop)
     if prior:
      for field in ('player','units','map','map_size','memory','owned_memory','upgrades','effects'):assert state[field]==prior[field],(game['game'],loop,field)
      shared+=1
     assert state['recent_commands']==[]
     target=selected[step];out.write(json.dumps(dict(observation=state,label=target))+'\n');counts[str(target['act'])]+=1;anchor_loops.append(loop)
   (folder/'windows.json').write_text(json.dumps(dict(windows=windows,production_events=events,unknown_keys=sorted(unknown),source_loops=list(map(int,record['steps']['game_loop']))))+'\n')
   for p in [parent/'corpus/dataset.json',parent/'corpus/examples.jsonl.gz',parent/'job.json',parent/'reconciliation.json',parent/'unknown.json',Path(job['record']),Path(job['replay']),Path(job['catalog']),folder/'states.jsonl.gz',folder/'windows.json']:bindings[str(p)]=sha(p)
   item=dict(game=game['game'],role=game['role'],human_result_code=game['human_result_code'],source_observations=len(record['steps']['game_loop']),anchors=len(windows),counts=dict(counts),shared_verified_command_states=shared,maximum_actual_gap=max((b-a for a,b in zip(anchor_loops,anchor_loops[1:])),default=0));games.append(item);print(json.dumps(item),flush=True)
 finally:done.set();thread.join(3)
 assert all(sha(p)==h for p,h in bindings.items())
 report=dict(status='completed_actual_observation_preparation',games=games,bindings=bindings,peak_cpu=max(samples,default=0),training=False,rl=False,decision_loops=44,limits=['Actual observations at least44loops apart; source gaps remain explicit and are not interpolated.','Labels are first issued production events, not completed production.','Timing inputs contain no human action history or future arguments.','Unknown intervals and unsupported source-end waits are censored; losses retained; diagnostics reused; reserved untouched.'])
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 for p in code:
  dest=OUT/'source-snapshot'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 print(json.dumps(dict(status=report['status'],peak_cpu=report['peak_cpu'])),flush=True)
if __name__=='__main__':main()
