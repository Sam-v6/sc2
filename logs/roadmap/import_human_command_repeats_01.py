from pathlib import Path
import json
from src.learning.tournament_import import import_game
root=Path('logs/roadmap');source=root/'pro-preconverted-probe-01';out=root/'human-command-repeats-01'
job=dict(record=str(source/'fall-record-870.bin'),replay=str(source/'2cda222081e80d9a1c188698ce9bcda6.SC2Replay'),map=str(source/'original-acropolis.s2ma'),catalog=str(root/'joint-frozen-native-wait-02/static.json'),reconciliation=str(out/'reconciliation.json'),phase=str(source/'issue-loop-phase-verification-01.json'),record_index=870,output=str(out/'corpus/870'))
receipt=import_game(job);(out/'import-job.json').write_text(json.dumps(job,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ('status','training_eligible','unresolved_repeat_contexts')}))
