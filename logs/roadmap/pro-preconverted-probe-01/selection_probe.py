import pathlib,json,collections,mpyq
from src.learning.replay_extract import load_protocol
import sc2reader
P=pathlib.Path(__file__).parent;q=load_protocol(76052);out=[]
for idx,name in [(294,'e2dd17959af64796940c877c4a715a54'),(774,'688e7db4d4ea37cb45fac1d09d9559f2'),(870,'2cda222081e80d9a1c188698ce9bcda6')]:
 parsed=sc2reader.load_replay(str(P/f'{name}.SC2Replay'),load_level=4,load_map=False);masks=collections.defaultdict(collections.deque)
 for event in parsed.game_events:
  if event.pid!=0:continue
  if event.name=='SelectionEvent':key=('S',event.frame,event.control_group)
  elif 'ControlGroupEvent' in event.name:key=('C',event.frame,event.control_group)
  else:continue
  masks[key].append((event.mask_type,event.mask_data))
 archive=mpyq.MPQArchive(str(P/f'{name}.SC2Replay'));groups={i:[] for i in range(11)};counts=collections.Counter();disagreements=[];align=json.loads((P/f'command-alignment-{idx}.json').read_text());matches=collections.defaultdict(list)
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
   a=[a for a in matches[e['_gameloop']] if a['original']['m_sequence']==e['m_sequence']]
   if not a:continue
   counts['matched_commands']+=1
   if groups[10] is None:counts['unknown_selection']+=1;continue
   selected=set(groups[10]);actors={t&0xffffffff for t in a[0]['converted']['tags']};counts['known_selection']+=1;counts['actors_within_human_selection']+=actors<=selected;counts['exact_human_selection']+=actors==selected
   if not actors<=selected:disagreements.append({'loop':e['_gameloop'],'selection':sorted(selected),'actors':sorted(actors),'event':e,'converted':a[0]['converted']})
 r={'idx':idx,'first_disagreements':disagreements[:12],'counts':dict(counts),'limits':['Bit masks normalized with installed sc2reader1.8.0 reader; OneIndices removes named indices; steal set/add followed by replay automatic cleanup events','Sorted-tag reconstruction follows referenced SelectionTracker; mixed subgroup dispatch not independently reconstructed','Membership corroborates selected actor tags; it does not prove every command actor must equal the complete human UI selection'],'training_eligible':False};out.append(r);print(idx,counts)
(P/'professional-selection-audit.json').write_text(json.dumps(out,indent=2)+'\n')
