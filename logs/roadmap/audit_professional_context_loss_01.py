"""Read-only, component-checked human-teaching loss and per-game copying."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from src.learning.entity_audit import audit_commands
from src.learning.entity_examples import replay_examples
from src.learning.entity_policy import JointEntityPolicy, categorical_loss
from src.learning.entity_train import DELAYS

parser = argparse.ArgumentParser()
parser.add_argument('checkpoint',type=Path)
parser.add_argument('output',type=Path)
args = parser.parse_args()
assert not args.output.exists()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
configuration = json.loads(Path('logs/roadmap/joint-professional-fit-05/configuration.json').read_text())
policy, _ = JointEntityPolicy.load(args.checkpoint)
assert not policy.actor_count
totals = dict(ability=0.,actor=0.,mode=0.,queue=0.,delay=0.,target=0.,point_offset=0.)
count = 0
games = {}
max_discrepancy = 0.
for source in configuration['sources']:
    if source['role']!='teaching':
        continue
    for path, expected in source['bindings'].items():
        assert sha(Path(path))==expected
    directory = Path(source['dataset'])
    examples = list(replay_examples(directory,*configuration['vocabulary'],DELAYS,
                                    spatial=True,missing_fields=True))
    for inputs,label,command,reason in examples:
        if label is None:
            continue
        scores, cache = policy._forward(inputs,label['ability'],tuple(label['actors']),
                                       point=label['point'] if label['mode']==2 else None)
        components = dict.fromkeys(totals,0.)
        mask = np.arange(len(scores['ability']))>0
        components['ability'] = categorical_loss(scores['ability'],label['ability'],mask)[0]
        eligible = np.flatnonzero(inputs['actor_mask'])
        labels = np.isin(eligible,label['actors']).astype(float)
        logits = scores['actor'][eligible]
        components['actor'] = float(np.mean(np.logaddexp(0,logits)-labels*logits))
        if policy.refinement:
            components['actor'] += float(np.log(np.exp(logits-logits.max()).sum())+logits.max()
                                          -logits[labels.astype(bool)].mean()-np.log(labels.sum()))
        for name in ('mode','queue','delay'):
            if (name=='delay' and label['delay'] is None) or (name=='queue' and label['mode']==3):
                continue
            components[name] = categorical_loss(scores[name],int(label[name]))[0]
        if label['mode'] in (1,2):
            name = 'target' if label['mode']==1 else 'point'
            mask = inputs['target_mask'] if name=='target' else None
            components['target'] = categorical_loss(scores[name],label[name],mask)[0]
            if name=='point':
                error = scores['offset']-np.asarray(label['offset'])
                radii = np.asarray(inputs['point_radii'])[label['point']]
                components['point_offset'] = float(.5*np.square(error*radii).sum())
        expected,_ = policy.loss_and_gradients(inputs,label)
        discrepancy = abs(sum(components.values())-expected)
        max_discrepancy = max(max_discrepancy,discrepancy)
        assert discrepancy<1e-5,(directory,command,discrepancy)
        for name,value in components.items():
            totals[name] += value
        count += 1
    audit = audit_commands(policy,examples)
    games[directory.name] = dict(commands=len(examples),representable=audit['representable'],
                                predicted=audit['predicted'])
    print(json.dumps(dict(game=directory.name,complete=audit['predicted']['complete'],
                          representable_loss_rows=count)),flush=True)
means = {k:v/count for k,v in totals.items()}
receipt = dict(checkpoint_sha256=sha(args.checkpoint),helper_sha256=sha(Path(__file__)),
               baseline_configuration_sha256=sha(Path('logs/roadmap/joint-professional-fit-05/configuration.json')),
               representable_loss_rows=count,component_means=means,
               total_mean=sum(means.values()),max_component_sum_discrepancy=max_discrepancy,
               teaching_games=games,
               scope='Frozen nine human teaching games only; components verified against actual loss_and_gradients on every representable command. No optimizer, diagnostic/reserved predictions, native game or RL.')
args.output.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
