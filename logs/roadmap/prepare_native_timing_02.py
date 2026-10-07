"""Native human production labels with independent ability and target evidence."""
import gzip,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
import mpyq,sc2reader
from src.learning.replay_extract import load_protocol
from src.learning.issued_commands import target_matches
from src.learning.tournament_commands import REGULAR_FLAGS
from src.learning.native_ability_identity import native_ability_matches as ability_matches
from src.learning.production_identity import producer_ability,research_ability
from src.learning.production_gate import native_gate_windows
ROOT=Path('logs/roadmap/dense-timing-cohort-01');OUT=Path('logs/roadmap/native-production-timing-02')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return list(map(json.loads,gzip.open(p,'rt')))
def main():
 report=json.loads((ROOT/'report.json').read_text());assert report['status']=='completed_dense_native_cohort'
 for p,h in report['bindings'].items():assert sha(p)==h,p
 manifest=json.loads((ROOT/'manifest.json').read_text());OUT.mkdir(exist_ok=False);results=[];bindings={str(Path(__file__)):sha(__file__),str(ROOT/'report.json'):sha(ROOT/'report.json'),str(ROOT/'manifest.json'):sha(ROOT/'manifest.json')}
 bindings['src/learning/production_gate.py']=sha('src/learning/production_gate.py')
 bindings['src/learning/native_ability_identity.py']=sha('src/learning/native_ability_identity.py')
 for game in manifest['games']:
  parent=Path(game['output']);receipt=json.loads((parent/'dataset.json').read_text());assert receipt['status']=='completed' and receipt['disable_fog'] is False;assert sha(game['replay'])==game['sha256']
  archive=mpyq.MPQArchive(game['replay']);protocol=load_protocol(75689);init=protocol.decode_replay_initdata(archive.read_file('replay.initData'));users=[s['m_userId'] for s in init['m_syncLobbyState']['m_lobbyState']['m_slots'] if s['m_workingSetSlotId']==game['player']-1 and s['m_userId'] is not None];assert len(users)==1
  events=[e for e in protocol.decode_replay_game_events(archive.read_file('replay.game.events')) if e['_event'].endswith('.SCmdEvent') and e['_userid']['m_userId']==users[0]]
  data=json.loads((parent/'static.json').read_text())['game_data'];catalog={a['ability_id']:a for a in data['abilities']};units={u['unit_id']:u['name'] for u in data['units']}
  production=lambda a:catalog[a].get('friendly_name','').startswith(('Build ','Train ','Research ')) or catalog[a].get('friendly_name') in ('Morph OrbitalCommand','Morph PlanetaryFortress')
  reader=sc2reader.load_replay(game['replay'],load_level=2,load_map=False);names={}
  for event in events:
   ab=event['m_abil']
   if ab is None:continue
   key=(ab['m_abilLink'],ab['m_abilCmdIndex']);meta=reader.datapack.abilities.get((key[0]<<5)|key[1])
   if meta is None:continue
   candidate=producer_ability(meta.build_unit.name,key[1],data) if meta.build_unit else research_ability(meta.name,key[1],data)
   names[key]=catalog[candidate]['friendly_name'] if candidate is not None else meta.name
  rows=read(parent/'examples.jsonl.gz');byloop=defaultdict(list)
  for i,row in enumerate(rows):
   own={u['tag'] for u in row['observation']['units'] if u['alliance']==1};types={u['tag']:units[u['unit_type']] for u in row['observation']['units'] if u['alliance']==1}
   for j,command in enumerate(row['commands']):
    if command['units'] and set(command['units'])<=own:byloop[row['action_loop']].append(((i,j),command,types))
  matches=[];usage=Counter()
  for event in events:
   candidates=[]
   for identity,command,types in byloop[event['_gameloop']]:
    if target_matches(command,event) and ability_matches(dict(ability=command['ability'],tags=command['units']),event,catalog,names,types):candidates.append((identity,command))
   matches.append(candidates);usage.update(identity for identity,_ in candidates)
  accepted={};seed=defaultdict(set);seed_keys=defaultdict(list)
  keyof=lambda e:(e['_gameloop'],e['m_sequence'])
  linkof=lambda e:None if e['m_abil'] is None else(e['m_abil']['m_abilLink'],e['m_abil']['m_abilCmdIndex'])
  for event,candidates in zip(events,matches,strict=True):
   if len(candidates)!=1 or usage[candidates[0][0]]!=1:continue
   identity,command=candidates[0];flags=event['m_cmdFlags']
   if flags & ~REGULAR_FLAGS or not flags & 0x100:continue
   accepted[keyof(event)]=dict(ability=command['ability'],native_position=identity)
   seed[linkof(event)].add(command['ability']);seed_keys[linkof(event)].append(keyof(event))
  classes=[]
  for event in events:
   key=keyof(event);item=dict(key=key,event=event,classification='unknown',proof='unresolved',ability=None)
   if key in accepted:
    item.update(accepted[key],classification='production' if production(accepted[key]['ability']) else 'nonproduction',proof='unique_native_target_queue_ability_own_actor')
   else:
    candidates=seed.get(linkof(event),set());kinds={production(a) for a in candidates};flags=event['m_cmdFlags']
    if kinds=={False}:item.update(classification='nonproduction',proof='verified_numeric_nonproduction_identity',reference_keys=seed_keys[linkof(event)])
    elif kinds=={True} and flags & 0x100 and not flags & ~REGULAR_FLAGS:item.update(classification='production',proof='regular_user_numeric_production_identity',reference_keys=seed_keys[linkof(event)],ability=next(iter(candidates)) if len(candidates)==1 else None)
   classes.append(item)
  states=read(parent/'observations.jsonl.gz');assert [s['game_loop'] for s in states]==list(range(0,receipt['last_loop']+1,44));folder=OUT/game['game'];folder.mkdir();counts=Counter();labels=[]
  labels=native_gate_windows([s['game_loop'] for s in states],[e['key'] for e in classes if e['classification']=='production'],[e['key'] for e in classes if e['classification']=='unknown'],receipt['last_loop'])
  with gzip.open(folder/'examples.jsonl.gz','xt') as stream:
   for state,label in zip(states,labels,strict=True):
    counts[str(label['act'])]+=1
    # Archived causal human history is preserved separately, excluded from gate inputs.
    stream.write(json.dumps(dict(observation=dict(state,recent_commands=[]),label=label),separators=(',',':'))+'\n')
  (folder/'events.json').write_text(json.dumps(classes,indent=2)+'\n')
  item=dict(game=game['game'],role=game['role'],player_name=game['player_name'],reader_datapack=str(reader.datapack.id),source_events=len(events),counts=dict(counts),event_counts=dict(Counter(e['classification'] for e in classes)),unique_native_proofs=len(accepted),anchors=len(states),covered_elapsed_loops=(len(states)-1)*44,total_elapsed_loops=receipt['last_loop'],unknown_label_semantics='Human SCmdEvent issuance only; engine manager repeats excluded explicitly')
  results.append(item);print(json.dumps(item),flush=True)
  for p in [parent/'dataset.json',parent/'static.json',parent/'observations.jsonl.gz',parent/'examples.jsonl.gz',Path(game['replay']),folder/'events.json',folder/'examples.jsonl.gz']:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in report['bindings'].items())
 (OUT/'report.json').write_text(json.dumps(dict(status='prepared_native_human_production_timing',games=results,bindings=bindings,training=False,rl=False,interval='Native current state L; human issuance in (L,L+44], pre-command state alignment distinct from partial pro issue-loop observations.',limitations=['Masters teaching is one named player, Mez, across five games.','Calibration and evaluation are different named players but reused diagnostics, not fresh acceptance.','Source reader uses an older data pack; names alone never establish negative labels.','Production gates target original human SCmdEvent decisions; professional choice cohort also retains explicitly provenance-backed manager repetitions.']),indent=2)+'\n')
if __name__=='__main__':main()
