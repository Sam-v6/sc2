"""Project candidate actor matrix memory from actual human command groups."""
import hashlib,json,time
from pathlib import Path
from src.learning.teacher_states import teacher_states,own_actors
ROOT=Path('logs/roadmap');OUT=ROOT/'actor-memory-projection-01';OUT.mkdir(exist_ok=False)
datasets=[ROOT/'issued-timing-masked-01'/f'issued-{n}' for n in (51574,51573,51958,51890,51891)]
datasets += [ROOT/f'issued-{n}-expansion-01' for n in (51572,51685,51885)]
files=[Path(__file__),Path('src/learning/teacher_states.py'),ROOT/'consistent-fullgame-02/actors/report.json',*[p/name for p in datasets for name in ('dataset.json','static.json','examples.jsonl.gz')]]
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=hashes();previous=json.loads((ROOT/'consistent-fullgame-02/actors/report.json').read_text());width=previous['full_feature_columns'];inventory=[];start=time.monotonic()
for p in datasets:
    receipt=json.loads((p/'dataset.json').read_text());assert receipt['status']=='completed'
    commands=0;entities=0;maxactors=0
    for row,state in teacher_states(p):
        actors=own_actors(state);known={u['tag'] for u in actors}
        for c in row['commands']:
            assert set(c['units'])<=known
            commands+=1;entities+=len(actors);maxactors=max(maxactors,len(actors))
    inventory.append({'dataset':str(p),'replay_sha256':receipt['sha256'],'commands':commands,'entity_examples':entities,'max_candidate_actors':maxactors,'professional':False})
assert len({r['replay_sha256'] for r in inventory})==len(inventory)
after=hashes();assert after==before
total=sum(r['entity_examples'] for r in inventory);dense=total*width*4
report={'status':'completed','scope':'Projection for eight currently terminal candidate teaching games only; two long retries and Rom excluded; no model loaded/fit or RL',
        'files_before':before,'files_after':after,'sources_unchanged':True,'datasets':inventory,'command_groups':sum(r['commands'] for r in inventory),
        'entity_examples':total,'full_feature_columns':width,'dense_float32_matrix_bytes':dense,
        'dense_list_plus_stack_minimum_bytes':2*dense,'overhead_excluded':'Python objects, groups, normalization and training temporary allocations; machine free memory is not measured',
        'old_fit_active_columns':previous['training_columns'],'new_active_columns_not_measured':True,'reserved51886_not_used':True,'wall_seconds':time.monotonic()-start}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('files_before','files_after','datasets')}))
