"""Pairwise human precedence from sparse state utilities, without expanded states."""

import numpy as np
from scipy.special import expit


def utility_objective(
    parameters,
    state,
    row,
    left,
    right,
    truth,
    sample_weight,
    regularization,
    family_count,
):
    weights = parameters.reshape(state.shape[1] + 1, family_count)
    scores = state @ weights[:-1] + weights[-1]
    logits = scores[row, left] - scores[row, right]
    loss = np.dot(sample_weight, np.logaddexp(0, logits) - truth * logits)
    loss += regularization * np.square(weights[:-1]).sum() / 2
    residual = sample_weight * (expit(logits) - truth)
    score_gradient = np.zeros_like(scores)
    np.add.at(score_gradient, (row, left), residual)
    np.add.at(score_gradient, (row, right), -residual)
    gradient = np.vstack((state.T @ score_gradient, score_gradient.sum(axis=0)))
    gradient[:-1] += regularization * weights[:-1]
    return float(loss), gradient.ravel()
