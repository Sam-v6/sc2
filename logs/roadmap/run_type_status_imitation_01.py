"""One frozen paired human-imitation representation comparison; no RL."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch

from src.learning.actor_selection import construction_products
from src.learning.entity_audit import audit_commands
from src.learning.entity_train import collect, validate_datasets
from src.learning.goal_first_policy import GoalFirstPolicy
from src.learning.goal_first_train import fit_goal_first, prediction_history_examples, teaching_support
from src.learning.teacher_states import teacher_states

ROOT = Path('logs/roadmap')
OUT = ROOT / 'type-status-imitation-01'
TRAIN = ('294','870','955','839','991','523')
HELD = ('887','920','851')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n')


def ability_metrics(examples, predictions, macro_ids):
    labels = np.array([c.ability for _,_,c,_ in examples])
    predicted = np.array([p['ability'] for p in predictions])
    macro = np.isin(labels,list(macro_ids))
    selected = np.isin(predicted,list(macro_ids))
    correct = labels == predicted
    return dict(rows=len(labels), macro_rows=int(macro.sum()), ability_correct=int(correct.sum()),
        macro_correct=int((macro & correct).sum()), macro_recall=float((macro & correct).sum()/macro.sum()),
        macro_false_positives=int((~macro & selected).sum()), macro_false_positive_rate=float((~macro & selected).sum()/(~macro).sum()))


assert not OUT.exists()
assert os.environ['CUDA_VISIBLE_DEVICES']==''
assert os.environ['OPENBLAS_NUM_THREADS']==os.environ['OMP_NUM_THREADS']=='2'
torch.set_num_threads(2)
torch.set_num_interop_threads(2)
config_path=ROOT/'joint-professional-fit-05/configuration.json'
config=read(config_path)
sources=[s for s in config['sources'] if s['role']=='teaching']
paths={Path(s['dataset']).name:Path(s['dataset']) for s in sources}
assert set(paths)==set(TRAIN+HELD)
train,held=([paths[g] for g in names] for names in (TRAIN,HELD))
bindings={str(config_path):sha(config_path)}
for source in sources:
    bindings.update(source['bindings'])
code_paths=[*config['code_before'],'src/learning/goal_first_policy.py','src/learning/goal_first_train.py','src/learning/entity_type_status.py',__file__,os.environ['SC2_IMITATION_WATCHDOG'],'docs/superpowers/plans/2026-10-06-type-status-imitation.md']
bindings.update({str(p):sha(p) for p in code_paths})
for path,digest in bindings.items():
    assert sha(path)==digest
started=time.monotonic()
validated=validate_datasets(train,held,missing_fields=True)
games={}
for game in TRAIN+HELD:
    games[game]=collect([paths[game]],config['vocabulary'],spatial=True,missing_fields=True)[0]
    print(json.dumps(dict(stage='loaded',game=game,rows=len(games[game]))),flush=True)
teaching=[e for g in TRAIN for e in games[g]]
validation=[e for g in HELD for e in games[g]]
fitting=[(x,y) for x,y,_,_ in teaching if y is not None]
assert len(teaching)==3400 and len(validation)==1113
x=fitting[0][0]
entities,types,orders,scene,history,roles=x['encoder']
dimensions=(entities.shape[1],len(scene),roles.shape[1],*config['vocabulary'][:2],x['point_features'].shape[1])
base=GoalFirstPolicy(dimensions,(0,1,2,4,8,16,32,64,128,256,512),hidden=64,seed=8156)
candidate=GoalFirstPolicy(dimensions,base.delays,hidden=64,seed=8156,type_status=True)
support=teaching_support(base,fitting)
for p in (base,candidate):
    p.clear_unseen_inputs(support)
for name,value in base.state_dict().items():
    assert torch.equal(value,candidate.state_dict()[name])
assert not candidate.status_projection.weight.any()
assert base.predict(x)==candidate.predict(x)
static=read(train[0]/'static.json')['game_data']
macro_ids={a['ability_id'] for a in static['abilities'] if any(k in a.get('friendly_name','').upper() for k in ('BUILD ','TRAIN ','RESEARCH '))}
contract=dict(bindings=bindings,sources=validated,train=TRAIN,held=HELD,vocabulary=config['vocabulary'],dimensions=dimensions,hidden=64,seed=8156,shuffle_seed=8156,
    epochs=30,optimizer_seconds_per_arm=600,batch_size=16,rate=.001,support_neutralization='Same teaching-only support; new projection zero initialized.',
    training_rows=len(teaching),fitting_rows=len(fitting),held_rows=len(validation),arms=['baseline','type_status'],macro_ids=sorted(macro_ids),
    runtime=dict(executable=sys.executable,torch=torch.__version__,numpy=np.__version__,threads=2,cpu=True,cuda_initialized=torch.cuda.is_initialized()),
    gates=dict(matched_epochs=30,macro_recall_gain=.10,complete_fraction_gain=.05,max_false_positive_increase=.05,own_macro_recall_gain=.10),
    history='Original causal human event-slot history for supervised teaching and ordinary audits; final-policy history on unchanged human states is diagnostic only.',
    scope='Fresh matched six-game human fits; three held games have prior development diagnostic use. No774/reserved/native/RL; no acceptance or promotion.')
if os.environ.get('SC2_TYPE_STATUS_PREFLIGHT_ONLY')=='1':
    assert all(sha(p)==digest for p,digest in bindings.items())
    write(ROOT/'type-status-imitation-01.preflight.json',dict(status='preflight_passed_no_fit',contract=contract,initial_base_weight_parity=True,initial_teaching_prediction_parity=True,optimizer_updates=0))
    print(json.dumps(dict(status='preflight_passed_no_fit',fitting_rows=len(fitting))),flush=True)
    sys.exit(0)
OUT.mkdir()
np.savez_compressed(OUT/'teaching-support.npz',**support)
contract['support_sha256']=sha(OUT/'teaching-support.npz')
write(OUT/'contract.json',contract)
for name,p in [('baseline',base),('type_status',candidate)]:
    arm=OUT/name
    arm.mkdir()
    p.save(arm/'initial.npz',dict(contract_sha256=sha(OUT/'contract.json'),stage='initial',arm=name))
    print(json.dumps(dict(stage='fit_started',arm=name,parameters=sum(v.numel() for v in p.parameters()))),flush=True)
    fitted=fit_goal_first(p,fitting,epochs=30,batch_size=16,rate=.001,seconds=600,seed=8156)
    write(arm/'fit.json',fitted)
    p.save(arm/'policy.npz',dict(contract_sha256=sha(OUT/'contract.json'),fit_status=fitted['status'],arm=name))
    loaded,_=GoalFirstPolicy.load(arm/'policy.npz')
    report=dict(checkpoint_sha256=sha(arm/'policy.npz'),teaching=audit_commands(p,teaching),held=audit_commands(p,validation),commands=[],ability={},own_history={})
    for game in TRAIN+HELD:
        predictions=[]
        for index,(inputs,label,command,reason) in enumerate(games[game]):
            prediction=p.predict(inputs)
            assert prediction==loaded.predict(inputs)
            predictions.append(prediction)
            report['commands'].append(dict(game=game,row=index,prediction=prediction,command=command.as_dict(),exclusion=reason))
        report['ability'][game]=ability_metrics(games[game],predictions,macro_ids)
    ordinary_held=[r['prediction'] for r in report['commands'] if r['game'] in HELD]
    report['held_ability']=ability_metrics(validation,ordinary_held,macro_ids)
    own_predictions=[]
    for game in HELD:
        rebuilt,records=prediction_history_examples(p,games[game],teacher_states(paths[game]),config['vocabulary'],construction_products(read(paths[game]/'static.json')['game_data']))
        assert all(loaded.predict(inputs)==r['prediction'] for (inputs,_,_,_),r in zip(rebuilt,records,strict=True))
        report['own_history'][game]=dict(audit=audit_commands(p,rebuilt),ability=ability_metrics(rebuilt,[r['prediction'] for r in records],macro_ids))
        own_predictions.extend(r['prediction'] for r in records)
        write(arm/f'{game}-own-history.json',records)
    report['own_held_ability']=ability_metrics(validation,own_predictions,macro_ids)
    write(arm/'report.json',report)
    print(json.dumps(dict(stage='arm_finished',arm=name,fit_status=fitted['status'],epochs=fitted['epochs_completed'],held_macro=report['held_ability']['macro_recall'],held_complete=report['held']['predicted']['complete'],own_macro=report['own_held_ability']['macro_recall'])),flush=True)
a,b=(read(OUT/name/'report.json') for name in ('baseline','type_status'))
fa,fb=(read(OUT/name/'fit.json') for name in ('baseline','type_status'))
gates=dict(matched_epochs=fa['epochs_completed']==fb['epochs_completed']==30 and fa['status']==fb['status']=='completed',
    macro_recall_gain=b['held_ability']['macro_recall']>=a['held_ability']['macro_recall']+.10,
    complete_gain=b['held']['predicted']['complete']/len(validation)>=a['held']['predicted']['complete']/len(validation)+.05,
    false_positives=b['held_ability']['macro_false_positive_rate']<=a['held_ability']['macro_false_positive_rate']+.05,
    own_macro_recall_gain=b['own_held_ability']['macro_recall']>=a['own_held_ability']['macro_recall']+.10)
assert all(sha(p)==digest for p,digest in bindings.items()) and not torch.cuda.is_initialized()
comparison=dict(status='completed',gates=gates,all_gates_passed=all(gates.values()),contract_sha256=sha(OUT/'contract.json'),arm_bindings={name:{file:sha(OUT/name/file) for file in ['initial.npz','fit.json','policy.npz','report.json']} for name in ('baseline','type_status')},seconds=time.monotonic()-started,bindings_unchanged=True,promoted=False,native_games=0,rl_updates=0)
write(OUT/'comparison.json',comparison)
print(json.dumps(comparison),flush=True)
