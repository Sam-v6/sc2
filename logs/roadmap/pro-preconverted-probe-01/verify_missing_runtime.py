import base64
import hashlib
import json
from pathlib import Path
import tempfile

import numpy as np

from src.learning.entity_encoder import JointEntityEncoder
from src.learning.entity_examples import state_inputs
from src.learning.entity_execution import JointCommandAgent
from src.learning.entity_policy import JointEntityPolicy
from src.learning.gameplay import PlayerView
from src.learning.tournament_observation import partial_observation
from src.learning.tournament_record import decode_record

root = Path(__file__).parent
results = []
policy = JointEntityPolicy(JointEntityEncoder(188, 618, 9, 1970, 3801, hidden=4),
                          (0, 1, 8), missing_fields=True, spatial_features=401)
with tempfile.TemporaryDirectory() as temporary:
    checkpoint = Path(temporary) / 'format-only.npz'
    policy.save(checkpoint, {'purpose': 'input-format probe; random untrained weights'})
    restored, _ = JointEntityPolicy.load(checkpoint)
    for idx, size in ((294, (200, 184)), (774, (200, 184)), (870, (176, 184))):
        path = root / f'fall-record-{idx}.bin'
        data = decode_record(path.read_bytes())
        view = PlayerView()
        tested = 0
        for step in range(len(data['steps']['game_loop'])):
            state = partial_observation(data, step, size, view)
            if step % 100:
                continue
            # Converted header height maps are not yet independently reconciled.
            terrain = {'terrain_height': {'known': False}}
            for source, name in (('buildable', 'placement_grid'), ('pathable', 'pathing_grid')):
                grid = data['images'][source][step]
                terrain[name] = dict(width=128, height=128, bits_per_pixel=1,
                    data=base64.b64encode(np.packbits(grid).tobytes()).decode(),
                    coordinate_system='feature_minimap', world_size=list(size),
                    transform='world_y_flip_then_uniform_max_dimension_scale')
            inputs = state_inputs(state, 1970, 3801, 296, missing_fields=True, terrain=terrain)
            assert inputs['point_features'].shape[1] == 401
            assert np.isfinite(inputs['point_features']).all()
            assert (inputs['point_features'][:, -5:] == [0, 1, 1, 1, 1]).all()
            assert (inputs['point_features'][:, 386:388] == 0).all()
            expected = policy.predict(inputs)
            assert restored.predict(inputs) == expected
            command, delay = JointCommandAgent(restored, (1970, 3801, 296), {}, terrain).decide(state)
            assert command.ability == expected['ability'] and delay == expected['delay']
            command.to_proto()
            tested += 1
        result = dict(idx=idx, samples=tested, stride=100,
                      record_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        results.append(result)
        print(result, flush=True)
paths = [Path('src/learning') / (name+'.py') for name in ('entity_encoder',
    'entity_examples', 'entity_missing', 'entity_execution', 'entity_policy',
    'entity_spatial', 'tournament_observation', 'tournament_record')]
paths.append(Path(__file__))
receipt = dict(records=results, training_eligible=False, optimizer_updates=0,
    gameplay_episodes=0, height_map='Unknown pending independent map reconciliation',
    bindings={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
(root / 'missing-runtime-verification-01.json').write_text(json.dumps(receipt, indent=2)+'\n')
