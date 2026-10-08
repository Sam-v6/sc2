from pathlib import Path
import json
from src.learning.tournament_import import import_game
P=Path(__file__).parent;old=Path('logs/roadmap/pro-preconverted-probe-01');result=[]
identity=json.loads((P/'player-identity-audit-02.json').read_text());eligible={g['idx'] for g in identity['games'] if g['initial_identity_consistent']}
for item in json.loads((P/'record-range-plan.json').read_text())['records']:
 index=item['idx']
 if index not in eligible:continue
 output=Path(f'logs/roadmap/pro-demonstrations-07/{index}')
 if (output/'dataset.json').exists():continue
 job=dict(record=str(P/f'fall-record-{index}.bin'),replay=str(P/item['raw_name']),map=str(old/('original-acropolis.s2ma' if item['map_hash'].startswith('30770d') else 'original-disco.s2ma')),catalog='logs/roadmap/joint-frozen-native-wait-02/static.json',reconciliation=str(P/'command-reconciliation-01.json'),phase=str(old/'issue-loop-phase-verification-01.json'),record_index=index,output=str(output))
 (P/f'import-job-{index}-07.json').write_text(json.dumps(job,indent=2)+'\n');r=import_game(job);row={'idx':index,'status':r['status'],'commands':r['issued_command_audit']['matched_issued_commands'],'player':r['player'],'source_user_id':r['source_user_id'],'own_type_checks':r['own_type_checks'],'split':item['split']};result.append(row);print(json.dumps(row),flush=True);(P/'import-results-07.json').write_text(json.dumps(result,indent=2)+'\n')
for index in (774,870):
 job=json.loads((old/f'import-job-{index}-05.json').read_text());job['output']=f'logs/roadmap/pro-demonstrations-07/{index}';(old/f'import-job-{index}-07.json').write_text(json.dumps(job,indent=2)+'\n');r=import_game(job);print(json.dumps({'idx':index,'status':r['status'],'commands':r['issued_command_audit']['matched_issued_commands']}),flush=True)
