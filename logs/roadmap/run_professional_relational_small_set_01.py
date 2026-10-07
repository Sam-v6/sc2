"""Matched CPU-backend human-only comparison, frozen before optimizer updates."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch

from src.learning.entity_audit import audit_commands
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_torch_encoder import TorchEntityEncoder
from src.learning.entity_train import Adam, collect, validate_datasets

root=Path('logs/roadmap')
output=root/'professional-small-set-relational-01'
assert not output.exists() and os.environ.get('CUDA_VISIBLE_DEVICES')==''
torch.set_num_threads(2)
assert not torch.cuda.is_initialized()
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=root/'professional-small-set-01'
old_contract=read(old/'contract.json')
old_report=read(old/'report.json')
assert sha(old/'policy.npz')==old_report['checkpoint_sha256']
assert sha(old/'contract.json')==old_report['contract_sha256']
configuration_path=root/'joint-professional-fit-05/configuration.json'
assert sha(configuration_path)==old_contract['parent_configuration_sha256']
configuration=read(configuration_path)
sources=old_contract['sources']
paths=[Path(s['dataset']) for s in sources]
assert len(paths)==9 and not any(p.name in ('774','848','51483','51886') for p in paths)
assert validate_datasets(paths,[],missing_fields=True)==sources
selected={}
for source in sources:
    for p,h in source['bindings'].items():assert sha(Path(p))==h
    directory=Path(source['dataset'])
    examples,_=collect([directory],configuration['vocabulary'],spatial=True,missing_fields=True)
    for record in old_contract['selected']:
        if record['game']==directory.name:
            example=examples[record['row']]
            assert example[1] is not None and example[2].ability==record['ability']
            selected[(record['game'],record['row'])]=example
rows=[selected[(r['game'],r['row'])] for r in old_contract['selected']]
assert len(rows)==62
sample=rows[0][0]['encoder']
def make_policy(attention):
    return JointEntityPolicy(TorchEntityEncoder(sample[0].shape[1],len(sample[3]),sample[5].shape[1],
                             configuration['vocabulary'][0],configuration['vocabulary'][1],
                             hidden=32,seed=8100,role_pooling=True,relational_attention=attention),
                             configuration['delays'],seed=8101,refinement=True,actor_cutoff=True,
                             missing_fields=True,spatial_features=rows[0][0]['point_features'].shape[1],
                             actor_relative_points=True)
policies={name:make_policy(attention) for name,attention in [('baseline',False),('attention',True)]}
initial={name:audit_commands(policy,rows) for name,policy in policies.items()}
assert initial['baseline']==initial['attention']
code={p:sha(Path(p)) for p in read(root/'joint-professional-fit-07/configuration.json')['code_before']}
extra=Path('src/learning/entity_torch_encoder.py').absolute()
code[str(extra)]=sha(extra)
contract=dict(sources=sources,selected=old_contract['selected'],original_contract_sha256=sha(old/'contract.json'),
              original_checkpoint_sha256=sha(old/'policy.npz'),code_sha256=code,helper_sha256=sha(Path(__file__)),
              runtime=dict(interpreter=sys.executable,torch=torch.__version__,numpy=np.__version__,
                           torch_module=torch.__file__,torch_module_sha256=sha(Path(torch.__file__)),
                           threads=2,device='cpu',cuda_initialized=False),
              epochs=200,expected_updates=800,batch_size=16,rate=.001,seed=8100,
              optimizer_seconds_max=120,actor_geometry=False,context_layer_norm=False,ability_importance=False,
              gates=dict(complete_min=56,actors_min=56,ability_min=62,target_min=59),
              scope='Matched CPU backend with/without relational attention; exact selected human teaching rows. No other replay predictions, native game, GPU or RL.')
output.mkdir()
(output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
reports={}
for name,policy in policies.items():
    run=output/name; run.mkdir()
    optimizer=Adam(policy,.001); shuffle=np.random.default_rng(8102)
    history=[]; start=time.monotonic(); status='completed'
    for epoch in range(200):
        order=shuffle.permutation(len(rows)); losses=[]
        for offset in range(0,len(rows),16):
            if time.monotonic()-start>=120:
                status='wall_bound'; break
            losses.append(optimizer.step([(rows[i][0],rows[i][1]) for i in order[offset:offset+16]]))
        history.append(dict(epoch=epoch+1,updates=optimizer.updates,mean_loss=float(np.mean(losses)) if losses else None))
        if (epoch+1)%25==0:print(json.dumps(dict(run=name,**history[-1])),flush=True)
        if status!='completed':break
    seconds=time.monotonic()-start
    policy.save(run/'policy.npz',dict(contract=contract,status=status,updates=optimizer.updates))
    checkpoint=sha(run/'policy.npz')
    final=audit_commands(policy,rows)
    assert sha(run/'policy.npz')==checkpoint
    for p,h in code.items():assert sha(Path(p))==h
    assert validate_datasets(paths,[],missing_fields=True)==sources
    assert not torch.cuda.is_initialized()
    report=dict(status=status,initial=initial[name],final=final,history=history,optimizer_updates=optimizer.updates,
                optimizer_seconds=seconds,checkpoint_sha256=checkpoint,bindings_unchanged=True)
    (run/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    reports[name]=report
    print(json.dumps(dict(run=name,status=status,updates=optimizer.updates,seconds=seconds,predicted=final['predicted'])),flush=True)
g=contract['gates']; current=reports['attention']['final']['predicted']
gates=dict(complete=current['complete']>=g['complete_min'],actors=current['actors']>=g['actors_min'],
           ability=current['ability']>=g['ability_min'],target=current['target']>=g['target_min'])
receipt=dict(status='completed' if all(r['status']=='completed' for r in reports.values()) else 'wall_bound',
             contract_sha256=sha(output/'contract.json'),gates=gates,
             all_gates_passed=all(r['status']=='completed' for r in reports.values()) and all(gates.values()),
             predicted={name:r['final']['predicted'] for name,r in reports.items()},
             checkpoint_sha256={name:r['checkpoint_sha256'] for name,r in reports.items()},
             promoted=False,native_games=0,reserved_predictions=0,diagnostic_predictions=0,rl_updates=0)
(output/'comparison.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
