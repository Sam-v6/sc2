import json
from pathlib import Path
from collections import Counter
import time

import numpy as np

from src.learning.entity_audit import audit_commands
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect, digest, validate_datasets

root=Path.cwd(); output=root/'logs/roadmap/joint-entity-fit-03'; baseline=root/'logs/roadmap/joint-entity-fit-02'
report=json.loads((output/'report.json').read_text())
configuration=json.loads((output/'configuration.json').read_text())
contract=json.loads((root/'logs/roadmap/joint-entity-fit-contract-03.json').read_text())
assert report['status']=='completed' and report['bindings_unchanged']
assert report['optimizer_updates']==contract['expected_optimizer_updates']==44278
assert len(report['history'])==169 and all(r['commands']==4189 for r in report['history'])
assert sum(r['commands'] for r in report['history'])==contract['expected_example_passes']==707941
sources=configuration['sources']
paths={role:[Path(s['dataset']) for s in sources if s['role']==role] for role in ('teaching','diagnostic')}
assert validate_datasets(paths['teaching'],paths['diagnostic'])==sources
models={}
for name,path in (('nine_player_games',baseline/'policy.npz'),('three_players',output/'policy.npz')):
    policy,metadata=JointEntityPolicy.load(path)
    assert policy.refinement
    if name=='three_players':
        assert metadata['configuration']==configuration and metadata['updates']==44278
    models[name]=policy
bound=[baseline/'policy.npz', output/'policy.npz', output/'report.json', output/'configuration.json', root/'logs/roadmap/joint-entity-fit-contract-03.json', Path(__file__)]
bound += [Path(path) for path in configuration['code_before']]
before={str(p):digest(p) for p in bound}
assert before[str(output/'policy.npz')]==report['checkpoint_sha256']
start=time.monotonic(); results={}
for role,directories in paths.items():
    results[role]={};all_examples=[]; by_player={}
    for directory in directories:
        examples,_=collect([directory],configuration['vocabulary'])
        receipt=json.loads((directory/'dataset.json').read_text())
        player=receipt['player']['player_info']['player_name']
        by_player.setdefault(player,[]).extend(examples)
        all_examples.extend(examples)
    for name,policy in models.items():
        summary=audit_commands(policy,all_examples)
        if name=='three_players':
            assert summary==report['teaching' if role=='teaching' else 'validation']
        individual={player:audit_commands(policy,examples) for player,examples in by_player.items()}
        groups=Counter();geometry=Counter()
        for inputs,label,command,exclusion in all_examples:
            predicted=policy.predict(inputs)
            actual={inputs['tags'][i] for i in predicted['actors']}; gold=set(command.units)
            groups['over_selected']+=int(len(actual)>len(gold))
            groups['under_selected']+=int(len(actual)<len(gold))
            groups['same_size_wrong_members']+=int(len(actual)==len(gold) and actual!=gold)
            groups['true_positive']+=len(actual&gold);groups['false_positive']+=len(actual-gold);groups['false_negative']+=len(gold-actual)
            if label is not None and command.target_point is not None:
                scores=policy.scores(inputs,ability=command.ability,actors=label['actors'],point=label['point'])
                geometry['points']+=1; geometry['oracle_correct_cell']+=int(scores['point'].argmax()==label['point'])
                point=inputs['world_points'][label['point']]+scores['offset']*inputs['point_radii'][label['point']]
                geometry['human_cell_offset_within_one_tile']+=int(np.linalg.norm(point-command.target_point)<=1)
        results[role][name]=dict(summary=summary,players=individual,actor_membership=dict(groups),spatial_oracle=dict(geometry))
        print(json.dumps(dict(role=role,model=name,commands=summary['commands'],ordinary=summary['predicted'],players={p:dict(commands=a['commands'],ordinary=a['predicted']) for p,a in individual.items()})),flush=True)
assert before=={str(p):digest(p) for p in bound}
assert validate_datasets(paths['teaching'],paths['diagnostic'])==sources
assert all(digest(Path(path))==sha for path,sha in configuration['code_before'].items())
t=results['teaching']['three_players']['summary'];n=t['commands'];gate=contract['teaching_gate']
passed=all(t['predicted'][key]/n>=gate[key+'_fraction'] for key in ('ability','actors','complete'))
receipt=dict(status='verified',results=results,teaching_gate_passed=passed,bindings_unchanged=True,source_before=sources,checkpoint_bindings=before,seconds=time.monotonic()-start,reserved_replays_opened=False,rl_run=False,scope='Same expanded teaching and separate Rom diagnostic cohorts; per-player scores. Added Lyra/Huski are teaching for new model, not held-out improvement. Rom is prospective diagnostic, not randomized fresh acceptance. Approximate update/pass matching; no native/professional claim.')
(root/'logs/roadmap/diverse-human-fit-comparison-01.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(teaching_gate_passed=passed,seconds=receipt['seconds'])),flush=True)
