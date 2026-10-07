"""Independent preservation, event identity, wire uniqueness and split verification."""
import gzip,hashlib,json,mpyq,math,struct
from collections import defaultdict
from src.learning.tournament_record import decode_record
from pathlib import Path
from src.learning.replay_extract import replay_metadata,load_protocol
from src.learning.replay_command_events import command_events
from src.learning.entity_train import validate_datasets
ROOT=Path('logs/roadmap');OUT=ROOT/'human-command-cohort-03';manifest=json.loads((OUT/'manifest.json').read_text());results=[];identities=set()
for path,digest in manifest['code_bindings'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
for game in manifest['games']:
 folder=OUT/game['game'];parent=Path(game['parent']);dataset=folder/'corpus';old=[json.loads(l) for l in gzip.open(parent/'examples.jsonl.gz','rt')];new=[json.loads(l) for l in gzip.open(dataset/'examples.jsonl.gz','rt')];key=lambda r:(r['action_loop'],r['source_sequence']);prior={key(r):r for r in old};current={key(r):r for r in new};assert len(prior)==len(old) and len(current)==len(new)
 assert len(new)==game['new_count']==len(old)+game['added']
 for k,row in prior.items():
  replacement=current[k];assert row['commands']==replacement['commands'],(game['game'],k)
  assert [u for u in row['observation']['units'] if u['alliance']!=4]==[u for u in replacement['observation']['units'] if u['alliance']!=4],(game['game'],k,'owned and neutral units')
  for field in ('player','map','map_size','upgrades','effects','owned_memory'):
   assert row['observation'].get(field)==replacement['observation'].get(field),(game['game'],k,field)
 receipt=json.loads((dataset/'dataset.json').read_text());assert receipt['sha256'] not in identities;identities.add(receipt['sha256']);replay=Path(receipt['source_replay']);meta,_=replay_metadata(replay);protocol=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));original=list(protocol.decode_replay_game_events(mpyq.MPQArchive(str(replay)).read_file('replay.game.events')));events,unknown=command_events(original,receipt['source_user_id']);bykey={(e['_gameloop'],e['m_sequence']):e for e in events};g=json.loads((folder/'reconciliation.json').read_text())['games'][0];selected={(s['loop'],s['sequence']):s['tags'] for s in g['selections']};added=json.loads((folder/'added.json').read_text());wirepath=next(Path(p) for p in g['bindings'] if Path(p).name==f"fall-actions-{game['game']}.json");wire=json.loads(wirepath.read_text());used={tuple(a['converted_position']) for a in g['accepted'] if (a['loop'],a['sequence']) in prior};seen=set()
 for item in added:
  k=(item['loop'],item['sequence']);assert k not in prior and k in current;event=bykey[k];assert event.get('source_manager') and event['source_manager']['m_state']==1 and event['source_manager']['m_sequence']==k[1]
  assert {tag & 0xffffffff for tag in item['command']['units']}<=set(selected[k]);position=tuple(item['converted_position']);assert position not in used and position not in seen;seen.add(position);action=wire['actions'][position[0]]['actions'][position[1]];assert set(action['tags'])==set(item['command']['units'])
  assert selected[k]==selected[(event['source_command']['loop'],event['source_command']['sequence'])]
  assert current[k]['original_command']==item['command']
  translated=current[k]['commands'][0];expected_command=dict(item['command'])
  if translated!=expected_command:
   mapping=next(m for m in receipt['source_resource_mappings'] if (m['loop'],m['sequence'])==k)
   target=event['m_data']['TargetUnit'];point=[target['m_snapshotPoint'][axis]/4096 for axis in ('x','y')]
   assert target['m_snapshotControlPlayerId']==target['m_snapshotUpkeepPlayerId']==0
   assert mapping['position']==point and mapping['original_tag']==expected_command['target_unit']
   candidates=[u for u in current[k]['observation']['units'] if u['alliance']==3 and u['unit_type']==mapping['unit_type'] and u['position'][:2]==point and u.get('display_type',1)==1]
   assert len(candidates)==1 and candidates[0]['tag']==mapping['source_tag']
   expected_command['target_unit']=mapping['source_tag']
  assert translated==expected_command
  assert item['command']['ability']==action['ability'], (game['game'],k,'wire ability')
  assert item['command']['queue']==bool(event['m_cmdFlags'] & 2)
  source_target=event['m_data']
  if 'TargetPoint' in source_target:assert item['command']['target_point']==[source_target['TargetPoint'][axis]/4096 for axis in ('x','y')]
  if 'TargetUnit' in source_target:assert item['command']['target_unit'] & 0xffffffff == source_target['TargetUnit']['m_tag']
  assert current[k]['observation']['game_loop']==k[0] and 'source_repeat_provenance' not in current[k]['observation']
 # Reconstruct enemy memory from EVERY chronological source frame, including
 # frames without accepted commands. This checks the fog repair independently
 # of PlayerView/partial_observation and prevents future-state memory leakage.
 job=json.loads((folder/'job.json').read_text());record=decode_record(Path(job['record']).read_bytes());fields=record['units']['fields'];indices=defaultdict(list)
 for i,step in enumerate(record['units']['step']):
  if int(fields['alliance'][i])==4:indices[int(step)].append(i)
 byloop=defaultdict(list)
 for r in new:byloop[r['action_loop']].append(r)
 known={};checked=0;memory_changed=0;enemy_changed=0
 size=new[0]['observation']['map_size']
 for step,loop in enumerate(record['steps']['game_loop']):
  loop=int(loop);grid=record['images']['visibility'][step];height,width=grid.shape;scale=width/max(size);visible={}
  for i in indices[step]:
   display=int(fields['observation'][i])
   if fields['is_blip'][i] or display==3:continue
   tag=int(fields['id'][i]);pos=list(map(float,fields['pos'][i]));x=math.floor(pos[0]*scale);y=math.floor((size[1]-pos[1])*scale)
   seen=display==1 and 0<=x<width and 0<=y<height and grid[y,x]==2
   identity=dict(tag=tag,unit_type=int(fields['unitType'][i]),position=pos)
   if seen:known[tag]=dict(identity,last_seen_loop=loop);visible[tag]=dict(identity,health=float(fields['health'][i]))
   elif display==2 and tag not in known:known[tag]=dict(identity,last_seen_loop=None)
  expected=[dict(v) for tag,v in sorted(known.items()) if tag not in visible]
  for r in byloop.get(loop,[]):
   st=r['observation'];assert st['memory']==expected,(game['game'],loop,'source memory');actual={u['tag']:u for u in st['units'] if u['alliance']==4};assert set(actual)==set(visible),(game['game'],loop,'source visible tags')
   for tag,v in visible.items():
    assert all(actual[tag].get(f)==value for f,value in v.items() if f!='health'),(game['game'],loop,tag,'source visible identity')
    assert struct.pack('<f',actual[tag].get('health',0))==struct.pack('<f',v['health']),(game['game'],loop,tag,'source health float32')
   checked+=1;k=key(r)
   if k in prior:
    memory_changed+=int(prior[k]['observation']['memory']!=st['memory']);enemy_changed+=int([u for u in prior[k]['observation']['units'] if u['alliance']==4]!=list(actual.values()))
 assert checked==len(new)
 assert len(unknown)==game['unknown_repeat_contexts'];results.append(dict(game=game['game'],role=game['role'],old_preserved=len(old),added=len(added),new=len(new),unknown_contexts=len(unknown),source_fog_checked=checked,old_memory_changed=memory_changed,old_enemy_changed=enemy_changed))
assert len(identities)==5 and manifest['peak_cpu']<=80
original_manifest=json.loads((ROOT/'human-command-cohort-02/manifest.json').read_text())
assert not identities.intersection(g['sha256'] for g in original_manifest['games'])
reserved=json.loads((ROOT/'compatible-expansion-split-01.json').read_text())
# Reserved source protection follows the existing intake's frozen identity check.
intake=ROOT/'pro-source-expansion-02/final-verification.json'
intake_report=json.loads(intake.read_text());assert intake_report['status']=='verified_intake'
allowed={row['path']:row for row in intake_report['sources'] if row['role']=='teaching'}
for game in manifest['games']:
 assert game['parent'] in allowed
 for path,digest in allowed[game['parent']]['bindings'].items():
  assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
assert not identities.intersection(row['whole_replay_sha256'] for row in reserved['replays'] if row['role'].startswith('reserved'))

validate_datasets([OUT/g['game']/'corpus' for g in manifest['games'] if g['role']=='teaching'],[OUT/g['game']/'corpus' for g in manifest['games'] if g['role']=='diagnostic'],missing_fields=True)
result=dict(status='verified_additional_professional_command_cohort',games=results,total_added=sum(g['added'] for g in results),training=False,rl=False,peak_cpu=manifest['peak_cpu'],limitations=['Five additional games for current production-choice corpus, already used in an older broad-controller experiment; no fresh evaluation. Reserved and diagnostic games were not loaded.','Original labels, owned/neutral units and player/map fields are preserved; enemy visibility and memory are causally reconstructed from the supplied source grid. History includes recovered commands and explicitly unknown event slots.'],bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),OUT/'manifest.json',intake,ROOT/'human-command-cohort-02/manifest.json')})
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(result))
