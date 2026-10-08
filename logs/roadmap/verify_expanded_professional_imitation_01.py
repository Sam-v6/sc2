"""Rebuild the expanded human imitation evidence; never refit or play."""
from collections import Counter
import hashlib,json
from pathlib import Path
import numpy as np
import torch
from src.learning.actor_selection import construction_products
from src.learning.entity_audit import audit_commands
from src.learning.entity_train import collect,validate_datasets
from src.learning.goal_first_policy import GoalFirstPolicy
from src.learning.goal_first_train import prediction_history_examples,teaching_support
from src.learning.teacher_states import teacher_states
OUT=Path('logs/roadmap/expanded-professional-imitation-01')
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def normal(x):return json.loads(json.dumps(x))
torch.set_num_threads(2);torch.set_num_interop_threads(2)
c=read(OUT/'contract.json');report=read(OUT/'report.json');fit=read(OUT/'fit.json');comparison=read(OUT/'comparison.json')
assert comparison['contract_sha256']==sha(OUT/'contract.json') and comparison['report_sha256']==sha(OUT/'report.json')
assert c['rl'] is False and c['hidden']==64 and c['type_status'] is False
assert c['epochs']==30 and c['samples_per_epoch']==3398 and c['fitting_rows']==6086
assert c['seed']==c['shuffle_seed']==8156 and c['sample_seed']==8159
assert c['batch_size']==16 and c['rate']==.001 and c['optimizer_seconds']==600
for p,d in c['bindings'].items():assert sha(p)==d,p
intake=read('logs/roadmap/pro-source-expansion-02/final-verification.json')
train=[Path(s['path']) for s in intake['sources'] if s['role']=='teaching']
held=[Path(s['path']) for s in intake['sources'] if s['role']=='development']
assert normal(validate_datasets(train,held,missing_fields=True))==c['sources']
games={d.name:collect([d],c['vocabulary'],spatial=True,missing_fields=True)[0] for d in train+held}
teaching=[e for d in train for e in games[d.name]];validation=[e for d in held for e in games[d.name]]
fitting=[(x,y) for x,y,_,_ in teaching if y is not None]
assert len(teaching)==6089 and len(fitting)==6086 and len(validation)==1113
rng=np.random.default_rng(8159);samples=[rng.choice(6086,3398,replace=False).tolist() for _ in range(30)]
assert samples==c['sample_indices']
assert len(set(i for s in samples for i in s))==6086
initial,_=GoalFirstPolicy.load(OUT/'initial.npz');fresh=GoalFirstPolicy(c['dimensions'],initial.delays,hidden=64,seed=8156)
support=teaching_support(fresh,fitting);saved=dict(np.load(OUT/'teaching-support.npz',allow_pickle=False))
assert c['support_sha256']==sha(OUT/'teaching-support.npz')
for k in support:np.testing.assert_array_equal(support[k],saved[k])
fresh.clear_unseen_inputs(support)
for k,v in fresh.state_dict().items():assert torch.equal(v,initial.state_dict()[k]),k
exposure=Counter();rng=np.random.default_rng(8156)
for epoch in fit['history']:
    order=rng.permutation(3398);exposure.update(samples[epoch['epoch']-1][i] for i in order[:epoch['presentations']])
assert {str(i):exposure[i] for i in range(6086)}==fit['actual_exposure']
assert sum(exposure.values())==fit['presentations']==sum(e['presentations'] for e in fit['history'])
policy,meta=GoalFirstPolicy.load(OUT/'policy.npz');assert meta['contract_sha256']==sha(OUT/'contract.json')
assert report['checkpoint_sha256']==sha(OUT/'policy.npz')
assert normal(audit_commands(policy,teaching))==report['teaching']
assert normal(audit_commands(policy,validation))==report['held']
static=read(train[0]/'static.json')['game_data']
macro={a['ability_id'] for a in static['abilities'] if any(k in a.get('friendly_name','').upper() for k in ('BUILD ','TRAIN ','RESEARCH '))}
def metrics(examples,predictions):
    labels=np.array([e[2].ability for e in examples]);p=np.array([r['ability'] for r in predictions]);m=np.isin(labels,list(macro));sel=np.isin(p,list(macro));correct=labels==p
    return dict(rows=len(labels),macro_rows=int(m.sum()),ability_correct=int(correct.sum()),macro_correct=int((m&correct).sum()),macro_recall=float((m&correct).sum()/m.sum()),macro_false_positives=int((~m&sel).sum()),macro_false_positive_rate=float((~m&sel).sum()/(~m).sum()))
records=[]
for d in train+held:
    predictions=[]
    for i,(inputs,label,command,reason) in enumerate(games[d.name]):
        pred=policy.predict(inputs);predictions.append(pred)
        records.append(dict(game=d.name,row=i,prediction=pred,command=command.as_dict(),exclusion=reason))
    assert metrics(games[d.name],predictions)==report['ability'][d.name]
assert normal(records)==report['commands']
assert metrics(validation,[r['prediction'] for r in records if r['game'] in c['held']])==report['held_ability']
names={a['ability_id']:a.get('friendly_name','') for a in static['abilities']}
for role,ids in [('teaching',c['train']),('development',c['held'])]:
    selected=[r for r in records if r['game'] in ids]
    classes={}
    for a in sorted({r['command']['ability'] for r in selected}):
        rows=[r for r in selected if r['command']['ability']==a]
        classes[str(a)]=dict(name=names[a],rows=len(rows),correct=sum(r['prediction']['ability']==a for r in rows))
    assert classes==report['ability_by_class'][role]
own=[]
for d in held:
    rebuilt,preds=prediction_history_examples(policy,games[d.name],teacher_states(d),c['vocabulary'],construction_products(read(d/'static.json')['game_data']))
    assert normal(preds)==read(OUT/f'{d.name}-own-history.json')
    assert normal(audit_commands(policy,rebuilt))==report['own_history'][d.name]['audit']
    assert metrics(rebuilt,[r['prediction'] for r in preds])==report['own_history'][d.name]['ability']
    own.extend(r['prediction'] for r in preds)
assert metrics(validation,own)==report['own_held_ability']
base=c['baseline_ability'];ba=c['baseline_audit'];old=read('logs/roadmap/repaired-production-imitation-01/repaired/report.json')
gates=dict(completed_budget=fit['status']=='completed' and fit['epochs_completed']==30 and fit['updates']==6390 and fit['presentations']==101940,macro_gain=report['held_ability']['macro_recall']>=base['macro_recall']+.10,complete_gain=report['held']['predicted']['complete']/1113>=ba['predicted']['complete']/1113+.05,false_positives=report['held_ability']['macro_false_positive_rate']<=base['macro_false_positive_rate']+.05,own_macro_gain=report['own_held_ability']['macro_recall']>=old['own_held_ability']['macro_recall']+.10)
assert gates==comparison['gates'] and all(gates.values())==comparison['all_gates']
result=dict(status='verified',ordinary_predictions=len(records),own_history_predictions=len(own),actual_presentations=sum(exposure.values()),gates=gates,bindings={str(p):sha(p) for p in [OUT/'contract.json',OUT/'report.json',OUT/'fit.json',OUT/'comparison.json',OUT/'policy.npz',Path(__file__)]})
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
