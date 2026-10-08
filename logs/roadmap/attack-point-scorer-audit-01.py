"""Audit the fixed sampler and full-grid training fit without retraining."""
import ast
import hashlib
import json
from pathlib import Path
import numpy as np
from src.learning.global_imitation import global_features, coordinate_signs
from src.learning.imitation import FactorPolicy
from src.learning.actor_selection import group_features
from src.learning.spatial_construction import candidate_features, decode_terrain, spatial_candidates
from src.learning.teacher_states import teacher_states, own_actors
root=Path('logs/roadmap');out=root/'attack-point-scorer-01'
report=json.loads((out/'report.json').read_text())
for file,binding in report['files_before'].items():assert hashlib.sha256(Path(file).read_bytes()).hexdigest()==binding['sha256']
assert hashlib.sha256((out/'points.npz').read_bytes()).hexdigest()==report['checkpoint_sha256']
macro=FactorPolicy.load(root/'imitation-prefix-240-01/policy.npz')
policy=FactorPolicy.load(out/'points.npz')
structures=json.loads((root/'spatial-prefix-240-01/report.json').read_text())['structure_types']
vocab=report['selected_type_vocabulary']
script=root/'attack-point-scorer-01.py'
tree=ast.parse(script.read_text());functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('rows','features')]
exec(compile(ast.Module(body=functions,type_ignores=[]),str(script),'exec'))
rng=np.random.default_rng(5007);results=[];conflicts=0;local_conflicts=0;commands=0
for directory in map(Path,report['train']):
    errors=[]
    for state,group,origin,context,terrain,truth,_ in rows(directory):
        points=spatial_candidates(state['map_size'],0,spacing=2)
        distances=np.linalg.norm(points-truth,axis=1);positive=int(distances.argmin())
        eligible=np.flatnonzero(np.arange(len(points))!=positive)
        global_neg=rng.choice(eligible,32,replace=False)
        local=np.argsort(distances)[1:65];local_conflicts+=int(positive in local)
        local_neg=rng.choice(local,16,replace=False)
        center=np.asarray([u['position'][:2] for u in group]).mean(axis=0)
        near=np.argsort(np.linalg.norm(points-center,axis=1));near=near[near!=positive][:256]
        actor_neg=rng.choice(near,16,replace=False)
        conflicts+=int(positive in np.r_[global_neg,local_neg,actor_neg]);commands+=1
        logits=policy.predict(features(state,group,origin,context,points,terrain))['ability']
        chosen=points[int((logits[:,1]-logits[:,0]).argmax())]
        errors.append(float(np.linalg.norm(chosen-truth)))
    results.append({'dataset':str(directory),'commands':len(errors),'within_2_accuracy':float(np.mean(np.asarray(errors)<=2)),
                    'mean_error_tiles':float(np.mean(errors)),'median_error_tiles':float(np.median(errors))})
# Reproduce the reported edge case separately; it is not training data.
points=spatial_candidates([128,128],0,spacing=2);d=np.linalg.norm(points-[1,1],axis=1);positive=int(d.argmin());old=np.argsort(d)[1:65]
fixed=np.argsort(d);fixed=fixed[fixed!=positive][:64]
assert positive in old and positive not in fixed
for file,binding in report['files_before'].items():assert hashlib.sha256(Path(file).read_bytes()).hexdigest()==binding['sha256']
receipt={'status':'completed_without_fitting','commands':commands,'positive_in_local_pool':local_conflicts,'sampled_label_conflicts':conflicts,
    'edge_case':{'truth':[1,1],'positive':positive,'old_negative_pool_contains_positive':bool(positive in old),'explicit_exclusion_removes_positive':bool(positive not in fixed)},
    'training_full_grid':results,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'limitation':'Original experiment source preserved; tied-distance sampler must explicitly exclude the positive before reuse.'}
(out/'training-and-sampler-audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
