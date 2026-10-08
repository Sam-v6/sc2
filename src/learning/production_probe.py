"""Closed-form human production forecast diagnostic, not a game controller."""

import numpy as np
from scipy.linalg import solve


def fit_forecast(matrix, labels, seconds, *, regularization):
    """Fit ability scores and log delay using teaching-only feature scaling."""
    if matrix.shape[0] == 0 or regularization <= 0:
        raise ValueError("Expected teaching rows and positive regularization")
    classes, targets = np.unique(labels, return_inverse=True)
    squares = np.asarray(matrix.power(2).mean(axis=0)).ravel()
    columns = np.flatnonzero(squares)
    scales = np.sqrt(squares[columns])
    values = matrix[:, columns].multiply(1 / scales).tocsr()
    outputs = np.column_stack((np.eye(len(classes))[targets], np.log1p(seconds)))
    prior = outputs.mean(axis=0)
    kernel = (values @ values.T).toarray()
    column_mean = kernel.mean(axis=0)
    mean = kernel.mean()
    centered = kernel - column_mean[:, None] - column_mean[None, :] + mean
    system = centered + regularization * len(targets) * np.eye(len(targets))
    residual = outputs - prior
    dual = solve(system, residual, assume_a="pos")
    relative_residual = np.linalg.norm(system @ dual - residual) / max(
        np.linalg.norm(residual), 1
    )
    return dict(
        classes=classes,
        columns=columns,
        scales=scales,
        values=values,
        prior=prior,
        dual=dual,
        column_mean=column_mean,
        mean=mean,
        relative_residual=float(relative_residual),
    )


def predict_forecast(model, matrix):
    """Predict native ability IDs and nonnegative seconds from causal inputs."""
    values = matrix[:, model["columns"]].multiply(1 / model["scales"]).tocsr()
    kernel = (values @ model["values"].T).toarray()
    centered = (
        kernel
        - kernel.mean(axis=1, keepdims=True)
        - model["column_mean"][None, :]
        + model["mean"]
    )
    scores = centered @ model["dual"] + model["prior"]
    return model["classes"][scores[:, :-1].argmax(axis=1)], np.maximum(
        0, np.expm1(scores[:, -1])
    )
