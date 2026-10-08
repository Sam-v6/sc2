"""Sequential new-source imports; no optimizer or model prediction."""
from pathlib import Path
import hashlib,json
from src.learning.tournament_import import import_game
P=Path(__file__).parent; old=Path('logs/roadmap/pro-preconverted-probe-01')
selection=json.loads((P/'record-range-plan.json').read_text())
identity=json.loads((P/'player-identity-audit-01.json').read_text())
assert len(identity['games'])==5 and all(g['initial_identity_consistent'] and g['matched_initial_native_types']==13 for g in identity['games'])
results=[]
for item in selection['records']:
    i=item['idx']; output=Path(f'logs/roadmap/pro-demonstrations-09/{i}')
    assert not output.exists()
    job=dict(record=str(P/f'fall-record-{i}.bin'),replay=str(P/item['raw_name']),map=str(old/('original-acropolis.s2ma' if item['map_hash'].startswith('30770d') else 'original-disco.s2ma')),catalog='logs/roadmap/joint-frozen-native-wait-02/static.json',reconciliation=str(P/'command-reconciliation-02.json'),phase=str(old/'issue-loop-phase-verification-01.json'),record_index=i,output=str(output))
    (P/f'import-job-{i}-09.json').write_text(json.dumps(job,indent=2)+'\n')
    r=import_game(job)
    assert r['status']=='completed'
    result=dict(idx=i,status=r['status'],commands=r['issued_command_audit']['matched_issued_commands'],own_type_checks=r['own_type_checks'],sha256=r['sha256'],source_user_id=r['source_user_id'])
    results.append(result);(P/'import-results-09.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(result),flush=True)
