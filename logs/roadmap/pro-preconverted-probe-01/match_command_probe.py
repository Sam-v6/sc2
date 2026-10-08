import pathlib,json,collections,hashlib
P=pathlib.Path(__file__).parent

def matches(a,e):
 d=e['m_data']
 if 'None' in d:return a['target_type']==0
 if 'TargetPoint' in d:return a['target_type']==2 and a['target']==[int(d['TargetPoint'][k]/4096) for k in ('x','y')]
 if 'TargetUnit' in d:return a['target_type']==1 and (a['target']&0xffffffff)==d['TargetUnit']['m_tag']
 return False
out=[];mapping=collections.defaultdict(collections.Counter)
for idx in (294,774,870):
 dataset=json.loads((P/f'fall-actions-{idx}.json').read_text());events=json.loads((P/f'raw-commands-{idx}.json').read_text());by=collections.defaultdict(list)
 for row in dataset['actions']:by[row['loop']].extend(row['actions'])
 counts=collections.Counter();accepted=[];unknown=[]
 for e in events:
  actions=by.get(e['_gameloop'],[]); candidates=[a for a in actions if matches(a,e)];counts['issued']+=1;counts['same_loop_any_action']+=bool(actions)
  if len(candidates)==1:
   a=candidates[0];counts['unique_loop_target_match']+=1
   link=e['m_abil'];key=(link['m_abilLink'],link['m_abilCmdIndex']) if link else ('smart',0);mapping[key][a['ability']]+=1
   accepted.append({'loop':e['_gameloop'],'converted':a,'original':e,'restored_queue':bool(e['m_cmdFlags']&2),'restored_point':[e['m_data']['TargetPoint'][k]/4096 for k in ('x','y')] if 'TargetPoint' in e['m_data'] else None})
  else:unknown.append({'loop':e['_gameloop'],'candidate_count':len(candidates)})
 r={'idx':idx,'header':dataset['header'],'counts':dict(counts),'unresolved':unknown,'raw_sha256':hashlib.sha256((P/f'raw-commands-{idx}.json').read_bytes()).hexdigest(),'converted_sha256':hashlib.sha256((P/f'fall-actions-{idx}.json').read_bytes()).hexdigest(),'criterion':'same exact issue loop and target type, integer-truncated point or lower32 target tag; ability and actor selection not yet independently verified','accepted':accepted};(P/f'command-alignment-{idx}.json').write_text(json.dumps(r,indent=2)+'\n');out.append({k:v for k,v in r.items() if k not in ('accepted','unresolved')});print(idx,counts,flush=True)
summary={'games':out,'ability_mapping_candidates':[{'link':list(k),'counts':dict(v)} for k,v in mapping.items()],'training_eligible':False,'remaining':['Verify selected unit tags against replay selection events','Verify ability mapping independently','Decode units, verify observation precedes command execution and fog safety','Recover missing upgrades or explicitly mask unavailable observations','Exclude ambiguous repeats and unrecovered command modes']};(P/'professional-command-alignment-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
