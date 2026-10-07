"""Check ability identity with each replay excluded from reference mappings."""
import ast
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import mpyq
from src.learning.issued_commands import target_matches
from src.learning.replay_extract import load_protocol
root=Path('logs/roadmap')
original=json.loads((root/'issued-ability-audit-01.json').read_text())
for file,sha in original['files'].items():assert hashlib.sha256(Path(file).read_bytes()).hexdigest()==sha
source=root/'issued-ability-audit-01.py'
functions=[n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('key','load')]
exec(compile(ast.Module(body=functions,type_ignores=[]),str(source),'exec'))
results=[]
for entry in original['games']:
 directory=Path(entry['dataset']);events,_,issued,catalog,_=load(directory)
 references={tuple(m['event_key']):{int(a):[s for s in rows if s['dataset']!=str(directory)] for a,rows in m['canonical_abilities'].items()} for m in original['mappings']}
 references={k:{a:rows for a,rows in choices.items() if rows} for k,choices in references.items()}
 result={'dataset':str(directory),'checked':0,'mismatches':[],'no_independent_reference':0,'ambiguous':[],'ability_resolved_target_ambiguities':[]}
 for row in issued:
  for c in row['commands']:
   candidates=[e for e in events[row['action_loop']] if target_matches(c,e)]
   canonical=catalog[c['ability']].get('remaps_to_ability_id') or c['ability']
   supported=[(e,references.get(key(e),{})) for e in candidates if len(references.get(key(e),{}))==1]
   matching=[e for e,ref in supported if canonical in ref]
   if len(candidates)==1:
    if len(supported)!=1:result['no_independent_reference']+=1;continue
    result['checked']+=1
    if not matching:result['mismatches'].append({'loop':row['action_loop'],'raw_ability':c['ability'],'canonical':canonical,'event_key':key(candidates[0]),'expected':list(supported[0][1])})
   elif len(matching)==1:
    result['checked']+=1
    result['ability_resolved_target_ambiguities'].append({'loop':row['action_loop'],'raw_ability':c['ability'],'event_key':key(matching[0]),'target_only_candidates':len(candidates)})
   else:result['ambiguous'].append({'loop':row['action_loop'],'raw_ability':c['ability'],'target_only_candidates':len(candidates),'ability_matching_candidates':len(matching)})
 results.append(result)
for file,sha in original['files'].items():assert hashlib.sha256(Path(file).read_bytes()).hexdigest()==sha
report={'status':'completed_without_relabeling','scope':'leave-one-replay-out empirical ability mapping; no replay validates against its own reference events',
 'games':results,'files':original['files'],'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'reference_audit_sha256':hashlib.sha256((root/'issued-ability-audit-01.json').read_bytes()).hexdigest(),
 'limitations':'Empirical same-build consistency is not an authoritative complete protocol table. Unreferenced abilities and ambiguity remain explicit. Teaching data unchanged.'}
(root/'issued-ability-audit-crossgame-01.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(results,indent=2))
