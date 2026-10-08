import json
from pathlib import Path
import numpy as np
from src.learning.tournament_record import decode_record
root=Path(__file__).parent;result=[]
for idx in (294,774,870):
    record=decode_record((root/f'fall-record-{idx}.bin').read_bytes());steps=record['steps'];block=record['units'];fields=block['fields'];loops=steps['game_loop'];examples=[];counts={'scv_commands':0,'idle_before_and_at':0,'new_order_at_command':0,'busy_before':0}
    aligned=json.loads((root/f'command-alignment-{idx}.json').read_text())['accepted']
    def actor_orders(step,tag):
        indices=np.flatnonzero((block['step']==step)&(fields['id']==tag))
        if len(indices)!=1:return None
        i=indices[0];return [int(fields[f'order{k}'][i]['ability']) for k in range(4) if fields[f'order{k}'][i]['ability']]
    for row in aligned:
        if row['converted']['ability']!=524:continue
        indices=np.flatnonzero(loops==row['loop'])
        if len(indices)!=1:continue
        i=int(indices[0]);tag=row['converted']['tags'][0];current=actor_orders(i,tag);before=actor_orders(i-1,tag) if i else None
        counts['scv_commands']+=1
        if before==[] and current==[]:counts['idle_before_and_at']+=1
        if before==[] and current and 524 in current:counts['new_order_at_command']+=1
        if before:counts['busy_before']+=1
        examples.append(dict(loop=row['loop'],queue=row['restored_queue'],before=before,current=current,nearby=[dict(loop=int(loops[j]),minerals=int(steps['minerals'][j]),orders=actor_orders(j,tag)) for j in range(max(0,i-1),min(i+2,len(loops)))]))
    result.append(dict(idx=idx,counts=counts,examples=examples));print(idx,counts,flush=True)
(root/'command-state-timing-audit-01.json').write_text(json.dumps(result,indent=2)+'\n')
