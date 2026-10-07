from pathlib import Path
from collections import Counter
import hashlib,json
import numpy as np
from src.learning.entity_examples import replay_examples,decode_command
from src.learning.entity_train import DELAYS
root=Path('logs/roadmap/pro-demonstrations-04');results=[]
for idx in (294,774,870):
 directory=root/str(idx);counts=Counter()
 for inputs,label,command,reason in replay_examples(directory,1970,3801,296,DELAYS,spatial=True,missing_fields=True):
  assert np.isfinite(inputs['encoder'][0]).all()
  assert np.isfinite(inputs['point_features']).all()
  counts['commands']+=1
  if reason:counts[reason]+=1
  else:
   assert decode_command(dict(ability=label['ability'],actors=label['actors'],mode=label['mode'],queue=label['queue'],target=label.get('target',0),point=label.get('point',0),offset=label.get('offset',[0,0])),inputs)==command
   counts['representable']+=1
 receipt=json.loads((directory/'dataset.json').read_text())
 for group in ('source_bindings','code_bindings'):
  for name,expected in receipt[group].items():
   assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==expected
 import gzip
 with gzip.open(directory/'examples.jsonl.gz','rt') as stream:
  for row in map(json.loads,stream):
   state=row['observation']
   assert state['game_loop']==row['action_loop']
   assert len(row['commands'])==1
   assert all(c['game_loop']<=row['action_loop'] for c in state['recent_commands'])
   assert 'upgrade_absence' in state['unknown_fields']['world']
   assert state['unmapped_own_upgrades']

 assert counts['commands']==receipt['issued_command_audit']['matched_issued_commands']
 result=dict(idx=idx,counts=dict(counts),resource_mappings=len(receipt['source_resource_mappings']),own_type_checks=receipt['own_type_checks']);results.append(result);print(result,flush=True)
paths=[Path(__file__),*[d/n for d in (root/str(i) for i in (294,774,870)) for n in ('dataset.json','static.json','examples.jsonl.gz')]]
out=dict(records=results,optimizer_updates=0,training_eligible=False,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
Path('logs/roadmap/pro-preconverted-probe-01/imported-examples-verification-04.json').write_text(json.dumps(out,indent=2)+'\n')
