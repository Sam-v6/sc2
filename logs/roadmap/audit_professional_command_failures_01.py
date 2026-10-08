"""Locate frozen imitation errors using the exact trainer input factory."""
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np

from src.learning.entity_examples import decode_command
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect

root=Path('logs/roadmap')
run=root/'joint-professional-fit-06'
configuration=json.loads((run/'configuration.json').read_text())
policy,_=JointEntityPolicy.load(run/'policy.npz')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
groups={}
for source in configuration['sources']:
    assert source['role'] in ('teaching','diagnostic')
    for path,expected in source['bindings'].items(): assert sha(Path(path))==expected
    directory=Path(source['dataset'])
    static=json.loads((directory/'static.json').read_text())['game_data']
    names={a['ability_id']:a.get('friendly_name','') for a in static['abilities']}
    examples,_=collect([directory],configuration['vocabulary'],spatial=True,missing_fields=True)
    for inputs,label,command,reason in examples:
        if label is None: continue
        name=names.get(command.ability,'')
        family='construction' if name.startswith('Build ') else 'other'
        key=f"{source['role']}:{family}:{command.ability}:{name}"
        group=groups.setdefault(key,dict(counts=Counter(),point_errors=[],gold_cell_errors=[],gold_cell_ranks=[],actor_counts=Counter(),actor_types=Counter()))
        counts=group['counts'];counts['commands']+=1
        ordinary=policy.predict(inputs)
        ability_oracle=policy.predict(inputs,ability=command.ability)
        human=set(label['actors'])
        types=inputs['encoder'][1]
        human_types=Counter(int(types[i]) for i in human)
        group['actor_counts'][len(human)]+=1
        group['actor_types'][str(sorted(human_types.items()))]+=1
        for label_name,prediction in [('ordinary',ordinary),('ability_oracle',ability_oracle)]:
            counts[label_name+'_actors']+=set(prediction['actors'])==human
            counts[label_name+'_actor_types_counts']+=Counter(int(types[i]) for i in prediction['actors'])==human_types
        counts['ordinary_ability']+=ordinary['ability']==command.ability
        if label['mode']==2:
            scores,_=policy._forward(inputs,ability=command.ability,actors=label['actors'],point=label['point'])
            index=int(np.argmax(scores['point']))
            # The gold-cell-conditioned offset is diagnostic; the point head
            # itself never depends on the explicit refinement cell.
            scores_pred,_=policy._forward(inputs,ability=command.ability,actors=label['actors'])
            predicted=inputs['world_points'][index]+scores_pred['offset']*inputs['point_radii'][index]
            gold_cell=inputs['world_points'][label['point']]+scores['offset']*inputs['point_radii'][label['point']]
            error=float(np.linalg.norm(predicted-command.target_point))
            gold_error=float(np.linalg.norm(gold_cell-command.target_point))
            group['point_errors'].append(error);group['gold_cell_errors'].append(gold_error)
            group['gold_cell_ranks'].append(int(np.sum(scores['point']>scores['point'][label['point']]))+1)
            counts['point_commands']+=1
            counts['point_cell_top1']+=index==label['point']
            counts['point_within_two']+=error<=2
            counts['gold_cell_within_two']+=gold_error<=2
        elif label['mode']==1:
            scores,_=policy._forward(inputs,ability=command.ability,actors=label['actors'])
            predicted=int(np.argmax(np.where(inputs['target_mask'],scores['target'],-np.inf)))
            counts['unit_target_commands']+=1
            counts['unit_target_oracle_top1']+=predicted==label['target']
    print(json.dumps(dict(game=directory.name,commands=len(examples))),flush=True)
summary={}
for key,group in groups.items():
    summary[key]=dict(counts=dict(group['counts']),actor_counts=dict(group['actor_counts']),actor_types=dict(group['actor_types']))
    for field in ('point_errors','gold_cell_errors','gold_cell_ranks'):
        values=group[field]
        if values:summary[key][field]=dict(mean=float(np.mean(values)),median=float(np.median(values)),p95=float(np.percentile(values,95)))
receipt=dict(scope='Frozen fit06 error localization. Human ability/actors/cell are explicit oracles only. Uses exact trainer.collect; no optimizer, reserved replay, native game or RL.',checkpoint_sha256=sha(run/'policy.npz'),helper_sha256=sha(Path(__file__)),configuration_sha256=sha(run/'configuration.json'),groups=summary)
path=root/'professional-command-failures-01.json'
assert not path.exists();path.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(output=str(path),groups=len(summary))))
