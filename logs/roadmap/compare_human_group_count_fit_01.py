import json
from pathlib import Path
from collections import Counter
import time

import numpy as np

from src.learning.entity_audit import audit_commands
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_examples import decode_command
from src.learning.entity_train import collect, digest, validate_datasets

root=Path.cwd(); output=root/'logs/roadmap/joint-entity-fit-06'; baseline=root/'logs/roadmap/joint-entity-fit-05'
report=json.loads((output/'report.json').read_text())
configuration=json.loads((output/'configuration.json').read_text())
contract=json.loads((root/'logs/roadmap/human-group-count-comparison-contract-01.json').read_text())
assert report['status']=='completed' and report['bindings_unchanged']
old_configuration=json.loads((baseline/'configuration.json').read_text())
assert old_configuration['sources']==configuration['sources']
assert all(old_configuration[k]==configuration[k] for k in ('epochs','batch_size','hidden','rate','refinement','actor_cutoff','spatial','seed'))
assert report['optimizer_updates']==contract['expected_optimizer_updates']==44278
assert len(report['history'])==169 and all(r['commands']==4189 for r in report['history'])
assert sum(r['commands'] for r in report['history'])==contract['expected_example_passes']==707941
sources=configuration['sources']
paths={role:[Path(s['dataset']) for s in sources if s['role']==role] for role in ('teaching','diagnostic')}
assert validate_datasets(paths['teaching'],paths['diagnostic'])==sources
models={}
for name,path in (('cutoff',baseline/'policy.npz'),('count',output/'policy.npz')):
    policy,metadata=JointEntityPolicy.load(path)
    assert policy.refinement
    assert policy.actor_cutoff
    assert policy.spatial_features == 386
    assert policy.actor_count == (name=='count')
    if name=='count':
        assert metadata['configuration']==configuration and metadata['updates']==44278
    models[name]=policy
bound=[baseline/'policy.npz', output/'policy.npz', output/'report.json', output/'configuration.json', root/'logs/roadmap/human-group-count-comparison-contract-01.json', Path(__file__)]
bound += [Path(path) for path in configuration['code_before']]
bound += [root/'logs/roadmap/human-gas-worker-audit-01.json']
before={str(p):digest(p) for p in bound}
assert before[str(output/'policy.npz')]==report['checkpoint_sha256']
assert before[str(baseline/'policy.npz')]==json.loads((baseline/'report.json').read_text())['checkpoint_sha256']
gas_audit_path=root/'logs/roadmap/human-gas-worker-audit-01.json'
gas_audit=json.loads(gas_audit_path.read_text())
gas_keys={(c['dataset'],c['loop'],json.dumps(c['human'],sort_keys=True)) for c in gas_audit['cases']}
assert len(gas_keys)==47
static=json.loads((paths['teaching'][0]/'static.json').read_text())
refinery_types={u['unit_id'] for u in static['game_data']['units'] if 'Refinery' in u.get('name','')}
start=time.monotonic(); results={}
for role,directories in paths.items():
    results[role]={};all_examples=[]; by_player={};gas_indices=set();matched_gas=set()
    for directory in directories:
        examples,_=collect([directory],configuration['vocabulary'],spatial=True)
        receipt=json.loads((directory/'dataset.json').read_text())
        player=receipt['player']['player_info']['player_name']
        by_player.setdefault(player,[]).extend(examples)
        for i,(inputs,label,command,exclusion) in enumerate(examples):
            loop=round(float(inputs['encoder'][3][0])*13440)
            key=(directory.name,loop,json.dumps(command.as_dict(),sort_keys=True))
            if key in gas_keys:
                gas_indices.add(len(all_examples)+i);matched_gas.add(key)
        all_examples.extend(examples)
    if role=='teaching':assert matched_gas==gas_keys and len(gas_indices)==47
    for name,policy in models.items():
        summary=audit_commands(policy,all_examples)
        if name=='cutoff':
            old_report=json.loads((baseline/'report.json').read_text())
            assert summary==old_report['teaching' if role=='teaching' else 'validation']
        if name=='count':
            assert summary==report['teaching' if role=='teaching' else 'validation']
        individual={player:audit_commands(policy,examples) for player,examples in by_player.items()}
        groups=Counter();geometry=Counter();gas=Counter()
        for example_i,(inputs,label,command,exclusion) in enumerate(all_examples):
            predicted=policy.predict(inputs)
            actual={inputs['tags'][i] for i in predicted['actors']}; gold=set(command.units)
            groups['same_size']+=int(len(actual)==len(gold))
            tag_index={tag:i for i,tag in enumerate(inputs['tags'])}
            target_i=tag_index.get(command.target_unit)
            if (example_i in gas_indices) if role=='teaching' else (target_i is not None and inputs['actor_mask'][target_i] and inputs['encoder'][1][target_i] in refinery_types and all(inputs['encoder'][1][tag_index[tag]]==45 for tag in command.units)):
                decoded=decode_command(predicted,inputs)
                gas['commands']+=1
                gas['same_size']+=int(len(actual)==len(gold))
                gas['actors']+=int(actual==gold)
                gas['target']+=int(decoded.target_unit==command.target_unit)
                gas['complete']+=int(actual==gold and decoded.ability==command.ability and decoded.target_unit==command.target_unit and decoded.target_point is None and decoded.queue==command.queue and decoded.autocast==command.autocast)
            groups['over_selected']+=int(len(actual)>len(gold))
            groups['under_selected']+=int(len(actual)<len(gold))
            groups['same_size_wrong_members']+=int(len(actual)==len(gold) and actual!=gold)
            groups['true_positive']+=len(actual&gold);groups['false_positive']+=len(actual-gold);groups['false_negative']+=len(gold-actual)
            if label is not None and command.target_point is not None:
                scores=policy.scores(inputs,ability=command.ability,actors=label['actors'],point=label['point'])
                geometry['points']+=1; geometry['oracle_correct_cell']+=int(scores['point'].argmax()==label['point'])
                point=inputs['world_points'][label['point']]+scores['offset']*inputs['point_radii'][label['point']]
                geometry['human_cell_offset_within_one_tile']+=int(np.linalg.norm(point-command.target_point)<=1)
        results[role][name]=dict(summary=summary,players=individual,actor_membership=dict(groups),spatial_oracle=dict(geometry),gas_worker=dict(gas))
        print(json.dumps(dict(role=role,model=name,commands=summary['commands'],ordinary=summary['predicted'],players={p:dict(commands=a['commands'],ordinary=a['predicted']) for p,a in individual.items()})),flush=True)
assert before=={str(p):digest(p) for p in bound}
assert validate_datasets(paths['teaching'],paths['diagnostic'])==sources
assert all(digest(Path(path))==sha for path,sha in configuration['code_before'].items())
print(json.dumps({name:results['teaching'][name]['gas_worker'] for name in models}),flush=True)
(root/'logs/roadmap/human-group-count-fit-comparison-partial-01.json').write_text(json.dumps(results,indent=2)+'\n')
assert results['teaching']['cutoff']['gas_worker']==dict(commands=47,same_size=13,actors=5,target=30,complete=5)
assert results['teaching']['count']['gas_worker']['commands']==47
t=results['teaching']['count']['summary'];n=t['commands'];gate=contract['teaching_gate']
passed=all(t['predicted'][key]/n>=gate[key+'_fraction'] for key in ('ability','actors','complete'))
receipt=dict(status='verified',results=results,teaching_gate_passed=passed,bindings_unchanged=True,source_before=sources,checkpoint_bindings=before,seconds=time.monotonic()-start,reserved_replays_opened=False,rl_run=False,scope='Same expanded teaching and separate Rom diagnostic cohorts; per-player scores. Both models teach on the same three-player split. Rom is prospective diagnostic, not randomized fresh acceptance. Identical update/pass budget and source split; added human log-group-size supervision and top-ranked predicted-count actor selection. Equal update/pass budget, not compute-matched. No native/professional claim.')
(root/'logs/roadmap/human-group-count-fit-comparison-01.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(teaching_gate_passed=passed,seconds=receipt['seconds'])),flush=True)
