"""Verify the matched run and apply gates frozen before fitting."""
import hashlib
import json
from pathlib import Path

root = Path('logs/roadmap')
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
old = root / 'joint-professional-fit-05'
new = root / 'joint-professional-fit-06'
contract_path = root / 'joint-professional-context-contract-01.json'
contract = read(contract_path)
baseline_config = read(old/'configuration.json')
current_config = read(new/'configuration.json')
assert sha(old/'policy.npz')==contract['baseline_sha256']
assert sha(old/'configuration.json')==contract['baseline_configuration_sha256']
assert current_config['context_layer_norm'] is True
matched_old = {k:v for k,v in baseline_config.items() if k!='code_before'}
matched_new = {k:v for k,v in current_config.items() if k not in ('code_before','context_layer_norm')}
for configuration in (matched_old, matched_new):
    configuration['sources'] = [dict(source, bindings={str(Path(path).absolute()):value
                                for path,value in source['bindings'].items()})
                                for source in configuration['sources']]
assert matched_old==matched_new
for path,expected in current_config['code_before'].items():
    assert sha(Path(path))==expected
for path,expected in contract['code_sha256'].items():
    assert sha(Path(path))==expected
for source in current_config['sources']:
    assert Path(source['dataset']).name not in ('848','51483','51886')
    for path,expected in source['bindings'].items():
        assert sha(Path(path))==expected
report = read(new/'report.json')
assert report['status']=='completed' and report['bindings_unchanged'] is True
assert report['checkpoint_sha256']==sha(new/'policy.npz')
assert report['optimizer_updates']==contract['expected_updates']==14100
assert len(report['history'])==50
assert all(row['commands']==4510 and row['epoch']==i+1 and row['updates']==282*(i+1)
           for i,row in enumerate(report['history']))
baseline = read(root/'professional-context-loss-baseline-02.json')
normalized = read(root/'professional-context-loss-normalized-02.json')
helper_path = root/'audit_professional_context_loss_02.py'
for receipt,checkpoint in [(baseline,old/'policy.npz'),(normalized,new/'policy.npz')]:
    assert receipt['checkpoint_sha256']==sha(checkpoint)
    assert receipt['helper_sha256']==sha(helper_path)
    assert receipt['representable_loss_rows']==4510
    assert receipt['baseline_configuration_sha256']==sha(old/'configuration.json')
    assert receipt['max_component_sum_discrepancy']<1e-5
assert set(baseline['teaching_games'])==set(normalized['teaching_games'])
for receipt,run in [(baseline,old),(normalized,new)]:
    training_report = read(run/'report.json')['teaching']['predicted']
    for field,expected in training_report.items():
        assert sum(game['predicted'][field] for game in receipt['teaching_games'].values())==expected
changes = {game: normalized['teaching_games'][game]['predicted']['complete']-
                  baseline['teaching_games'][game]['predicted']['complete']
           for game in baseline['teaching_games']}
assert sum(x['predicted']['complete'] for x in normalized['teaching_games'].values())==report['teaching']['predicted']['complete']
gates = contract['gates']
ratio = normalized['total_mean']/baseline['total_mean']
decision = dict(teaching_loss=ratio<=gates['teaching_loss_ratio_max'],
                teaching_complete=report['teaching']['predicted']['complete']>=gates['teaching_complete_min'],
                teaching_games=sum(delta>0 for delta in changes.values())>=gates['teaching_games_improved_min'],
                diagnostic_complete=report['validation']['predicted']['complete']>=gates['diagnostic_complete_min'],
                diagnostic_ability=report['validation']['predicted']['ability']>=gates['diagnostic_ability_min'],
                diagnostic_actors=report['validation']['predicted']['actors']>=gates['diagnostic_actors_min'])
receipt = dict(status='verified_terminal_matched_supervised_experiment',
               checkpoint_sha256=sha(new/'policy.npz'),contract_sha256=sha(contract_path),
               helper_sha256=sha(Path(__file__)), matched_updates=14100,
               loss_ratio=ratio,baseline_total_loss=baseline['total_mean'],
               normalized_total_loss=normalized['total_mean'],
               component_changes={k:normalized['component_means'][k]-v
                                  for k,v in baseline['component_means'].items()},
               teaching_complete=report['teaching']['predicted']['complete'],
               diagnostic=report['validation']['predicted'],per_game_complete_changes=changes,
               gates=decision,all_gates_passed=all(decision.values()),
               promoted=False,rl_updates=0,native_games=0,reserved_predictions=0,
               conclusion='Judge decision learning by the predeclared gates; reduced saturation alone establishes no competence.')
path = root/'professional-context-comparison-01.json'
assert not path.exists()
path.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
