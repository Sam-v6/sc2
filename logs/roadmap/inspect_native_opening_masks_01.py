"""Frozen-model initial-state availability ablation; no fitting or live play."""
import copy,gzip,json,hashlib
from pathlib import Path
import torch
from src.learning.teacher_states import teacher_states
from src.learning.entity_play import load_policy
from src.learning.entity_examples import state_inputs
from src.learning.actor_selection import construction_products
root=Path('logs/roadmap/type-status-native-inspection-01')
torch.set_num_threads(2)
torch.set_num_interop_threads(2)
source=Path('logs/roadmap/pro-demonstrations-07/920')
row,pro=next(teacher_states(source))
print('source_label',row['commands'], 'loop',pro['game_loop'],'missing',pro.get('unknown_fields'))
bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source/'static.json',source/'examples.jsonl.gz',Path(__file__),*root.glob('*/trace.jsonl.gz'),*root.glob('*/static.json'),*Path('logs/roadmap/type-status-imitation-01').glob('*/policy.npz')]}
result=dict(bindings=bindings,scope='Diagnostic input ablation of frozen initial states, no policy selection, fitting or RL',arms={})
for arm in ('baseline','type_status'):
 native=json.loads(next(gzip.open(root/arm/'trace.jsonl.gz','rt')))['observation']
 policy_path=Path('logs/roadmap/type-status-imitation-01')/arm/'policy.npz'
 before=hashlib.sha256(policy_path.read_bytes()).hexdigest()
 policy,_=load_policy(policy_path,'goal-first')
 static=json.loads((root/arm/'static.json').read_text())
 prostatic=json.loads((source/'static.json').read_text())
 cases={}
 for mask in (False,True):
  for timing in (False,True):
   state=copy.deepcopy(native)
   if mask: state.update(unknown_fields=pro['unknown_fields'],history_quality='event_slots')
   if timing: state['game_loop']=pro['game_loop']
   cases[f'native_source_mask_{mask}_source_time_{timing}']=(state,static)
 for mask in (False,True):
  state=copy.deepcopy(native)
  if mask: state.update(unknown_fields=pro['unknown_fields'],history_quality='event_slots')
  for unit in state['units']:
   for order in unit.get('orders',[]):
    if order.get('ability_id')==295: order['ability_id']=3666
  cases[f'native_canonical_gather_source_mask_{mask}']=(state,static)
 cases['source']=(pro,prostatic)
 records={}
 for name,(state,data) in cases.items():
  x=state_inputs(state,*policy.engine_vocabulary,products=construction_products(data['game_data']),missing_fields=True,terrain=data['terrain'])
  with torch.no_grad():
   logits,_=policy._forward(x)
   probabilities=torch.softmax(logits['ability'],dim=0)
   vals,inds=torch.topk(probabilities,3)
  records[name]=dict(decision=policy.predict(x),top_abilities=[dict(ability=int(i),probability=float(v)) for i,v in zip(inds,vals)],scv_probability=float(probabilities[524]))
 assert hashlib.sha256(policy_path.read_bytes()).hexdigest()==before
 result['arms'][arm]=records
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in bindings.items())
(root/'opening-mask-diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result['arms'],indent=2))
