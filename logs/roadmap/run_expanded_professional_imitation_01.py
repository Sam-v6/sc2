"""One bounded expanded-corpus supervised full raw-command fit; no RL."""
from collections import Counter
import hashlib,json,os,time
from pathlib import Path
import numpy as np
import torch
from src.learning.actor_selection import construction_products
from src.learning.entity_audit import audit_commands
from src.learning.entity_train import collect,validate_datasets
from src.learning.goal_first_policy import GoalFirstPolicy
from src.learning.goal_first_train import fit_goal_first,prediction_history_examples,teaching_support
from src.learning.teacher_states import teacher_states
ROOT=Path('logs/roadmap');OUT=ROOT/'expanded-professional-imitation-01'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
assert not OUT.exists()
assert os.environ['CUDA_VISIBLE_DEVICES']==''
torch.set_num_threads(2);torch.set_num_interop_threads(2)
intakepath=ROOT/'pro-source-expansion-02/final-verification.json';intake=read(intakepath)
bindings={str(intakepath):sha(intakepath),**intake['bindings'],**intake['required_reader_bindings']}
for source in intake['sources']:bindings.update(source['bindings'])
basepath=ROOT/'repaired-production-imitation-01/repaired/policy.npz'
basereportpath=basepath.with_name('report.json');old=read(basereportpath)
assert old['checkpoint_sha256']==sha(basepath)
bindings.update({str(p):sha(p) for p in [basepath,basereportpath,Path(__file__),Path(os.environ['SC2_FIT_WATCHDOG']),Path('docs/superpowers/plans/2026-10-06-expanded-professional-imitation.md')]})
for p in Path('src/learning').glob('*.py'):bindings[str(p)]=sha(p)
assert all(sha(p)==d for p,d in bindings.items())
config=read(ROOT/'joint-professional-fit-05/configuration.json');counts=config['vocabulary']
train=[Path(s['path']) for s in intake['sources'] if s['role']=='teaching']
held=[Path(s['path']) for s in intake['sources'] if s['role']=='development']
validated=validate_datasets(train,held,missing_fields=True)
games={}
for d in train+held:
    games[d.name]=collect([d],counts,spatial=True,missing_fields=True)[0]
    print(json.dumps(dict(stage='loaded',game=d.name,rows=len(games[d.name]))),flush=True)
teaching=[e for d in train for e in games[d.name]];validation=[e for d in held for e in games[d.name]]
fitting=[(x,y) for x,y,_,_ in teaching if y is not None]
assert len(teaching)==6089 and len(fitting)==6086 and len(validation)==1113
x=fitting[0][0];entities,types,orders,scene,history,roles=x['encoder']
dimensions=(entities.shape[1],len(scene),roles.shape[1],*counts[:2],x['point_features'].shape[1])
policy=GoalFirstPolicy(dimensions,(0,1,2,4,8,16,32,64,128,256,512),hidden=64,seed=8156)
support=teaching_support(policy,fitting);policy.clear_unseen_inputs(support)
sample_rng=np.random.default_rng(8159)
samples=[sample_rng.choice(len(fitting),3398,replace=False).tolist() for _ in range(30)]
assert all(len(set(s))==3398 for s in samples) and len(set(i for s in samples for i in s))==6086
static=read(train[0]/'static.json')['game_data']
macro_ids={a['ability_id'] for a in static['abilities'] if any(k in a.get('friendly_name','').upper() for k in ('BUILD ','TRAIN ','RESEARCH '))}
def ability_metrics(examples,predictions):
    labels=np.array([e[2].ability for e in examples]);p=np.array([r['ability'] for r in predictions])
    m=np.isin(labels,list(macro_ids));sel=np.isin(p,list(macro_ids));correct=labels==p
    return dict(rows=len(labels),macro_rows=int(m.sum()),ability_correct=int(correct.sum()),macro_correct=int((m&correct).sum()),macro_recall=float((m&correct).sum()/m.sum()),macro_false_positives=int((~m&sel).sum()),macro_false_positive_rate=float((~m&sel).sum()/(~m).sum()))
baseline,_=GoalFirstPolicy.load(basepath)
baseline_audit=audit_commands(baseline,validation)
assert baseline_audit==old['held']
baseline_ability=ability_metrics(validation,[baseline.predict(e[0]) for e in validation])
assert baseline_ability==old['held_ability']
assert baseline_ability['macro_correct']==21 and baseline_audit['predicted']['complete']==28
OUT.mkdir();np.savez_compressed(OUT/'teaching-support.npz',**support)
contract=dict(bindings=bindings,sources=validated,dimensions=dimensions,vocabulary=counts,sample_indices=samples,sample_seed=8159,shuffle_seed=8156,seed=8156,hidden=64,type_status=False,epochs=30,batch_size=16,rate=.001,optimizer_seconds=600,updates_bound=6390,presentations_bound=101940,teaching_raw=6089,fitting_rows=6086,samples_per_epoch=3398,held_rows=1113,train=[d.name for d in train],held=[d.name for d in held],support_sha256=sha(OUT/'teaching-support.npz'),baseline_ability=baseline_ability,baseline_audit=baseline_audit,rl=False,runtime=dict(torch=torch.__version__,numpy=np.__version__,threads=2,cuda_initialized=torch.cuda.is_initialized()))
write(OUT/'contract.json',contract);policy.save(OUT/'initial.npz',dict(stage='initial',contract_sha256=sha(OUT/'contract.json')))
print(json.dumps(dict(stage='fit_started',rows=len(fitting),updates_bound=6390)),flush=True)
def refresh(p,epoch,deadline):
    if time.monotonic()>=deadline:raise TimeoutError('Sample deadline')
    return [fitting[i] for i in samples[epoch]]
fit=fit_goal_first(policy,[fitting[i] for i in samples[0]],epochs=30,batch_size=16,rate=.001,seconds=600,seed=8156,refresh_examples=refresh)
assert fit['updates']<=6390 and fit['presentations']<=101940
exposure=Counter();rng=np.random.default_rng(8156)
for epoch in fit['history']:
    order=rng.permutation(3398);chosen=samples[epoch['epoch']-1]
    exposure.update(chosen[j] for j in order[:epoch['presentations']])
assert sum(exposure.values())==fit['presentations']
fit['actual_exposure']={str(i):exposure[i] for i in range(len(fitting))};write(OUT/'fit.json',fit)
policy.save(OUT/'policy.npz',dict(stage='fitted',contract_sha256=sha(OUT/'contract.json'),fit_status=fit['status']))
loaded,_=GoalFirstPolicy.load(OUT/'policy.npz')
report=dict(checkpoint_sha256=sha(OUT/'policy.npz'),teaching=audit_commands(policy,teaching),held=audit_commands(policy,validation),commands=[],ability={},own_history={})
for d in train+held:
    predictions=[]
    for index,(inputs,label,command,reason) in enumerate(games[d.name]):
        pred=policy.predict(inputs);assert pred==loaded.predict(inputs)
        predictions.append(pred);report['commands'].append(dict(game=d.name,row=index,prediction=pred,command=command.as_dict(),exclusion=reason))
    report['ability'][d.name]=ability_metrics(games[d.name],predictions)
report['held_ability']=ability_metrics(validation,[r['prediction'] for r in report['commands'] if r['game'] in contract['held']])
report['ability_by_class']={}
for role,ids in [('teaching',contract['train']),('development',contract['held'])]:
    records=[r for r in report['commands'] if r['game'] in ids]
    byclass={}
    names={a['ability_id']:a.get('friendly_name','') for a in static['abilities']}
    for ability in sorted({r['command']['ability'] for r in records}):
        rows=[r for r in records if r['command']['ability']==ability]
        byclass[str(ability)]=dict(name=names[ability],rows=len(rows),correct=sum(r['prediction']['ability']==ability for r in rows))
    report['ability_by_class'][role]=byclass

own=[]
for d in held:
    rebuilt,records=prediction_history_examples(policy,games[d.name],teacher_states(d),counts,construction_products(read(d/'static.json')['game_data']))
    assert all(loaded.predict(e[0])==r['prediction'] for e,r in zip(rebuilt,records,strict=True))
    report['own_history'][d.name]=dict(audit=audit_commands(policy,rebuilt),ability=ability_metrics(rebuilt,[r['prediction'] for r in records]))
    own.extend(r['prediction'] for r in records);write(OUT/f'{d.name}-own-history.json',records)
report['own_held_ability']=ability_metrics(validation,own)
write(OUT/'report.json',report)
gates=dict(completed_budget=fit['status']=='completed' and fit['epochs_completed']==30 and fit['updates']==6390 and fit['presentations']==101940,macro_gain=report['held_ability']['macro_recall']>=baseline_ability['macro_recall']+.10,complete_gain=report['held']['predicted']['complete']/1113>=baseline_audit['predicted']['complete']/1113+.05,false_positives=report['held_ability']['macro_false_positive_rate']<=baseline_ability['macro_false_positive_rate']+.05,own_macro_gain=report['own_held_ability']['macro_recall']>=old['own_held_ability']['macro_recall']+.10)
assert all(sha(p)==d for p,d in bindings.items())
write(OUT/'comparison.json',dict(gates=gates,all_gates=all(gates.values()),contract_sha256=sha(OUT/'contract.json'),report_sha256=sha(OUT/'report.json')))
print(json.dumps(dict(stage='completed',fit_status=fit['status'],held_ability=report['held_ability'],held_complete=report['held']['predicted']['complete'],own_ability=report['own_held_ability'],gates=gates)),flush=True)
