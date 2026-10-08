import pathlib,json,collections,mpyq,hashlib
from src.learning.tournament_commands import reconcile_commands
from src.learning.replay_extract import load_protocol
import sc2reader
P=pathlib.Path(__file__).parent;q=load_protocol(76052);out=[]
CAT=pathlib.Path("logs/roadmap/joint-frozen-native-wait-02/static.json");catalog={a["ability_id"]:a for a in json.loads(CAT.read_text())["game_data"]["abilities"]}
for idx,name in [(294,'e2dd17959af64796940c877c4a715a54'),(774,'688e7db4d4ea37cb45fac1d09d9559f2'),(870,'2cda222081e80d9a1c188698ce9bcda6')]:
 parsed=sc2reader.load_replay(str(P/f'{name}.SC2Replay'),load_level=4,load_map=False);masks=collections.defaultdict(collections.deque)
 for event in parsed.game_events:
  if event.pid!=0:continue
  if event.name=='SelectionEvent':key=('S',event.frame,event.control_group)
  elif 'ControlGroupEvent' in event.name:key=('C',event.frame,event.control_group)
  else:continue
  masks[key].append((event.mask_type,event.mask_data))
 archive=mpyq.MPQArchive(str(P/f'{name}.SC2Replay'));groups={i:[] for i in range(11)};selections={};counts=collections.Counter();disagreements=[];align=json.loads((P/f'command-alignment-{idx}.json').read_text());matches=collections.defaultdict(list)
 for a in align['accepted']:matches[a['loop']].append(a)
 def deselect(group,mask):
  mode,data=next(iter(mask.items()))
  if mode=='None':return group
  if mode=='ZeroIndices' and not data:return []
  if group is None:return None
  if mode=='ZeroIndices':return [group[i] for i in data] if all(0<=i<len(group) for i in data) else None
  if mode=='Mask':
   length,bits=data
   return [u for i,u in enumerate(group) if i>=length or not (bits>>i)&1] if length<=len(group) else None
  if mode=='OneIndices':return [u for i,u in enumerate(group) if i not in data] if all(0<=i<len(group) for i in data) else None
  return None
 for e in q.decode_replay_game_events(archive.read_file('replay.game.events')):
  if e['_userid']['m_userId']!=0:continue
  kind=e['_event'].split('.')[-1]
  if kind in ('SSelectionDeltaEvent','SControlGroupUpdateEvent'):
   selection=kind=='SSelectionDeltaEvent';g=e['m_controlGroupId'] if selection else e['m_controlGroupIndex'];mask=e['m_delta']['m_removeMask'] if selection else e['m_mask'];mode,data=masks[('S' if selection else 'C',e['_gameloop'],g)].popleft();assert mode==next(iter(mask))
   if mode=='Mask':
    packed=(len(data),sum(int(bit)<<i for i,bit in enumerate(data)));counts['normalized_mask_events']+=1;counts['different_packed_mask_events']+=packed!=tuple(mask['Mask']);mask['Mask']=packed
   elif mode!='None':assert data==mask[mode]
  if kind=='SSelectionDeltaEvent':
   g=e['m_controlGroupId'];d=e['m_delta'];v=deselect(groups[g],d['m_removeMask']);groups[g]=None if v is None else sorted(set(v+d['m_addUnitTags']))
  elif kind=='SControlGroupUpdateEvent':
   g=e['m_controlGroupIndex'];t=e['m_controlGroupUpdate']
   if t in (0,4):groups[g]=None if groups[10] is None else groups[10][:]
   elif t in (1,5):
    v=deselect(groups[g],e['m_mask']);groups[g]=None if v is None or groups[10] is None else sorted(set(v+groups[10]))
   elif t==2:groups[10]=deselect(groups[g],e['m_mask'])
   elif t==3:groups[g]=[]
   else:
    for k in range(10):groups[k]=None
  elif kind=='SCmdEvent':
   selections[(e['_gameloop'],e['m_sequence'])]=None if groups[10] is None else groups[10][:]
   a=[a for a in matches[e['_gameloop']] if a['original']['m_sequence']==e['m_sequence']]
   if not a:continue
   counts['matched_commands']+=1
   if groups[10] is None:counts['unknown_selection']+=1;continue
   selected=set(groups[10]);actors={t&0xffffffff for t in a[0]['converted']['tags']};counts['known_selection']+=1;counts['actors_within_human_selection']+=actors<=selected;counts['exact_human_selection']+=actors==selected
   if not actors<=selected:disagreements.append({'loop':e['_gameloop'],'selection':sorted(selected),'actors':sorted(actors),'event':e,'converted':a[0]['converted']})
 events=json.loads((P/f'raw-commands-{idx}.json').read_text());names={}
 for e in events:
  a=e['m_abil']
  if a is not None:
   key=(a['m_abilLink'],a['m_abilCmdIndex']);ability=parsed.datapack.abilities.get((key[0]<<5)|key[1])
   if ability is not None:names[key]=ability.name
 actions=json.loads((P/f'fall-actions-{idx}.json').read_text())['actions']
 accepted,audit=reconcile_commands(events,actions,selections,catalog,names)
 r=dict(idx=idx,selection_counts=dict(counts),audit=audit,
  accepted=[dict(row,command=row['command'].as_dict()) for row in accepted],
  selections=[dict(loop=k[0],sequence=k[1],tags=v) for k,v in selections.items()],
  replay_names=[dict(link=k[0],index=k[1],name=v) for k,v in names.items()],
  bindings={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (P/f'{name}.SC2Replay',P/f'raw-commands-{idx}.json',P/f'fall-actions-{idx}.json',CAT)})
 out.append(r);print(idx,len(accepted),len(audit['unresolved_events']),flush=True)
code=[pathlib.Path('src/learning/tournament_commands.py'),pathlib.Path(__file__),pathlib.Path(q.__file__),pathlib.Path(sc2reader.readers.__file__),pathlib.Path(__import__("importlib").import_module("sc2reader.data").__file__)]
receipt=dict(games=out,training_eligible=False,bindings={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in code})
(P/'command-reconciliation-03.json').write_text(json.dumps(receipt,indent=2)+'\n')
