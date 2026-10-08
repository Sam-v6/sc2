import json
from collections import Counter
from pathlib import Path
from src.learning.entity_train import validate_datasets, collect, digest

root=Path.cwd(); old=json.loads((root/'logs/roadmap/joint-entity-fit-02/configuration.json').read_text())
teaching=[Path(s['dataset']) for s in old['sources'] if s['role']=='teaching']
teaching += [root/'logs/roadmap/issued-timing-masked-01/issued-50925',root/'logs/roadmap/issued-timing-masked-01/issued-51960-p1']
diagnostic=[root/'logs/roadmap/issued-51482-rom-masked-01']
sources=validate_datasets(teaching,diagnostic)
contract=dict(teaching=list(map(str,teaching)),diagnostic=list(map(str,diagnostic)),sources=sources,
              vocabulary=old['vocabulary'],architecture='Unchanged refined joint model; no further architecture or loss changes',
              roles='Previously reused Lyra/Huski diagnostics explicitly become teaching before any new fit. Rom stays diagnostic; this is prospectively defined, not randomized fresh acceptance.',
              reserved_replays_not_opened=['51483','51886'],professional_teachers=0,
              planned_budget='Freeze comparable update budget separately after collection/count audit; no fit or prediction in this audit',
              code_before={str(Path('src/learning')/f'{name}.py'):digest(Path('src/learning')/f'{name}.py') for name in ('entity_train','entity_policy','entity_examples','entity_encoder')})
(root/'logs/roadmap/multiplayer-teacher-split-contract-01.json').write_text(json.dumps(contract,indent=2)+'\n')
results={}
for role,paths in (('teaching',teaching),('diagnostic',diagnostic)):
    examples,reports=collect(paths,old['vocabulary'])
    players=Counter()
    for path in paths:
        receipt=json.loads((path/'dataset.json').read_text())
        players[receipt['player']['player_info']['player_name']]+=receipt['issued_command_audit']['matched_issued_commands']
    results[role]=dict(commands=len(examples),representable=sum(label is not None for _,label,_,_ in examples),players=dict(players),datasets=reports)
    print(json.dumps(dict(role=role,**{k:v for k,v in results[role].items() if k!='datasets'})),flush=True)
assert validate_datasets(teaching,diagnostic)==sources
assert all(digest(Path(path))==sha for path,sha in contract['code_before'].items())
report=dict(status='verified',results=results,bindings_unchanged=True,model_predictions=False,fit=False,reserved_replays_opened=False)
(root/'logs/roadmap/multiplayer-teacher-split-audit-01.json').write_text(json.dumps(report,indent=2)+'\n')
