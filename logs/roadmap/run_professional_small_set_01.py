"""One bounded, human-teaching-only small-set learning diagnostic."""
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np

from src.learning.entity_audit import audit_commands
from src.learning.entity_encoder import JointEntityEncoder
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import Adam, collect, validate_datasets

root = Path('logs/roadmap')
output = root/'professional-small-set-01'
assert not output.exists()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
parent = root/'joint-professional-fit-05/configuration.json'
configuration = json.loads(parent.read_text())
sources = [s for s in configuration['sources'] if s['role']=='teaching']
paths = [Path(s['dataset']) for s in sources]
assert len(paths)==9 and not any(p.name in ('774','848','51483','51886') for p in paths)
current_sources = validate_datasets(paths,[],missing_fields=True)
assert [s['replay_sha256'] for s in current_sources] == [s['replay_sha256'] for s in sources]
for source in sources:
    for p,h in source['bindings'].items():
        assert sha(Path(p))==h
code = json.loads((root/'joint-professional-fit-07/configuration.json').read_text())['code_before']
for p,h in code.items():
    assert sha(Path(p))==h
groups = defaultdict(list)
for path in paths:
    examples,_ = collect([path],configuration['vocabulary'],spatial=True,missing_fields=True)
    for row,example in enumerate(examples):
        if example[1] is not None:
            groups[example[2].ability].append((path.name,row,example))
rng = np.random.default_rng(8100)
selected = []
for ability in sorted(groups):
    indices = rng.permutation(len(groups[ability]))[:2]
    selected.extend(groups[ability][i] for i in indices)
rows = [example for _,_,example in selected]
assert len(rows)>0 and len(rows)<=2*len(groups)
sample = rows[0][0]['encoder']
policy = JointEntityPolicy(JointEntityEncoder(sample[0].shape[1],len(sample[3]),sample[5].shape[1],
                           configuration['vocabulary'][0],configuration['vocabulary'][1],
                           hidden=32,seed=8100,role_pooling=True),configuration['delays'],seed=8101,
                           refinement=True,actor_cutoff=True,missing_fields=True,
                           spatial_features=rows[0][0]['point_features'].shape[1],actor_relative_points=True)
contract = dict(parent_configuration_sha256=sha(parent),sources=current_sources,code_sha256=code,
                helper_sha256=sha(Path(__file__)),seed=8100,epochs=200,batch_size=16,rate=.001,
                optimizer_seconds_max=120,ability_importance=False,context_layer_norm=False,
                selected=[dict(game=game,row=row,ability=example[2].ability) for game,row,example in selected],
                complete_min=math.ceil(.9*len(rows)),ability_min=math.ceil(.95*len(rows)),
                scope='Small-set memorization diagnostic only; human teaching examples; no held-out predictions, native games or RL.')
output.mkdir()
(output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
initial = audit_commands(policy,rows)
optimizer = Adam(policy,.001)
shuffle = np.random.default_rng(8102)
history=[]
start=time.monotonic()
status='completed'
for epoch in range(200):
    order=shuffle.permutation(len(rows))
    losses=[]
    for offset in range(0,len(rows),16):
        if time.monotonic()-start>=120:
            status='wall_bound'
            break
        batch=[(rows[i][0],rows[i][1]) for i in order[offset:offset+16]]
        losses.append(optimizer.step(batch))
    history.append(dict(epoch=epoch+1,updates=optimizer.updates,mean_loss=float(np.mean(losses)) if losses else None))
    if (epoch+1)%25==0:
        print(json.dumps(history[-1]),flush=True)
    if status!='completed':
        break
seconds=time.monotonic()-start
policy.save(output/'policy.npz',dict(contract=contract,status=status,updates=optimizer.updates))
checkpoint=sha(output/'policy.npz')
final=audit_commands(policy,rows)
for p,h in code.items():
    assert sha(Path(p))==h
assert validate_datasets(paths,[],missing_fields=True)==current_sources
assert sha(output/'policy.npz')==checkpoint
gates=dict(complete=final['predicted']['complete']>=contract['complete_min'],
           ability=final['predicted']['ability']>=contract['ability_min'])
receipt=dict(status=status,commands=len(rows),abilities=len(groups),history=history,
             optimizer_updates=optimizer.updates,optimizer_seconds=seconds,initial=initial,final=final,
             checkpoint_sha256=checkpoint,contract_sha256=sha(output/'contract.json'),
             bindings_unchanged=True,gates=gates,all_gates_passed=status=='completed' and all(gates.values()),
             promoted=False,reserved_predictions=0,diagnostic_predictions=0,native_games=0,rl_updates=0)
(output/'report.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('history','initial','final')},indent=2))
print(json.dumps(final,indent=2))
