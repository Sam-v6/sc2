"""Audit source SCV repeats across selection changes using the established mask decoder."""
from pathlib import Path
from collections import defaultdict,deque
import json,hashlib,mpyq,sc2reader
from src.learning.replay_extract import load_protocol,replay_metadata
root=Path('logs/roadmap');out=root/'worker-manager-selection-01';out.mkdir(exist_ok=False);source=root/'pro-preconverted-probe-01';replay=source/'2cda222081e80d9a1c188698ce9bcda6.SC2Replay';parsed=sc2reader.load_replay(str(replay),load_level=4,load_map=False);masks=defaultdict(deque)
for e in parsed.game_events:
 if e.pid!=0:continue
 if e.name=='SelectionEvent':key=('S',e.frame,e.control_group)
 elif 'ControlGroupEvent' in e.name:key=('C',e.frame,e.control_group)
 else:continue
 masks[key].append((e.mask_type,e.mask_data))
meta,_=replay_metadata(replay);pr=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));events=list(pr.decode_replay_game_events(mpyq.MPQArchive(str(replay)).read_file('replay.game.events')));groups={i:[] for i in range(11)};selections={};last=None;possible=[]
wire=json.loads((source/'fall-actions-870.json').read_text())['actions'];byloop={row['loop']:row['actions'] for row in wire};old=json.loads((root/'human-command-repeats-01/reconciliation.json').read_text())['games'][0];accepted={(r['loop'],r['sequence']) for r in old['accepted']}
def deselect(group,mode,data):
 if mode=='None':return group
 if mode=='ZeroIndices' and not data:return []
 if group is None:return None
 if mode=='Mask':return [u for i,u in enumerate(group) if i>=len(data) or not data[i]] if len(data)<=len(group) else None
 if not all(0<=i<len(group) for i in data):return None
 if mode=='ZeroIndices':return [group[i] for i in data]
 if mode=='OneIndices':return [u for i,u in enumerate(group) if i not in data]
 return None
for e in events:
 if e.get('_userid',{}).get('m_userId')!=0:continue
 kind=e['_event'].rsplit('.',1)[-1]
 if kind in ('SSelectionDeltaEvent','SControlGroupUpdateEvent'):
  select=kind=='SSelectionDeltaEvent';g=e['m_controlGroupId'] if select else e['m_controlGroupIndex'];mode,data=masks['S' if select else 'C',e['_gameloop'],g].popleft()
  raw=e['m_delta']['m_removeMask'] if select else e['m_mask'];assert mode==next(iter(raw))
  if mode not in ('None','Mask'):assert data==raw[mode]
  if select:
   v=deselect(groups[g],mode,data);groups[g]=None if v is None else sorted(set(v+e['m_delta']['m_addUnitTags']))
  else:
   t=e['m_controlGroupUpdate']
   if t in (0,4):groups[g]=None if groups[10] is None else groups[10][:]
   elif t in (1,5):
    v=deselect(groups[g],mode,data);groups[g]=None if v is None or groups[10] is None else sorted(set(v+groups[10]))
   elif t==2:groups[10]=deselect(groups[g],mode,data)
   elif t==3:groups[g]=[]
   else:
    for k in range(10):groups[k]=None
 elif kind in ('SCmdEvent','SCommandManagerStateEvent'):
  key=e['_gameloop'],e['m_sequence'];selections[key]=None if groups[10] is None else groups[10][:]
  if kind=='SCmdEvent':last=e
  elif last and last.get('m_abil')==dict(m_abilLink=155,m_abilCmdIndex=0,m_abilCmdData=None) and key not in accepted:
   matching=[a for a in byloop.get(e['_gameloop'],[]) if a['ability']==524 and groups[10] is not None and all(tag&0xffffffff in groups[10] for tag in a['tags'])]
   if len(matching)==1:possible.append(dict(loop=key[0],sequence=key[1],original_command=dict(loop=last['_gameloop'],sequence=last['m_sequence']),selected=groups[10][:],wire_action=matching[0]))
old_selections={(s['loop'],s['sequence']):s['tags'] for s in old['selections'] if (s['loop'],s['sequence']) in {(e['_gameloop'],e['m_sequence']) for e in events if e['_event'].endswith('.SCmdEvent') and e.get('_userid',{}).get('m_userId')==0}}
assert all(selections[k]==v for k,v in old_selections.items())
result=dict(status='audited_worker_repeat_selection',old_selections_preserved=len(old_selections),possible_missing_scv_commands=possible,missing_before9224=sum(r['loop']<9224 for r in possible),training=False,rl=False,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),replay,source/'fall-actions-870.json')})
(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');(out/'selections.json').write_text(json.dumps([dict(loop=k[0],sequence=k[1],tags=v) for k,v in selections.items()],indent=2)+'\n');(out/'auditor.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(result))
