"""Read-only verification of the predeclared human importance experiment."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from src.learning.entity_audit import audit_commands
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect, ability_importance_weights

root = Path('logs/roadmap')
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
old = root/'joint-professional-fit-05'
new = root/'joint-professional-fit-07'
contract_path = root/'joint-professional-importance-contract-01.json'
contract = read(contract_path)
before, after = read(old/'configuration.json'), read(new/'configuration.json')
assert sha(old/'policy.npz') == contract['baseline_sha256']
assert sha(old/'configuration.json') == contract['baseline_configuration_sha256']
assert sha(root/'professional-command-failures-01.json') == contract['diagnostic_audit_sha256']
assert sha(root/'run_professional_importance_fit_01.py') == contract['helper_sha256']
assert sha(Path('src/learning/entity_train.py')) == contract['trainer_sha256']
assert after['ability_importance'] is True and after['context_layer_norm'] is False
left = {k:v for k,v in before.items() if k != 'code_before'}
right = {k:v for k,v in after.items() if k not in ('code_before','ability_importance','importance','context_layer_norm')}
for configuration in (left, right):
    configuration['sources'] = [dict(s, bindings={str(Path(p).absolute()):v for p,v in s['bindings'].items()}) for s in configuration['sources']]
assert left == right
for p,v in after['code_before'].items():
    assert sha(Path(p)) == v
for source in after['sources']:
    assert Path(source['dataset']).name not in ('848','51483','51886')
    for p,v in source['bindings'].items():
        assert sha(Path(p)) == v
report = read(new/'report.json')
assert report['status'] == 'completed' and report['bindings_unchanged'] is True
assert report['checkpoint_sha256'] == sha(new/'policy.npz')
assert report['optimizer_updates'] == contract['expected_updates'] == 14100
assert len(report['history']) == 50
assert all(r['commands'] == 4510 and r['epoch'] == i+1 and r['updates'] == 282*(i+1) for i,r in enumerate(report['history']))
teaching = [Path(s['dataset']) for s in after['sources'] if s['role']=='teaching']
examples,_ = collect(teaching,after['vocabulary'],spatial=True,missing_fields=True)
abilities = [command.ability for _,label,command,_ in examples if label is not None]
weights = ability_importance_weights(abilities,len(teaching))
assert {str(k):v for k,v in Counter(abilities).items()} == {k:v['count'] for k,v in after['importance']['abilities'].items()}
for ability,weight in zip(abilities,weights):
    recorded = after['importance']['abilities'][str(ability)]
    assert abs(recorded['weight']-float(weight)) < 1e-12
assert sum(v['count'] for v in after['importance']['abilities'].values()) == 4510
diagnostic = [Path(s['dataset']) for s in after['sources'] if s['role']=='diagnostic']
assert len(diagnostic) == 1 and diagnostic[0].name == '774'
examples,_ = collect(diagnostic,after['vocabulary'],spatial=True,missing_fields=True)
assert len(examples) == 292 and all(label is not None for _,label,_,_ in examples)
names = {a['ability_id']:a.get('friendly_name','') for a in read(diagnostic[0]/'static.json')['game_data']['abilities']}
policy,_ = JointEntityPolicy.load(new/'policy.npz')
groups = defaultdict(list)
for example in examples:
    groups[example[2].ability].append(example)
audits = {str(ability):dict(name=names[ability],**audit_commands(policy,rows)) for ability,rows in groups.items()}
fields = report['validation']['predicted']
assert {f:sum(a['predicted'][f] for a in audits.values()) for f in fields} == fields
macros = {k:a for k,a in audits.items() if a['name'].startswith(('Build ','Train ','Research '))}
assert {k:a['commands'] for k,a in macros.items()} == contract['macro_ability_counts']
macro_correct = sum(a['predicted']['ability'] for a in macros.values())
smart_attack_correct = sum(audits[str(k)]['predicted']['ability'] for k in (1,3674))
assert sum(a['commands'] for a in macros.values()) == 91
assert sum(audits[str(k)]['commands'] for k in (1,3674)) == 198
g = contract['gates']
gates = dict(complete=fields['complete']>=g['complete_min'],macro_ability=macro_correct>=g['macro_ability_min'],
             required_abilities=all(audits[str(k)]['predicted']['ability']>=1 for k in g['required_abilities']),
             ability=fields['ability']>=g['ability_min'],smart_attack=smart_attack_correct>=g['smart_attack_ability_min'],
             teaching_complete=report['teaching']['predicted']['complete']>=g['teaching_complete_min'])
baseline_loss = read(root/'professional-context-loss-baseline-02.json')
weighted_loss = read(root/'professional-importance-loss-01.json')
for receipt,run in ((baseline_loss,old),(weighted_loss,new)):
    assert receipt['checkpoint_sha256']==sha(run/'policy.npz')
    assert receipt['helper_sha256']==sha(root/'audit_professional_context_loss_02.py')
    assert receipt['baseline_configuration_sha256']==sha(old/'configuration.json')
    assert receipt['representable_loss_rows']==4510 and receipt['max_component_sum_discrepancy']<1e-5
    for f,v in read(run/'report.json')['teaching']['predicted'].items():
        assert sum(game['predicted'][f] for game in receipt['teaching_games'].values())==v
receipt = dict(status='verified_terminal_matched_human_imitation',checkpoint_sha256=sha(new/'policy.npz'),
               contract_sha256=sha(contract_path),helper_sha256=sha(Path(__file__)),matched_updates=14100,
               diagnostic=fields,macro_ability_correct=macro_correct,macro_total=91,smart_attack_correct=smart_attack_correct,
               teaching_complete=report['teaching']['predicted']['complete'],
               unweighted_loss_before=baseline_loss['total_mean'],unweighted_loss_after=weighted_loss['total_mean'],
               per_ability=audits,gates=gates,all_gates_passed=all(gates.values()),
               promoted=False,native_games=0,rl_updates=0,reserved_predictions=0)
path = root/'professional-importance-comparison-01.json'
assert not path.exists()
path.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='per_ability'},indent=2))
