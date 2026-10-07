"""Measure frozen encoder bottlenecks; no optimizer or reserved replay input."""
import hashlib
import json
from pathlib import Path

import numpy as np

from src.learning.actor_selection import construction_products
from src.learning.entity_encoder import JointEntityEncoder
from src.learning.entity_examples import state_inputs
from src.learning.entity_policy import JointEntityPolicy
from src.learning.teacher_states import teacher_states

root = Path('logs/roadmap')
run = root / 'joint-professional-fit-06'
configuration = json.loads((run / 'configuration.json').read_text())
policy, _ = JointEntityPolicy.load(run / 'policy.npz')
initial = JointEntityEncoder(188, 618, 9, 1970, 3801, hidden=32, seed=8100,
                             role_pooling=True, context_layer_norm=True)
samples = {}
for source in configuration['sources']:
    assert source['role'] in ('teaching', 'diagnostic')
    directory = Path(source['dataset'])
    products = construction_products(json.loads((directory / 'static.json').read_text())['game_data'])
    for row, state in teacher_states(directory):
        inputs = state_inputs(dict(state, decision_loop=row['action_loop']),
                              *configuration['vocabulary'], products=products,
                              missing_fields=True)['encoder']
        for name, encoder in [('initial', initial), ('trained', policy.encoder)]:
            context, entities, cache = encoder.forward(*inputs)
            params = encoder.parameters
            history = cache['padded'].ravel() @ params['history']
            scene = cache['scene'] @ params['scene']
            pool = cache['pooled'] @ params['pool']
            values = dict(context_saturated=float(np.mean(np.abs(context) > .95)),
                          entity_saturated=float(np.mean(np.abs(entities) > .95)),
                          history_norm=float(np.linalg.norm(history)),
                          scene_norm=float(np.linalg.norm(scene)),
                          pool_norm=float(np.linalg.norm(pool)))
            key = source['role'] + ':' + name
            current = samples.setdefault(key, {k: [] for k in values})
            for k, v in values.items():
                current[k].append(v)
receipt = dict(scope='Frozen numeric encoder diagnostic over teaching and reused 774 only. No fitting, reserved replay, native game or RL.',
               checkpoint_sha256=hashlib.sha256((run / 'policy.npz').read_bytes()).hexdigest(),
               configuration_sha256=hashlib.sha256((run / 'configuration.json').read_bytes()).hexdigest(),
               helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               summary={key: {k: dict(rows=len(v), mean=float(np.mean(v)),
                                     p95=float(np.percentile(v,95)))
                              for k,v in current.items()}
                        for key,current in samples.items()})
(root / 'professional-encoder-saturation-02.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2))
