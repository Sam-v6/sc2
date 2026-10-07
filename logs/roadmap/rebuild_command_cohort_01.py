"""Refresh the existing cohort with conservative source-command repeat recovery."""
import hashlib,json,mpyq,threading
from pathlib import Path
from collections import Counter
import psutil
from src.learning.replay_command_events import command_events
from src.learning.tournament_record import decode_record
from src.learning.tournament_commands import reconcile_commands
from src.learning.tournament_tracker import CausalTracker
from src.learning.replay_extract import load_protocol,replay_metadata
from src.learning.tournament_import import import_game,check_bindings
from src.learning.entity_train import validate_datasets
ROOT=Path('logs/roadmap');OUT=ROOT/'human-command-cohort-01';OUT.mkdir(exist_ok=False)
TRAIN=('294','870','955','839','991','523');HELD=('887','920','851')
config=json.loads((ROOT/'joint-professional-fit-05/configuration.json').read_text());sources={Path(s['dataset']).name:Path(s['dataset']) for s in config['sources'] if s['role']=='teaching'}
assert set(sources)==set(TRAIN+HELD)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
code=[Path(__file__),*[Path('src/learning')/(n+'.py') for n in ('replay_command_events','tournament_record','tournament_commands','tournament_tracker','tournament_import','tournament_observation','tournament_targets','tournament_history','gameplay','entity_train')]]
code_hashes={str(p):sha(p) for p in code};summary=[];cpu=[];done=threading.Event()
def watch():
 while not done.is_set():
  usage=psutil.cpu_percent(interval=1);cpu.append(usage)
  if usage>80:done.set()
  done.wait(1)
thread=threading.Thread(target=watch,daemon=True);thread.start()
try:
 for game_id in TRAIN+HELD:
  assert not done.is_set(),'Whole-host CPU guard'
  parent=ROOT/'human-command-repeats-01/corpus/870' if game_id=='870' else ROOT/'pro-demonstrations-production-08'/game_id if game_id in TRAIN else sources[game_id]
  receipt=json.loads((parent/'dataset.json').read_text());paths=list(receipt['source_bindings']);recordpath=next(Path(p) for p in paths if p.endswith('.bin'));replay=Path(receipt['source_replay']);catalogpath=next(Path(p) for p in paths if Path(p).name=='static.json');mappath=next(Path(p) for p in paths if p.endswith('.s2ma'));phasepath=Path(receipt['source_phase_proof']);reconciliationpath=next(Path(p) for p in paths if Path(p).name!='static.json' and 'reconcil' in Path(p).name)
  for p,digest in receipt['source_bindings'].items():assert sha(p)==digest,p
  old=json.loads(reconciliationpath.read_text());g=next(g for g in old['games'] if g['idx']==int(game_id));check_bindings(g)
  wirepath=next(Path(p) for p in g['bindings'] if Path(p).name==f'fall-actions-{game_id}.json')
  wire=json.loads(wirepath.read_text());assert wire['record_sha256']==sha(recordpath)
  record=decode_record(recordpath.read_bytes());f=record['units']['fields'];data=json.loads(catalogpath.read_text())['game_data'];catalog={a['ability_id']:a for a in data['abilities']};names={u['unit_id']:u['name'] for u in data['units']};meta,details=replay_metadata(replay);proto=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));archive=mpyq.MPQArchive(str(replay));original=list(proto.decode_replay_game_events(archive.read_file('replay.game.events')));events,unknown=command_events(original,receipt['source_user_id'])
  tracker_events=list(proto.decode_replay_tracker_events(archive.read_file('replay.tracker.events')));tracker=CausalTracker(tracker_events,receipt['player']['player_info']['player_id'],data);boundary={(e['_gameloop'],(e['m_unitTagIndex']<<18)|e['m_unitTagRecycle']):{u['name']:u['unit_id'] for u in data['units']}.get(e['m_unitTypeName'].decode()) for e in tracker_events if e['_event'].endswith('.SUnitTypeChangeEvent')}
  own=[{} for _ in record['steps']['game_loop']]
  for i,step in enumerate(record['units']['step']):
   if f['alliance'][i]==1:own[int(step)][int(f['id'][i])]=int(f['unitType'][i])
  for i,row in enumerate(wire['actions']):
   loop=int(record['steps']['game_loop'][i]);assert row['loop']==loop;tracker.advance(loop);types={}
   for command in row['actions']:
    for tag in command['tags']:
     kind=own[i].get(tag);low=tag&0xffffffff
     if kind is None or tracker.owners.get(low)!=receipt['player']['player_info']['player_id']:continue
     assert kind in (tracker.own_types.get(low),boundary.get((loop,low)))
     types[tag]=names[kind]
   row['unit_types']=types
  selected={(s['loop'],s['sequence']):s['tags'] for s in g['selections']}
  repeats=[e for e in events if e.get('source_manager')]
  for e in repeats:
   origin=e['source_command'];selected[e['_gameloop'],e['m_sequence']]=selected.get((origin['loop'],origin['sequence']))
  source_names=g.get('verified_candidate_names',g['replay_names'])
  accepted,audit=reconcile_commands(events,wire['actions'],selected,catalog,{(s['link'],s['index']):s['name'] for s in source_names})
  oldkeys={(a['loop'],a['sequence']) for a in g['accepted']};used={tuple(a['converted_position']) for a in g['accepted']};repeatkeys={(e['_gameloop'],e['m_sequence']) for e in repeats}
  added=[dict(a,command=a['command'].as_dict()) for a in accepted if (a['loop'],a['sequence']) not in oldkeys and tuple(a['converted_position']) not in used and (a['loop'],a['sequence']) in repeatkeys]
  new=dict(g,accepted=sorted(g['accepted']+added,key=lambda a:(a['loop'],a['sequence'])),selections=[dict(loop=k[0],sequence=k[1],tags=v) for k,v in selected.items()],audit=audit)
  folder=OUT/game_id;folder.mkdir();bindings={**code_hashes,**{str(p):sha(p) for p in (parent/'dataset.json',reconciliationpath,replay,recordpath,wirepath,catalogpath,phasepath,mappath)}};recon=folder/'reconciliation.json';recon.write_text(json.dumps(dict(games=[new],training_eligible=False,bindings=bindings),indent=2)+'\n')
  job=dict(record=str(recordpath),replay=str(replay),map=str(mappath),catalog=str(catalogpath),reconciliation=str(recon),phase=str(phasepath),record_index=int(game_id),output=str(folder/'corpus'))
  (folder/'job.json').write_text(json.dumps(job,indent=2)+'\n');(folder/'added.json').write_text(json.dumps(added)+'\n');(folder/'unknown.json').write_text(json.dumps(unknown)+'\n');import_game(job)
  role='teaching' if game_id in TRAIN else 'diagnostic';validate_datasets([folder/'corpus'],[],missing_fields=True)
  player=details['m_playerList'][receipt['player']['player_info']['player_id']-1];human_result=player['m_result']
  row=dict(game=game_id,role=role,parent=str(parent),original_count=len(g['accepted']),added=len(added),new_count=len(new['accepted']),unknown_repeat_contexts=len(unknown),human_result_code=human_result,base_build=meta['BaseBuild'],added_abilities=dict(Counter(a['command']['ability'] for a in added)),sha256=receipt['sha256']);summary.append(row);print(json.dumps(row),flush=True)
finally:done.set();thread.join(3)
validated=validate_datasets([OUT/g/'corpus' for g in TRAIN],[OUT/g/'corpus' for g in HELD],missing_fields=True)
assert all(sha(p)==digest for p,digest in code_hashes.items())
manifest=dict(status='rebuilt_existing_command_cohort',games=summary,validated=validated,training=False,rl=False,peak_cpu=max(cpu,default=0),code_bindings=code_hashes,limitations=['No new independent replay diversity; existing diagnostic games are reused, reserved games untouched.','Only uniquely reconciled source repeats are added; selection-change contexts remain unknown.'])
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');snap=OUT/'source-snapshot'
for p in code:
 dest=snap/(p.relative_to(Path.cwd()) if p.is_absolute() else p);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
print(json.dumps(dict(status=manifest['status'],games=len(summary),added=sum(r['added'] for r in summary),peak_cpu=manifest['peak_cpu'])),flush=True)
