from pathlib import Path
import json,hashlib
import numpy as np
from src.learning.teacher_states import teacher_states
from src.learning.entity_examples import state_inputs
from src.learning.actor_selection import construction_products
from src.learning.entity_policy import JointEntityPolicy
P=Path('logs/roadmap');run=P/'joint-professional-fit-05';configuration=json.loads((run/'configuration.json').read_text());policy,_=JointEntityPolicy.load(run/'policy.npz');supports={};rows=0
for source in configuration['sources']:
 if source['role']!='teaching':continue
 directory=Path(source['dataset']);catalog=json.loads((directory/'static.json').read_text())['game_data'];products=construction_products(catalog)
 for row,state in teacher_states(directory):
  state=dict(state,decision_loop=row['action_loop']);inputs=state_inputs(state,*configuration['vocabulary'],products=products,missing_fields=True);encoder=inputs['encoder'];rows+=len(row['commands'])
  for name,array in [('entity',encoder[0]),('scene',encoder[3][None,:]),('history_roles',encoder[5])]:
   support=np.any(array!=0,axis=0);supports[name]=supports.get(name,np.zeros_like(support))|support
result={'scope':'Numeric feature support over all teaching replay rows only; no diagnostic/reserved data, optimizer or native game. Zero columns cannot have received data gradients.','teaching_commands':rows,'checkpoint_sha256':hashlib.sha256((run/'policy.npz').read_bytes()).hexdigest(),'features':{k:{'columns':len(v),'always_zero_columns':np.flatnonzero(~v).tolist(),'always_zero_weight_norm':float(np.linalg.norm(policy.encoder.parameters[k][~v]))} for k,v in supports.items()}}
(P/'professional-input-support-01.json').write_text(json.dumps(result,indent=2)+'\n');np.savez(P/'professional-input-support-01.npz',**supports);print(json.dumps(result,indent=2))
