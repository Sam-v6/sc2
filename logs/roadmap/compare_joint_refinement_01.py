import json
from pathlib import Path
import time
from collections import Counter

import numpy as np

from src.learning.entity_audit import audit_commands
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect, digest, validate_datasets

root=Path.cwd(); old=root/'logs/roadmap/joint-entity-fit-01'; new=root/'logs/roadmap/joint-entity-fit-02'
contract=json.loads((root/'logs/roadmap/joint-entity-fit-contract-02.json').read_text())
configuration=json.loads((new/'configuration.json').read_text())
report=json.loads((new/'report.json').read_text())
original=json.loads((old/'report.json').read_text())
assert report['status']=='completed' and report['bindings_unchanged']
assert report['optimizer_updates']==contract['expected_optimizer_updates']==44400
assert len(report['history'])==200 and all(row['commands']==3542 for row in report['history'])
assert digest(old/'policy.npz')==contract['baseline_checkpoint_sha256']==original['checkpoint_sha256']
assert digest(new/'policy.npz')==report['checkpoint_sha256']
old_policy,_=JointEntityPolicy.load(old/'policy.npz')
new_policy,metadata=JointEntityPolicy.load(new/'policy.npz')
assert not old_policy.refinement and new_policy.refinement
assert metadata['configuration']==configuration
paths={role:[Path(s['dataset']) for s in configuration['sources'] if s['role']==role] for role in ('teaching','diagnostic')}
assert validate_datasets(paths['teaching'],paths['diagnostic'])==configuration['sources']
assert all(digest(Path(path))==value for path,value in configuration['code_before'].items())
start=time.monotonic(); results={}
for role,directories in paths.items():
    examples,_=collect(directories,configuration['vocabulary'])
    results[role]={}
    for name,policy in (('baseline',old_policy),('refinement',new_policy)):
        audit=audit_commands(policy,examples)
        expected=original if name=='baseline' else report
        assert audit==expected['teaching' if role=='teaching' else 'validation']
        geometry=Counter(); groups=Counter()
        for inputs,label,command,exclusion in examples:
            prediction=policy.predict(inputs)
            predicted={inputs['tags'][i] for i in prediction['actors']}
            gold=set(command.units)
            groups['over_selected']+=int(len(predicted)>len(gold))
            groups['under_selected']+=int(len(predicted)<len(gold))
            groups['same_size_wrong_members']+=int(len(predicted)==len(gold) and predicted!=gold)
            groups['true_positive']+=len(predicted&gold)
            groups['false_positive']+=len(predicted-gold)
            groups['false_negative']+=len(gold-predicted)
            if label is not None and command.target_point is not None:
                scores=policy.scores(inputs,ability=command.ability,actors=label['actors'],point=label['point'])
                geometry['point_commands']+=1
                geometry['oracle_correct_cell']+=int(scores['point'].argmax()==label['point'])
                point=inputs['world_points'][label['point']]+scores['offset']*inputs['point_radii'][label['point']]
                geometry['human_cell_offset_within_one_tile']+=int(np.linalg.norm(point-command.target_point)<=1)
        results[role][name]=dict(audit=audit,actor_membership=dict(groups),spatial_oracle=dict(geometry))
        print(json.dumps(dict(split=role,model=name,ordinary=audit['predicted'],actor_membership=dict(groups),spatial_oracle=dict(geometry))),flush=True)
assert validate_datasets(paths['teaching'],paths['diagnostic'])==configuration['sources']
assert digest(old/'policy.npz')==contract['baseline_checkpoint_sha256'] and digest(new/'policy.npz')==report['checkpoint_sha256']
assert all(digest(Path(path))==value for path,value in configuration['code_before'].items())
t=results['teaching']['refinement']['audit']; n=t['commands']; gate=contract['teaching_gate']
passed=all(t['predicted'][key]/n>=gate[key+'_fraction'] for key in ('ability','actors','complete'))
receipt=dict(status='verified',results=results,refinement_teaching_gate_passed=passed,bindings_unchanged=True,checkpoint_sha256=report['checkpoint_sha256'],baseline_checkpoint_sha256=contract['baseline_checkpoint_sha256'],seconds=time.monotonic()-start,reserved_replays_opened=False,rl_run=False,scope='Reloaded checkpoints, exact audit regeneration and same-cohort comparison; cell offset diagnostics explicitly supply human cell. Combined changes cannot be attributed separately; no native evidence.')
(root/'logs/roadmap/joint-refinement-comparison-01.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(teaching_gate_passed=passed,seconds=receipt['seconds'])),flush=True)
