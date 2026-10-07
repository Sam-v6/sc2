import hashlib
import json
from pathlib import Path

import numpy as np

from src.learning.entity_examples import state_inputs
from src.learning.gameplay import PlayerView
from src.learning.tournament_observation import partial_observation
from src.learning.tournament_record import decode_record

root = Path(__file__).parent
results = []
for idx, size in ((294, (200, 184)), (774, (200, 184)), (870, (176, 184))):
    path = root / f'fall-record-{idx}.bin'
    data = decode_record(path.read_bytes())
    view = PlayerView()
    tested = 0
    for step in range(len(data['steps']['game_loop'])):
        state = partial_observation(data, step, size, view)
        if step % 20:
            continue
        inputs = state_inputs(state, 1970, 3801, 296, missing_fields=True)
        entities, _, _, scene, _, _ = inputs['encoder']
        assert entities.shape == (len(inputs['tags']), 188)
        assert scene.shape == (618,)
        assert np.isfinite(entities).all() and np.isfinite(scene).all()
        assert (entities[:, 10] == 0).all() and (entities[:, 104] == 0).all()
        assert scene[6] == 0 and scene[315] == 0
        tested += 1
    result = dict(idx=idx, input_samples=tested, stride=20,
                  record_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    results.append(result)
    print(result, flush=True)
paths = [Path('src/learning/entity_missing.py'), Path('src/learning/entity_examples.py'),
         Path('src/learning/tournament_observation.py'), Path(__file__)]
receipt = dict(records=results, training_eligible=False,
               bindings={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
(root / 'missing-input-verification-01.json').write_text(json.dumps(receipt, indent=2)+'\n')
