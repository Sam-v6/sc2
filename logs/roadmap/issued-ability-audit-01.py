"""Audit existing labels against independent single-event ability mappings."""
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import mpyq
from src.learning.issued_commands import target_matches
from src.learning.replay_extract import load_protocol
root=Path('logs/roadmap')
directories=[root/f'issued-{i}' for i in (51574,51573,51958,51890,51891,50925)]+[root/'issued-51960-p1',root/'issued-51957-p1',root/'issued-51959-held-01']

def key(event):
    a=event['m_abil']
    return ('smart',) if a is None else (a['m_abilLink'],a['m_abilCmdIndex'])

def load(directory):
    receipt=json.loads((directory/'dataset.json').read_text())
    replay=Path(receipt['replay']);assert hashlib.sha256(replay.read_bytes()).hexdigest()==receipt['sha256']
    source=Path(receipt['source_dataset']);archive=mpyq.MPQArchive(str(replay));protocol=load_protocol(int(receipt['metadata']['BaseBuild'][4:]))
    init=protocol.decode_replay_initdata(archive.read_file('replay.initData'));player=receipt['player']['player_info']['player_id']
    users=[s['m_userId'] for s in init['m_syncLobbyState']['m_lobbyState']['m_slots'] if s['m_workingSetSlotId']==player-1 and s['m_userId'] is not None];assert len(users)==1
    events=defaultdict(list)
    for event in protocol.decode_replay_game_events(archive.read_file('replay.game.events')):
        if event['_event'].endswith('.SCmdEvent') and event['_userid']['m_userId']==users[0]:events[event['_gameloop']].append(event)
    with gzip.open(source/'examples.jsonl.gz','rt') as f:native=list(map(json.loads,f))
    with gzip.open(directory/'examples.jsonl.gz','rt') as f:issued=list(map(json.loads,f))
    catalog={a['ability_id']:a for a in json.loads((directory/'static.json').read_text())['game_data']['abilities']}
    return events,native,issued,catalog,receipt

bindings={}
for directory in directories:
    receipt=json.loads((directory/'dataset.json').read_text());source=Path(receipt['source_dataset'])
    for path in [directory/'dataset.json',directory/'static.json',directory/'examples.jsonl.gz',source/'examples.jsonl.gz',Path(receipt['replay'])]:bindings[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
loaded=[load(d) for d in directories]
# Reference mappings come only from loops with a single original human event and
# a unique native target/queue match. Do not infer from multi-event ordering.
mappings=defaultdict(lambda:defaultdict(list))
for directory,(events,native,_,catalog,_) in zip(directories,loaded):
    for row in native:
        es=events[row['action_loop']]
        if len(es)!=1:continue
        candidates=[c for c in row['commands'] if target_matches(c,es[0])]
        if len(candidates)!=1:continue
        c=candidates[0];canonical=catalog[c['ability']].get('remaps_to_ability_id') or c['ability']
        mappings[key(es[0])][canonical].append({'dataset':str(directory),'loop':row['action_loop'],'raw_ability':c['ability']})
results=[]
for directory,(events,_,issued,catalog,_) in zip(directories,loaded):
    result={'dataset':str(directory),'checked':0,'mismatches':[],'unsupported_mapping':0,'ambiguous_event_pairing':0,'outside_game_reference':0}
    for row in issued:
        es=events[row['action_loop']];commands=row['commands']
        pairs=[]
        if len(es)==len(commands) and all(target_matches(c,e) for c,e in zip(commands,es)):pairs=list(zip(commands,es))
        else:
            remaining=list(es)
            for c in commands:
                matches=[e for e in remaining if target_matches(c,e)]
                if len(matches)==1:pairs.append((c,matches[0]));remaining.remove(matches[0])
                else:result['ambiguous_event_pairing']+=1
        for c,e in pairs:
            mapping=mappings[key(e)]
            if len(mapping)!=1:result['unsupported_mapping']+=1;continue
            canonical=catalog[c['ability']].get('remaps_to_ability_id') or c['ability'];expected=next(iter(mapping))
            result['checked']+=1
            if any(s['dataset']!=str(directory) for s in mapping[expected]):result['outside_game_reference']+=1
            if canonical!=expected:result['mismatches'].append({'loop':row['action_loop'],'event_key':key(e),'raw_ability':c['ability'],'canonical':canonical,'expected':expected})
    results.append(result)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in bindings.items())
report={'status':'completed_without_relabeling','scope':'empirical ability-identity audit using single-event unique native matches; does not replace authoritative protocol mapping',
        'files':bindings,'games':results,'mappings':[{'event_key':k,'canonical_abilities':dict(v)} for k,v in mappings.items()],
        'mapping_conflicts':[{'event_key':k,'canonical_abilities':sorted(v)} for k,v in mappings.items() if len(v)>1],
        'limitations':'Mappings use corpus-native observations; in-game reference is not independent ground truth. Unsupported and ambiguous cases remain explicit.'}
(root/'issued-ability-audit-01.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'games':results,'mapping_keys':len(mappings),'mapping_conflicts':report['mapping_conflicts']},indent=2))
