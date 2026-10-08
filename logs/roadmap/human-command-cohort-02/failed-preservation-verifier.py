"""Independent preservation, event identity, wire uniqueness and split verification."""
import gzip,hashlib,json,mpyq
from pathlib import Path
from src.learning.replay_extract import replay_metadata,load_protocol
from src.learning.replay_command_events import command_events
from src.learning.entity_train import validate_datasets
ROOT=Path('logs/roadmap');OUT=ROOT/'human-command-cohort-02';manifest=json.loads((OUT/'manifest.json').read_text());results=[];identities=set()
for path,digest in manifest['code_bindings'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
for game in manifest['games']:
 folder=OUT/game['game'];parent=Path(game['parent']);dataset=folder/'corpus';old=[json.loads(l) for l in gzip.open(parent/'examples.jsonl.gz','rt')];new=[json.loads(l) for l in gzip.open(dataset/'examples.jsonl.gz','rt')];key=lambda r:(r['action_loop'],r['source_sequence']);prior={key(r):r for r in old};current={key(r):r for r in new};assert len(prior)==len(old) and len(current)==len(new)
 assert len(new)==game['new_count']==len(old)+game['added']
 for k,row in prior.items():
  replacement=current[k];assert row['commands']==replacement['commands'],(game['game'],k)
  for field in ('player','units','map','map_size','upgrades','effects','memory','owned_memory'):
   assert row['observation'].get(field)==replacement['observation'].get(field),(game['game'],k,field)
 receipt=json.loads((dataset/'dataset.json').read_text());assert receipt['sha256'] not in identities;identities.add(receipt['sha256']);replay=Path(receipt['source_replay']);meta,_=replay_metadata(replay);protocol=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));original=list(protocol.decode_replay_game_events(mpyq.MPQArchive(str(replay)).read_file('replay.game.events')));events,unknown=command_events(original,receipt['source_user_id']);bykey={(e['_gameloop'],e['m_sequence']):e for e in events};g=json.loads((folder/'reconciliation.json').read_text())['games'][0];selected={(s['loop'],s['sequence']):s['tags'] for s in g['selections']};added=json.loads((folder/'added.json').read_text());wirepath=next(Path(p) for p in g['bindings'] if Path(p).name==f"fall-actions-{game['game']}.json");wire=json.loads(wirepath.read_text());used={tuple(a['converted_position']) for a in g['accepted'] if (a['loop'],a['sequence']) in prior};seen=set()
 for item in added:
  k=(item['loop'],item['sequence']);assert k not in prior and k in current;event=bykey[k];assert event.get('source_manager') and event['source_manager']['m_state']==1 and event['source_manager']['m_sequence']==k[1]
  assert set(item['command']['units'])==set(selected[k]);position=tuple(item['converted_position']);assert position not in used and position not in seen;seen.add(position);action=wire['actions'][position[0]]['actions'][position[1]];assert set(action['tags'])==set(item['command']['units'])
  assert current[k]['commands']==[item['command']]
  assert item['command']['ability']==action['ability'] or item['command']['ability'] in (1,23,3674,3675,3676,3679,3680,3681), (game['game'],k,'alias requires review')
  assert current[k]['observation']['game_loop']==k[0] and 'source_repeat_provenance' not in current[k]['observation']
 assert len(unknown)==game['unknown_repeat_contexts'];results.append(dict(game=game['game'],role=game['role'],old_preserved=len(old),added=len(added),new=len(new),unknown_contexts=len(unknown)))
assert len(identities)==9 and manifest['peak_cpu']<=80
validate_datasets([OUT/g['game']/'corpus' for g in manifest['games'] if g['role']=='teaching'],[OUT/g['game']/'corpus' for g in manifest['games'] if g['role']=='diagnostic'],missing_fields=True)
result=dict(status='verified_existing_command_cohort_expansion',games=results,total_added=sum(g['added'] for g in results),training=False,rl=False,peak_cpu=manifest['peak_cpu'],limitations=['No new replay diversity; diagnostics reused; reserved games were not loaded.','Original observations and labels are preserved; history includes recovered commands and explicitly unknown event slots.'],bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),OUT/'manifest.json')})
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(result))
