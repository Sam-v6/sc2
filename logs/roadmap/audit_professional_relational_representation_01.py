"""Locate actor membership versus ranking failures on the frozen small set."""
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np

from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect

root=Path('logs/roadmap/professional-small-set-relational-01/attention')
experiment=root.parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
contract=read(experiment/'contract.json')
comparison=read(experiment/'comparison.json')
assert sha(experiment/'contract.json')==comparison['contract_sha256']
report=read(root/'report.json')
assert sha(root/'policy.npz')==report['checkpoint_sha256']
assert report['status']=='completed' and report['optimizer_updates']==800
assert report['bindings_unchanged']
assert len(report['history'])==200
assert all(r['updates']==4*r['epoch'] for r in report['history'])
assert report['optimizer_seconds']<contract['optimizer_seconds_max']
assert report['initial']==read(experiment/'baseline/report.json')['initial']
configuration_path=Path('logs/roadmap/joint-professional-fit-05/configuration.json')
original=read(Path('logs/roadmap/professional-small-set-01/contract.json'))
assert sha(configuration_path)==original['parent_configuration_sha256']
assert contract['selected']==original['selected']
assert sha(Path(contract['runtime']['torch_module']))==contract['runtime']['torch_module_sha256']
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
    scores,cache=policy._forward(inputs,ability=command.ability)
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
        detail={}
        if len(gold)==1:
            g=next(iter(gold)); a=int(ranked[0])
            raw,types_,orders_,*_=inputs['encoder']
            p=policy.encoder.parameters
            projection=raw @ p['entity']+p['types'][types_]+p['abilities'][orders_]+p['entity_bias']
            detail=dict(gold_index=g,top_index=a,same_type=bool(types_[g]==types_[a]),
                        same_first_order=bool(orders_[g]==orders_[a]),
                        numeric_l2=float(np.linalg.norm(raw[g]-raw[a])),
                        changed_numeric_columns=np.flatnonzero(raw[g]!=raw[a]).tolist(),
                        base_embedding_l2=float(np.linalg.norm(np.tanh(projection[g])-np.tanh(projection[a]))),
                        relational_embedding_l2=float(np.linalg.norm(cache['entities'][g]-cache['entities'][a])),
                        position_distance_tiles=float(np.linalg.norm(inputs['entity_positions'][g]-inputs['entity_positions'][a])),
                        gold_base_saturated_fraction=float(np.mean(np.abs(np.tanh(projection[g]))>.99)),
                        top_base_saturated_fraction=float(np.mean(np.abs(np.tanh(projection[a]))>.99)),
                        gold_minus_top_logit=float(scores['actor'][g]-scores['actor'][a]))
        failures.append(dict(**selected,representation=detail,gold_count=len(gold),predicted_count=len(actual),
                             gold_types=dict(types_of(gold)),predicted_types=dict(types_of(actual)),
                             human_count_oracle_exact=top==gold,
                             min_gold_logit=float(min(scores['actor'][list(gold)])),
                             max_negative_logit=float(max(scores['actor'][negatives])) if negatives else None,
                             gold_ranks=[int(np.flatnonzero(ranked==i)[0])+1 for i in sorted(gold)]))
assert counts['exact']==report['final']['predicted']['actors']
receipt=dict(checkpoint_sha256=sha(root/'policy.npz'),contract_sha256=sha(experiment/'contract.json'),
             helper_sha256=sha(Path(__file__)),counts=dict(counts),failures=failures,
             scope='Frozen selected teaching rows only. Compares legitimate input features/base and relational embeddings for human actor and highest-scoring candidate. Human labels are diagnostic only; differences do not prove functional inequivalence. No fitting, other replay predictions, native game or RL.')
path=root/'actor-representation.json'
assert not path.exists()
path.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
