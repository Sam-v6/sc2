from pathlib import Path
import hashlib,json
from src.learning.entity_train import validate_datasets,validate_professional_source
P=Path(__file__).parent;root=Path('logs/roadmap/pro-demonstrations-07');train_indices=[294,870,955,887,839,991,920,851,523];diagnostic_indices=[774];reserved_indices=[848]
sources=validate_datasets([root/str(i) for i in train_indices],[root/str(i) for i in diagnostic_indices],True)
for index in reserved_indices:
 path=root/str(index);validate_professional_source(path,json.loads((path/'dataset.json').read_text()),True)
all_indices=train_indices+diagnostic_indices+reserved_indices;rows=[];bindings={}
for index in all_indices:
 path=root/str(index);receipt=json.loads((path/'dataset.json').read_text());role='teaching' if index in train_indices else 'diagnostic' if index in diagnostic_indices else 'reserved_professional_evaluation';rows.append({'idx':index,'dataset':str(path),'role':role,'replay_sha256':receipt['sha256'],'commands':receipt['issued_command_audit']['matched_issued_commands'],'player_id':receipt['player']['player_info']['player_id'],'source_user_id':receipt['source_user_id'],'own_type_checks':receipt['own_type_checks']})
 for name in ('dataset.json','static.json','examples.jsonl.gz'):bindings[str(path/name)]=hashlib.sha256((path/name).read_bytes()).hexdigest()
assert len({r['replay_sha256'] for r in rows})==len(rows)
ledger=json.loads((P/'ledger.json').read_text());assert ledger['reserved_bytes']<=ledger['cap_bytes'] and all(r['status']=='completed' for r in ledger['requests'])
result={'status':'verified_terminal_professional_imports','datasets':rows,'bindings':bindings,'teaching_commands':sum(r['commands'] for r in rows if r['role']=='teaching'),'diagnostic_commands':sum(r['commands'] for r in rows if r['role']=='diagnostic'),'reserved_commands':sum(r['commands'] for r in rows if r['role']=='reserved_professional_evaluation'),'own_type_checks':sum(r['own_type_checks'] for r in rows),'transfer_reserved_bytes':ledger['reserved_bytes'],'cap_bytes':ledger['cap_bytes'],'whole_game_splits_disjoint':True,'new_professional_optimizer_updates':0,'new_professional_model_predictions':0,'native_games':0,'rl_updates':0,'competence_demonstrated':False}
(P/'corpus-verification-07.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('datasets','bindings')},indent=2))
