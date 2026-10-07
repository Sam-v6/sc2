"""Locate actor membership versus ranking failures on the frozen small set."""
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np

from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect

root=Path('logs/roadmap/professional-small-set-actor-geometry-01')
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
contract=read(root/'contract.json')
report=read(root/'report.json')
assert sha(root/'policy.npz')==report['checkpoint_sha256']
assert sha(root/'contract.json')==report['contract_sha256']
configuration_path=Path('logs/roadmap/joint-professional-fit-05/configuration.json')
assert sha(configuration_path)==contract['parent_configuration_sha256']
configuration=read(configuration_path)
for p,h in contract['code_sha256'].items():
    assert sha(Path(p))==h
rows={}
for source in contract['sources']:
    path=Path(source['dataset'])
    assert path.name not in ('774','848','51483','51886')
    for p,h in source['bindings'].items():assert sha(Path(p))==h
    rows[path.name]=collect([path],configuration['vocabulary'],spatial=True,missing_fields=True)[0]
policy,_=JointEntityPolicy.load(root/'policy.npz')
counts=Counter()
failures=[]
for selected in contract['selected']:
    inputs,label,command,reason=rows[selected['game']][selected['row']]
    assert label is not None and command.ability==selected['ability']
    predicted=policy.predict(inputs)
    scores,_=policy._forward(inputs,ability=command.ability)
    gold=set(label['actors'])
    actual=set(predicted['actors'])
    eligible=np.flatnonzero(inputs['actor_mask'])
    ranked=eligible[np.argsort(-scores['actor'][eligible],kind='stable')]
    # The human group size is explicitly supplied here as a diagnostic oracle.
    top=set(int(i) for i in ranked[:len(gold)])
    types=inputs['encoder'][1]
    types_of=lambda indices:Counter(int(types[i]) for i in indices)
    counts.update(dict(commands=1,exact=actual==gold,correct_count=len(actual)==len(gold),
                       correct_type_counts=types_of(actual)==types_of(gold),
                       human_count_oracle_exact=top==gold))
    if actual!=gold:
        negatives=[int(i) for i in eligible if int(i) not in gold]
        failures.append(dict(**selected,gold_count=len(gold),predicted_count=len(actual),
                             gold_types=dict(types_of(gold)),predicted_types=dict(types_of(actual)),
                             human_count_oracle_exact=top==gold,
                             min_gold_logit=float(min(scores['actor'][list(gold)])),
                             max_negative_logit=float(max(scores['actor'][negatives])) if negatives else None,
                             gold_ranks=[int(np.flatnonzero(ranked==i)[0])+1 for i in sorted(gold)]))
assert counts['exact']==report['final']['predicted']['actors']
receipt=dict(checkpoint_sha256=sha(root/'policy.npz'),contract_sha256=sha(root/'contract.json'),
             helper_sha256=sha(Path(__file__)),counts=dict(counts),failures=failures,
             scope='Frozen selected teaching rows only. Human group-size oracle diagnoses ranking; it is not deployed. No fitting, other replay predictions, native game or RL.')
path=root/'actor-diagnosis.json'
assert not path.exists()
path.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
