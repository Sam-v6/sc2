"""Corrected point-head diagnostic using each trainer's actual input factory."""
import hashlib
import json
from pathlib import Path

import numpy as np

from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect

root = Path('logs/roadmap')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
results = {}
for number in (3,4,5,6):
    run = root / f'joint-professional-fit-{number:02}'
    configuration = json.loads((run/'configuration.json').read_text())
    diagnostic = [source for source in configuration['sources'] if source['role']=='diagnostic']
    assert len(diagnostic)==1 and Path(diagnostic[0]['dataset']).name=='774'
    for path,expected in diagnostic[0]['bindings'].items():
        assert sha(Path(path))==expected
    policy,_ = JointEntityPolicy.load(run/'policy.npz')
    examples,_ = collect([Path(diagnostic[0]['dataset'])],configuration['vocabulary'],
                         spatial=True,missing_fields=True)
    errors = {'ordinary':[], 'ability_actor_oracle':[]}
    modes = dict.fromkeys(errors,0)
    for inputs,label,command,reason in examples:
        if label is None or label['mode']!=2:
            continue
        for name in errors:
            conditioning = {} if name=='ordinary' else dict(ability=label['ability'],actors=label['actors'])
            scores,_ = policy._forward(inputs,**conditioning)
            index = int(np.argmax(scores['point']))
            point = inputs['world_points'][index]+scores['offset']*inputs['point_radii'][index]
            errors[name].append(float(np.linalg.norm(point-np.asarray(command.target_point))))
            modes[name] += int(np.argmax(scores['mode'])==2)
    results[str(number)] = dict(checkpoint_sha256=sha(run/'policy.npz'),
                                 diagnostic_bindings=diagnostic[0]['bindings'],
                                 errors={name:dict(commands=len(values),mean_tiles=float(np.mean(values)),
                                                  p95_tiles=float(np.percentile(values,95)),
                                                  within_two_tiles=sum(v<=2 for v in values),mode_correct=modes[name])
                                         for name,values in errors.items()})
receipt = dict(scope='Supersedes helper01 point metrics: it omitted construction_products supplied by trainer. Uses trainer.collect and every gold point row including mode mistakes. Reused774 only, no fitting/native/RL/reserved games.',
               helper_sha256=sha(Path(__file__)),results=results)
path = root/'professional-point-heads-corrected-02.json'
assert not path.exists()
path.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
