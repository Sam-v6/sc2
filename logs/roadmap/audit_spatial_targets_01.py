import json
from collections import Counter
from pathlib import Path

import numpy as np

from src.learning.spatial_construction import decode_terrain
from src.learning.teacher_states import teacher_states
from src.learning.entity_train import digest

root=Path.cwd();c=json.loads((root/'logs/roadmap/joint-entity-fit-04/configuration.json').read_text())
sources=[s for s in c['sources'] if s['role']=='teaching']; counts=Counter(); abilities={}
for source in sources:
    directory=Path(source['dataset']);static=json.loads((directory/'static.json').read_text())
    terrain=decode_terrain(static['terrain'])
    for row,state in teacher_states(directory):
        grids=decode_terrain(state['map'])
        for command in row['commands']:
            if command.get('target_point') is None: continue
            point=np.asarray(command['target_point']);height,width=grids['visibility'].shape
            if not (np.all(point>=0) and np.all(point<[width,height])):
                counts['outside_or_exact_upper_boundary']+=1;continue
            x,y=point.astype(int);visibility=int(grids['visibility'][y,x]);pathable=int(bool(terrain['pathing_grid'][y,x]));placeable=int(bool(terrain['placement_grid'][y,x]))
            counts['points']+=1;counts['visibility_'+str(visibility)]+=1
            counts['not_pathable']+=int(not pathable);counts['not_placeable']+=int(not placeable)
            group=abilities.setdefault(str(command['ability']),Counter());group['points']+=1;group['visibility_'+str(visibility)]+=1;group['not_pathable']+=int(not pathable);group['not_placeable']+=int(not placeable)
for source in sources: assert all(digest(Path(p))==sha for p,sha in source['bindings'].items())
receipt=dict(status='verified',counts=dict(counts),abilities={k:dict(v) for k,v in abilities.items()},sources=sources,scope='Native y,x pixel orientation and MSB-first binary grids via existing decoder. Point sampling uses floor coordinates. Static pathing/placement is descriptive, not dynamic legality; no target exclusion, fit, reserved replay or RL.')
(root/'logs/roadmap/spatial-target-audit-01.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(counts=receipt['counts'],abilities=receipt['abilities'])))
