"""Synthetic compact-encoder throughput; not human fitting or SC2 gameplay."""
import hashlib,json,time
from pathlib import Path
import numpy as np
from src.learning.entity_encoder import JointEntityEncoder
root=Path('logs/roadmap');static=root/'issued-timing-masked-01/issued-51574/static.json'
files=[Path(__file__),Path('src/learning/entity_encoder.py'),static]
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=hashes();data=json.loads(static.read_text())['game_data']
units=max(u['unit_id'] for u in data['units'])+1;abilities=max(a['ability_id'] for a in data['abilities'])+1
model=JointEntityEncoder(32,16,9,units,abilities,hidden=32,seed=1)
rng=np.random.default_rng(2);entities=rng.normal(0,.1,(200,32)).astype(np.float32)
types=rng.choice([18,45,48],200);orders=rng.choice([0,23,295],200)
scene=np.zeros(16,dtype=np.float32);history=rng.choice([1,16,23,524],32)
roles=np.zeros((32,9),dtype=np.float32)
parameters_before={k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in model.parameters.items()}
t=time.monotonic()
for _ in range(1000):
    context,encoded,cache=model.forward(entities,types,orders,scene,history,roles)
    gradients=model.backward(cache,np.ones(32,dtype=np.float32),np.ones_like(encoded)/200)
assert all(np.isfinite(v).all() for v in gradients.values())
assert parameters_before=={k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in model.parameters.items()}
assert hashes()==before
report={'status':'completed','scope':'Synthetic200entity/32feature/32history encoder forward+backward; no optimizer, complete policy, human fit or native performance claim',
        'files_before':before,'files_after':hashes(),'vocabulary':{'unit_slots':units,'ability_slots':abilities},'iterations':1000,
        'wall_seconds':time.monotonic()-t,'parameter_bytes':sum(p.nbytes for p in model.parameters.values()),
        'numeric_entity_payload_bytes':entities.nbytes,'categorical_entity_payload_bytes':types.nbytes+orders.nbytes,
        'parameters_unchanged':True,'new_downloads':False}
(root/'entity-encoder-smoke-01.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('files_before','files_after')}))
