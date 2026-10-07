"""Inspect original human resource-commitment commands without fitting a policy."""
import gzip,hashlib,json
from collections import Counter
from pathlib import Path
from src.learning.production_execution import goal_catalog,order_goals
ROOT=Path('logs/roadmap');DATA=ROOT/'human-production-goals-02';prep=json.loads((DATA/'preparation.json').read_text())
records=[];binding={};ambiguous=Counter();all_commands=Counter();names=prep['names']
for item in prep['coverage']:
 g=item['game'];directory=next(Path(p).parent for p in prep['bindings'] if p.endswith(f'/{g}/dataset.json'))
 static=json.loads((directory/'static.json').read_text())['game_data'];catalog={a['ability_id']:a for a in static['abilities']};unit_names={u['unit_id']:u['name'] for u in static['units']};goals=goal_catalog(static,names)
 with gzip.open(directory/'examples.jsonl.gz','rt') as f: rows=list(map(json.loads,f))
 events=[]
 for row in rows:
  command=row['original_command']; own={u['tag']:u for u in row['observation']['units'] if u['alliance']==1}
  resolved=set()
  for tag in command['units']:
   if tag not in own:continue
   unit=dict(own[tag],orders=[dict(ability_id=command['ability'])]); matches=order_goals(unit,goals,catalog,unit_names)
   resolved.update(n for n,_ in matches)
  if len(resolved)==1:
   name=next(iter(resolved));events.append(dict(loop=row['action_loop'],source_sequence=row['source_sequence'],goal=name,units=command['units'],queue=command['queue']))
   all_commands[name]+=1
  elif resolved:ambiguous[str(command['ability'])]+=1
 records.append(dict(game=g,role=item['role'],commands=len(events),opening=events[:18]))
 for p in (directory/'examples.jsonl.gz',directory/'static.json'):binding[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(status='verified_descriptive_command_audit',rl=False,records=records,counts=dict(all_commands),ambiguous=dict(ambiguous),limitations=['Original issued commands are intentions; cancellations and rejected commands are not proven completed production.','Actor-unobserved commands are omitted from this descriptive mapping, not treated as negative intentions.'],bindings=binding)
for p in (Path(__file__),DATA/'preparation.json',Path('src/learning/production_execution.py')):report['bindings'][str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
(ROOT/'human-production-commitments-02.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],commands=sum(all_commands.values()),ambiguous=dict(ambiguous),openings={r['game']:[(round(e['loop']/22.4,2),e['goal']) for e in r['opening'][:8]] for r in records})),flush=True)
