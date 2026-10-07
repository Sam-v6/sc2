"""Independently reconstruct paired imitation artifacts; never refit."""
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from src.learning.actor_selection import construction_products
from src.learning.entity_audit import audit_commands
from src.learning.entity_train import collect,validate_datasets
from src.learning.goal_first_policy import GoalFirstPolicy
from src.learning.goal_first_train import prediction_history_examples,teaching_support
from src.learning.teacher_states import teacher_states

ROOT=Path('logs/roadmap/type-status-imitation-01')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normal(value):
    return json.loads(json.dumps(value))


contract,comparison=read(ROOT/'contract.json'),read(ROOT/'comparison.json')
assert comparison['contract_sha256']==sha(ROOT/'contract.json')
assert contract['train']==['294','870','955','839','991','523']
assert contract['held']==['887','920','851']
assert contract['epochs']==30 and contract['optimizer_seconds_per_arm']==600 and contract['rate']==.001 and contract['batch_size']==16
assert contract['seed']==contract['shuffle_seed']==8156
for path,digest in contract['bindings'].items():
    assert sha(path)==digest,path
config=read('logs/roadmap/joint-professional-fit-05/configuration.json')
paths={Path(s['dataset']).name:Path(s['dataset']) for s in config['sources'] if s['role']=='teaching'}
assert set(paths)==set(contract['train']+contract['held'])
assert validate_datasets([paths[g] for g in contract['train']],[paths[g] for g in contract['held']],missing_fields=True)==contract['sources']
games={}
for game in contract['train']+contract['held']:
    games[game]=collect([paths[game]],contract['vocabulary'],spatial=True,missing_fields=True)[0]
    print(json.dumps(dict(stage='reconstructed',game=game,rows=len(games[game]))),flush=True)
teaching=[e for g in contract['train'] for e in games[g]]
held=[e for g in contract['held'] for e in games[g]]
fitting=[(x,y) for x,y,_,_ in teaching if y is not None]
assert len(teaching)==contract['training_rows']==3400 and len(fitting)==contract['fitting_rows']==3398 and len(held)==contract['held_rows']==1113
assert sha(ROOT/'teaching-support.npz')==contract['support_sha256']
base_initial,_=GoalFirstPolicy.load(ROOT/'baseline/initial.npz')
expected=GoalFirstPolicy(contract['dimensions'],base_initial.delays,hidden=64,seed=8156)
support=teaching_support(expected,fitting)
expected.clear_unseen_inputs(support)
with np.load(ROOT/'teaching-support.npz',allow_pickle=False) as archive:
    for key in support:
        np.testing.assert_array_equal(support[key],archive[key])
for name,value in expected.state_dict().items():
    torch.testing.assert_close(value,base_initial.state_dict()[name],rtol=0,atol=0)
candidate_initial,_=GoalFirstPolicy.load(ROOT/'type_status/initial.npz')
assert not base_initial.type_status and candidate_initial.type_status
for name,value in base_initial.state_dict().items():
    torch.testing.assert_close(value,candidate_initial.state_dict()[name],rtol=0,atol=0)
assert not candidate_initial.status_projection.weight.any()
macro=set(contract['macro_ids'])
static=read(paths[contract['train'][0]]/'static.json')['game_data']
assert macro=={a['ability_id'] for a in static['abilities'] if any(k in a.get('friendly_name','').upper() for k in ('BUILD ','TRAIN ','RESEARCH '))}


def macro_metrics(examples,predictions):
    counts=Counter()
    for (_,_,gold,_),pred in zip(examples,predictions,strict=True):
        counts['rows']+=1
        ismacro=gold.ability in macro
        counts['macro_rows']+=ismacro
        correct=gold.ability==pred['ability']
        counts['ability_correct']+=correct
        counts['macro_correct']+=ismacro and correct
        counts['macro_false_positives']+=not ismacro and pred['ability'] in macro
    result={k:counts[k] for k in ['rows','macro_rows','ability_correct','macro_correct','macro_false_positives']}
    result['macro_recall']=result['macro_correct']/result['macro_rows']
    result['macro_false_positive_rate']=result['macro_false_positives']/(result['rows']-result['macro_rows'])
    return result


reports,fits={},{}
for name in contract['arms']:
    arm=ROOT/name
    for file,digest in comparison['arm_bindings'][name].items():
        assert sha(arm/file)==digest
    report,fit=read(arm/'report.json'),read(arm/'fit.json')
    policy,meta=GoalFirstPolicy.load(arm/'policy.npz')
    assert meta['contract_sha256']==sha(ROOT/'contract.json') and meta['fit_status']==fit['status']
    assert policy.type_status==(name=='type_status')
    assert report['checkpoint_sha256']==sha(arm/'policy.npz')
    assert fit['epochs_completed']<=30 and fit['optimizer_seconds']<=610
    assert fit['presentations']==sum(h['presentations'] for h in fit['history'])
    if fit['status']=='completed':
        assert fit['epochs_completed']==len(fit['history'])==30
        assert fit['presentations']==len(fitting)*30 and fit['updates']==int(np.ceil(len(fitting)/16))*30
    assert audit_commands(policy,teaching)==report['teaching']
    assert audit_commands(policy,held)==report['held']
    all_records=[]
    for game in contract['train']+contract['held']:
        predictions=[]
        for index,(inputs,label,gold,reason) in enumerate(games[game]):
            prediction=policy.predict(inputs)
            predictions.append(prediction)
            all_records.append(dict(game=game,row=index,prediction=prediction,command=gold.as_dict(),exclusion=reason))
        assert macro_metrics(games[game],predictions)==report['ability'][game]
    assert normal(all_records)==report['commands']
    predictions=[r['prediction'] for r in all_records if r['game'] in contract['held']]
    assert macro_metrics(held,predictions)==report['held_ability']
    own=[]
    for game in contract['held']:
        rebuilt,records=prediction_history_examples(policy,games[game],teacher_states(paths[game]),contract['vocabulary'],construction_products(read(paths[game]/'static.json')['game_data']))
        assert normal(records)==read(arm/f'{game}-own-history.json')
        assert audit_commands(policy,rebuilt)==report['own_history'][game]['audit']
        predictions=[r['prediction'] for r in records]
        assert macro_metrics(rebuilt,predictions)==report['own_history'][game]['ability']
        own.extend(predictions)
    assert macro_metrics(held,own)==report['own_held_ability']
    reports[name],fits[name]=report,fit
    print(json.dumps(dict(stage='arm_verified',arm=name,ordinary_rows=len(all_records),own_rows=len(own))),flush=True)
a,b=reports['baseline'],reports['type_status']
fa,fb=fits['baseline'],fits['type_status']
gates=dict(matched_epochs=fa['epochs_completed']==fb['epochs_completed']==30 and fa['status']==fb['status']=='completed',macro_recall_gain=b['held_ability']['macro_recall']>=a['held_ability']['macro_recall']+.10,complete_gain=b['held']['predicted']['complete']/len(held)>=a['held']['predicted']['complete']/len(held)+.05,false_positives=b['held_ability']['macro_false_positive_rate']<=a['held_ability']['macro_false_positive_rate']+.05,own_macro_recall_gain=b['own_held_ability']['macro_recall']>=a['own_held_ability']['macro_recall']+.10)
assert gates==comparison['gates'] and all(gates.values())==comparison['all_gates_passed']
telemetry=read(ROOT.with_suffix('.telemetry.json'))
assert telemetry['status']=='completed' and telemetry['returncode']==0 and telemetry['stop_reason'] is None
assert not comparison['promoted'] and comparison['native_games']==comparison['rl_updates']==0
result=dict(status='verified_development_gate_result',all_gates_passed=all(gates.values()),gates=gates,comparison_sha256=sha(ROOT/'comparison.json'),contract_sha256=sha(ROOT/'contract.json'),telemetry_sha256=sha(ROOT.with_suffix('.telemetry.json')),verifier_sha256=sha(__file__),ordinary_predictions_verified=9026,own_history_predictions_verified=2226,scope='Source/initial weights/support/final predictions/metrics/gates reconstructed; no optimizer refit, native competence or acceptance claim.')
(ROOT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
