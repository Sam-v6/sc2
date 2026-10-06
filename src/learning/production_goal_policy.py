"""Frozen human outcome prediction from the same masked current-state features."""

import numpy as np
from scipy.sparse import csr_matrix, hstack

from src.learning.entity_examples import state_inputs
from src.learning.entity_execution import project_observation
from src.learning.entity_type_status import unit_type_status
from src.learning.intention_probe import probe_features


def current_features(state, vocabulary, products, profile=None):
    projected = project_observation(dict(state, recent_commands=[]), profile)
    inputs = state_inputs(projected, *vocabulary, products=products,
                          missing_fields=True)
    current, _ = probe_features(inputs, *vocabulary[:2])
    return hstack([current, csr_matrix(unit_type_status(inputs, vocabulary[0])
                                       .reshape(1, -1))]).tocsr()


def predict_goals(model, features):
    counts = np.maximum(model['model'].predict(features[:, model['columns']])
                        * model['scale'], 0)[0]
    return {name: int(np.rint(count)) for name, count in zip(model['names'], counts,
                                                            strict=True)
            if np.rint(count) > 0}, counts
