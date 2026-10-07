import copy
import json
from collections import Counter
from pathlib import Path

import numpy as np

from src.learning.entity_examples import state_inputs
from src.learning.entity_train import digest
from src.learning.teacher_states import teacher_states

root = Path.cwd()
configuration = json.loads((root/'logs/roadmap/joint-entity-fit-04/configuration.json').read_text())
sources = [s for s in configuration['sources'] if s['role']=='teaching']
counts = Counter(); static_grids = Counter(); probes = {}
code = {p:digest(Path(p)) for p in configuration['code_before']}
for source in sources:
    directory = Path(source['dataset'])
    static = json.loads((directory/'static.json').read_text())
    for name, grid in static.get('terrain', {}).items():
        static_grids[name] += int(bool(grid.get('data')))
    for row, state in teacher_states(directory):
        counts['states'] += 1
        for name in ('visibility','creep'):
            counts[name+'_present'] += int(bool(state.get('map', {}).get(name, {}).get('data')))
        for name in ('effects','radar_contacts'):
            counts[name+'_nonempty'] += int(bool(state.get(name)))
        if probes: continue
        baseline = state_inputs(state, *configuration['vocabulary'][:2], upgrade_count=configuration['vocabulary'][2])
        for field, value in (('map', {'visibility': {'data':'changed'}, 'creep':{'data':'changed'}}), ('effects',[{'effect_id':999,'positions':[{'x':100,'y':100}]}]), ('radar_contacts',[{'position':[100,100,0]}])):
            changed = copy.deepcopy(state);changed[field] = value
            candidate = state_inputs(changed, *configuration['vocabulary'][:2], upgrade_count=configuration['vocabulary'][2])
            identical = all(np.array_equal(x,y) for x,y in zip(baseline['encoder'],candidate['encoder']))
            identical &= all(np.array_equal(baseline[k],candidate[k]) for k in ('actor_mask','target_mask','points','world_points','point_radii'))
            probes[field] = bool(identical)
        probes['source'] = str(directory)
assert code == {p:digest(Path(p)) for p in code}
for source in sources:
    assert all(digest(Path(p))==sha for p,sha in source['bindings'].items())
receipt = dict(status='verified',counts=dict(counts),static_grids=dict(static_grids),changed_fields_leave_model_inputs_identical=probes,code_bindings=code,source_bindings=sources,scope='Current compact preprocessing omits visibility/creep grids, radar and effects, and static terrain grids. Mutations are isolated sensitivity probes, not hidden state or training changes. No claimed causal explanation of fit errors; live fit untouched.')
(root/'logs/roadmap/spatial-sensor-gap-audit-01.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('code_bindings','source_bindings')}))
