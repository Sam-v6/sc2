import gzip
import json
from pathlib import Path
from src.learning.entity_audit import audit_commands
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect, digest

root=Path.cwd(); old=root/'logs/roadmap/issued-51960-p1'; corrected=root/'logs/roadmap/issued-timing-masked-01/issued-51960-p1'
with gzip.open(old/'examples.jsonl.gz','rt') as f: original=list(map(json.loads,f))
with gzip.open(corrected/'examples.jsonl.gz','rt') as f: revised=list(map(json.loads,f))
assert len(original)==len(revised)==303
changes=[]
for a,b in zip(original,revised):
    assert {k:v for k,v in a.items() if k!='next_action_delay'}=={k:v for k,v in b.items() if k!='next_action_delay'}
    if a['next_action_delay']!=b['next_action_delay']:
        assert a['next_action_delay'] is not None and b['next_action_delay'] is None
        changes.append(a['action_loop'])
paths=[root/'logs/roadmap/issued-timing-masked-01/issued-50925',corrected]
configuration=json.loads((root/'logs/roadmap/joint-entity-fit-02/configuration.json').read_text())
bound=[p/name for p in paths for name in ('dataset.json','static.json','examples.jsonl.gz')]
bound += [root/f'logs/roadmap/joint-entity-fit-{i:02d}/policy.npz' for i in (1,2)]
before={str(p):digest(p) for p in bound}
examples,_=collect(paths,configuration['vocabulary']);results={}
for i in (1,2):
    policy,_=JointEntityPolicy.load(root/f'logs/roadmap/joint-entity-fit-{i:02d}/policy.npz')
    report=audit_commands(policy,examples)
    prior=json.loads((root/f'logs/roadmap/joint-entity-fit-{i:02d}/report.json').read_text())['validation']
    for mode in ('predicted','ability_oracle','ability_actor_oracle'):
        for field in ('ability','actors','mode','queue','target','complete'):
            assert report[mode][field]==prior[mode][field]
    assert report['point_errors']==prior['point_errors']
    results[str(i)]=report
assert before=={str(p):digest(p) for p in bound}
receipt=dict(status='verified',changed_huski_timing_rows=changes,results=results,before=before,bindings_unchanged=True,training_affected=False,scope='Corrected reused Huski timing diagnostic; all observations/action identities/arguments and non-timing counts unchanged; original fit reports preserved. No retraining/native/RL/holdout use.')
(root/'logs/roadmap/joint-refinement-timing-diagnostic-correction-01.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(changed_rows=len(changes),known_timing_commands=results['2']['timed_commands'],baseline=results['1']['predicted'],refinement=results['2']['predicted'])),flush=True)
