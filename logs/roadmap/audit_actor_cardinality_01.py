import json
from pathlib import Path
from collections import Counter
import numpy as np
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect, digest
root=Path.cwd(); directory=root/'logs/roadmap/joint-entity-fit-03'
c=json.loads((directory/'configuration.json').read_text()); r=json.loads((directory/'report.json').read_text())
assert r['status']=='completed' and r['bindings_unchanged']
policy,_=JointEntityPolicy.load(directory/'policy.npz')
bindings={str(p):digest(p) for p in [directory/'policy.npz',directory/'configuration.json',Path(__file__),*[Path(p) for p in c['code_before']]]}
assert bindings[str(directory/'policy.npz')]==r['checkpoint_sha256']
results={}
for role in ('teaching','diagnostic'):
 total=Counter();sizes={}
 for source in c['sources']:
  if source['role']!=role: continue
  examples,_=collect([Path(source['dataset'])],c['vocabulary'])
  for inputs,label,command,exclusion in examples:
   if label is None: total['excluded']+=1;continue
   gold=set(label['actors']);eligible=np.flatnonzero(inputs['actor_mask']);k=len(gold)
   scores=policy.scores(inputs,ability=command.ability)['actor']
   ranked=eligible[np.argsort(-scores[eligible],kind='stable')]
   threshold=set(i for i in eligible if scores[i]>=0)
   if not threshold: threshold={ranked[0]}
   counts=sizes.setdefault(str(k),Counter());counts['commands']+=1
   counts['human_ability_threshold_exact']+=int(threshold==gold)
   counts['human_ability_and_group_size_topk_exact']+=int(set(ranked[:k])==gold)
   counts['over_selected']+=int(len(threshold)>k)
   counts['under_selected']+=int(len(threshold)<k)
   counts['same_size_wrong_members']+=int(len(threshold)==k and threshold!=gold)
   total.update(counts={}) if False else None
   total['commands']+=1
   for key in ('human_ability_threshold_exact','human_ability_and_group_size_topk_exact','over_selected','under_selected','same_size_wrong_members'):
    total[key]+=int({'human_ability_threshold_exact':threshold==gold,'human_ability_and_group_size_topk_exact':set(ranked[:k])==gold,'over_selected':len(threshold)>k,'under_selected':len(threshold)<k,'same_size_wrong_members':len(threshold)==k and threshold!=gold}[key])
 results[role]=dict(total=dict(total),group_sizes={k:dict(v) for k,v in sizes.items()})
assert bindings=={p:digest(Path(p)) for p in bindings}
receipt=dict(status='verified',results=results,bindings=bindings,scope='Human ability and optional exact human group size supplied only as oracle diagnostics. No changed predictor, native game, fit, reserved replay or RL.')
(root/'logs/roadmap/actor-cardinality-audit-01.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({role:result['total'] for role,result in results.items()}))
