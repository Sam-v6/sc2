import gzip,json
from collections import Counter
from pathlib import Path
OUT=Path('logs/roadmap/primitives-hard-baseline-01/panel')
contract=json.loads((OUT/'contract.json').read_text());counts=Counter();delayed=Counter();examples=[]
for job in contract['jobs']:
 replay=Path(job['replay']);data=json.loads(replay.with_suffix('.primitives.data.json').read_text());names={u['unit_id']:u['name'] for u in data['units']};state=None
 for line in gzip.open(replay.with_suffix('.primitives.jsonl.gz'),'rt'):
  row=json.loads(line)
  if row['observation']:state=row['observation']
  by_tag={u['tag']:u for u in state['units']} if state else {}
  for command,code in zip(row['commands'],row['results'],strict=True):
   if code==1:continue
   target=by_tag.get(command['target_unit'],{});actors=[by_tag.get(tag,{}) for tag in command['units']]
   actor_names=','.join(names.get(u.get('unit_type'),'unknown') for u in actors);target_name=names.get(target.get('unit_type'),'unknown')
   counts[(code,command['ability'],actor_names,target_name)]+=1
   if len(examples)<10:examples.append(dict(job=job,loop=row['loop'],command=command,result=code,sampled_actor=actors,sampled_target=target,state_loop=state['game_loop'] if state else None))
  for error in row['delayed_errors']:delayed[(error['ability'],error['result'])]+=1
r=dict(raw=[dict(result=k[0],ability=k[1],actors=k[2],target=k[3],count=v) for k,v in counts.items()],delayed=[dict(ability=k[0],result=k[1],count=v) for k,v in delayed.items()],examples=examples,limits=['Actor/target descriptions use the most recent macro sample and can precede the command; response codes are exact.'])
(OUT/'action-error-audit.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k!='examples'},indent=2))
