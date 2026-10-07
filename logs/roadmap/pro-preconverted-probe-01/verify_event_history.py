import hashlib
import json
from collections import defaultdict, Counter
from pathlib import Path
import time

import numpy as np

from src.learning.entity_examples import state_inputs, command_label
from src.learning.entity_train import DELAYS
from src.learning.gameplay import Command, PlayerView
from src.learning.tournament_history import history_rows
from src.learning.tournament_observation import partial_observation
from src.learning.tournament_record import decode_record

root = Path(__file__).parent
source = root/'command-reconciliation-03.json'
reconciled = json.loads(source.read_text())
results = []
for game in reconciled['games']:
    idx = game['idx']
    record = decode_record((root/f'fall-record-{idx}.bin').read_bytes())
    events = json.loads((root/f'raw-commands-{idx}.json').read_text())
    accepted = []
    for item in game['accepted']:
        raw = item['command']
        command = Command(**dict(raw, units=tuple(raw['units']),
            target_point=tuple(raw['target_point']) if raw.get('target_point') is not None else None))
        accepted.append(dict(item,command=command))
    rows = list(history_rows(events, accepted))
    by_loop = defaultdict(list)
    for row in rows:by_loop[row['loop']].append(row)
    view = PlayerView()
    size = (176,184) if idx==870 else (200,184)
    count = representable = with_unknown = masked_timing = 0
    exclusions = Counter()
    start = time.perf_counter()
    for step,loop in enumerate(record['steps']['game_loop']):
        state = partial_observation(record,step,size,view)
        for row in by_loop.get(int(loop),[]):
            candidate = dict(state, recent_commands=row['recent_commands'], history_quality='event_slots')
            inputs = state_inputs(candidate,1970,3801,296,missing_fields=True)
            assert np.isfinite(inputs['encoder'][0]).all()
            assert np.isfinite(inputs['encoder'][5]).all()
            expected = [0 if c.get('unknown') else c['ability'] for c in row['recent_commands']]
            assert list(inputs['encoder'][4]) == expected
            for slot,c in enumerate(row['recent_commands'],32-len(row['recent_commands'])):
                if c.get('unknown'):
                    assert (inputs['encoder'][0][:,94+30+2*slot:94+32+2*slot]==0).all()
            count += 1
            with_unknown += any(c.get('unknown') for c in row['recent_commands'])
            masked_timing += row['next_action_delay'] is None
            try:
                command_label(row['command'],inputs,DELAYS,row['next_action_delay'])
                representable += 1
            except ValueError as error:
                exclusions[str(error)] += 1
        if step % 500 == 0:print(dict(idx=idx,step=step,checked=count),flush=True)
    assert count==len(accepted)
    result=dict(idx=idx,history_rows=count,representable_labels=representable,
        rows_with_unknown_history=with_unknown,masked_timing=masked_timing,
        exclusions=dict(exclusions),seconds=time.perf_counter()-start)
    results.append(result);print(result,flush=True)
paths=[source,Path(__file__),*[Path('src/learning')/(n+'.py') for n in
    ('tournament_history','entity_missing','entity_examples','teacher_states')]]
receipt=dict(records=results,training_eligible=False,optimizer_updates=0,
    bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
(root/'event-history-verification-01.json').write_text(json.dumps(receipt,indent=2)+'\n')
