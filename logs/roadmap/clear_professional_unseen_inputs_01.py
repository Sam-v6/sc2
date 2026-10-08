"""Derive a separately bound checkpoint without fitting or held-out inputs."""
import hashlib
import json
from pathlib import Path

import numpy as np

from src.learning.actor_selection import construction_products
from src.learning.entity_examples import state_inputs
from src.learning.entity_policy import JointEntityPolicy
from src.learning.teacher_states import teacher_states

root = Path('logs/roadmap')
parent = root / 'joint-professional-fit-05/policy.npz'
output = root / 'joint-professional-fit-05-supported'
output.mkdir(exist_ok=True)
checkpoint = output / 'policy.npz'
assert not checkpoint.exists(), 'Never overwrite an experiment checkpoint'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
configuration = json.loads((parent.parent / 'configuration.json').read_text())
support_path = root / 'professional-input-support-01.npz'
audit = json.loads((root / 'professional-input-support-01.json').read_text())
assert audit['checkpoint_sha256'] == sha(parent)
with np.load(support_path, allow_pickle=False) as archive:
    support = {name: archive[name].copy() for name in archive.files}
original, metadata = JointEntityPolicy.load(parent)
derived, _ = JointEntityPolicy.load(parent)
derived.encoder.clear_unseen_inputs(support)
for name, before in original.parameters.items():
    after = derived.parameters[name]
    encoder_name = next((key for key in support
                         if before is original.encoder.parameters[key]), None)
    if encoder_name is None:
        np.testing.assert_array_equal(before, after)
    else:
        mask = support[encoder_name]
        np.testing.assert_array_equal(before[mask], after[mask])
        assert np.all(after[~mask] == 0)
seen = {name: np.zeros_like(mask) for name, mask in support.items()}
rows = 0
for source in configuration['sources']:
    if source['role'] != 'teaching':
        continue
    for filename, expected in source['bindings'].items():
        assert sha(Path(filename)) == expected
    directory = Path(source['dataset'])
    products = construction_products(json.loads((directory / 'static.json').read_text())['game_data'])
    for row, state in teacher_states(directory):
        inputs = state_inputs(dict(state, decision_loop=row['action_loop']),
                              *configuration['vocabulary'], products=products,
                              missing_fields=True)['encoder']
        for name, values in [('entity', inputs[0]), ('scene', inputs[3][None, :]),
                             ('history_roles', inputs[5])]:
            seen[name] |= np.any(values != 0, axis=0)
            assert np.all(values[:, ~support[name]] == 0)
        before = original.encoder.forward(*inputs)[:2]
        after = derived.encoder.forward(*inputs)[:2]
        for a, b in zip(before, after, strict=True):
            np.testing.assert_array_equal(a, b)
        rows += len(row['commands'])
for name in support:
    np.testing.assert_array_equal(seen[name], support[name])
assert rows == audit['teaching_commands']
provenance = dict(parent_sha256=sha(parent), support_sha256=sha(support_path),
                  helper_sha256=sha(Path(__file__)),
                  encoder_code_sha256=sha(Path('src/learning/entity_encoder.py')),
                  teaching_configuration_sha256=sha(parent.parent / 'configuration.json'))
derived.save(checkpoint, dict(metadata, input_support_correction=provenance))
loaded, saved_metadata = JointEntityPolicy.load(checkpoint)
for name, expected in derived.parameters.items():
    np.testing.assert_array_equal(expected, loaded.parameters[name])
assert saved_metadata['input_support_correction'] == provenance
assert sha(parent) == audit['checkpoint_sha256']
receipt = dict(provenance, checkpoint_sha256=sha(checkpoint),
               teaching_commands_verified=rows, exact_teaching_encoder_parity=True,
               supported_parameters_unchanged=True, checkpoint_roundtrip_verified=True,
               scope='Frozen derivative only; no optimizer, diagnostic/reserved replay, native game or RL. No strength claim or promotion.')
(output / 'verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
