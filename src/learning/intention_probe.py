"""Optional sparse diagnostics for human action-choice signal, not a controller."""

from collections import Counter
import time

import numpy as np


def probe_features(inputs, unit_count, ability_count):
    """Separate masked current state from causal event history without labels."""
    from scipy.sparse import csr_matrix

    entities, types, orders, scene, abilities, roles = inputs["encoder"]
    masks = entities[:, 94:124]
    base = np.where(masks, entities[:, :30], 0)
    scene_size = len(scene) // 2
    state = dict(
        enumerate(
            np.concatenate(
                (
                    np.where(scene[scene_size:], scene[:scene_size], 0),
                    scene[scene_size:],
                )
            )
        )
    )
    ownership = np.where(base[:, 2:5].any(axis=1), base[:, 2:5].argmax(axis=1), 3)
    counts = Counter()
    count_width = unit_count + ability_count
    for owner in range(4):
        selected = ownership == owner
        values = base[selected].sum(axis=0) / masks[selected].sum(axis=0).clip(min=1)
        availability = masks[selected].mean(axis=0) if selected.any() else np.zeros(30)
        for column, value in enumerate(np.concatenate((values, availability))):
            state[len(scene) + 8 * count_width + owner * 60 + column] = value
    for row, (owner, kind, order) in enumerate(
        zip(ownership, types, orders, strict=True)
    ):
        observed = bool(base[row, 5])
        group = 2 * owner + int(observed)
        counts[len(scene) + group * count_width + int(kind)] += 1
        # Remembered units have no observed current orders.
        if observed:
            counts[len(scene) + group * count_width + unit_count + int(order)] += 1
    state.update({column: np.log1p(count) for column, count in counts.items()})
    history = {}
    slot_width = ability_count + 11  # Native ability,9roles,presence,unknown.
    for slot, (ability, role) in enumerate(
        zip(abilities, roles, strict=True), 32 - len(abilities)
    ):
        offset = slot * slot_width
        history[offset + int(ability)] = 1
        history.update(
            {offset + ability_count + i: value for i, value in enumerate(role)}
        )
        history[offset + ability_count + 9] = 1
        history[offset + ability_count + 10] = float(ability == 0)

    def sparse(values, width):
        nonzero = [(index, value) for index, value in values.items() if value != 0]
        return csr_matrix(
            (
                [value for _, value in nonzero],
                ([0] * len(nonzero), [index for index, _ in nonzero]),
            ),
            shape=(1, width),
        )

    return sparse(state, len(scene) + 8 * count_width + 240), sparse(
        history, 32 * slot_width
    )


def fit_probe(matrix, labels, *, regularization, max_iterations, deadline):
    """Fit one diagnostic classifier; scaling/classes use this training fold only."""
    from scipy.optimize import minimize
    from scipy.special import logsumexp

    classes, targets, counts = np.unique(
        labels, return_inverse=True, return_counts=True
    )
    squares = np.asarray(matrix.power(2).mean(axis=0)).ravel()
    columns = np.flatnonzero(squares)
    scales = np.sqrt(squares[columns])
    values = matrix[:, columns].multiply(1 / scales).tocsr()
    width, class_count = len(columns), len(classes)
    initial = np.zeros((width + 1, class_count))
    initial[-1] = np.log(counts / counts.sum())
    latest = initial.ravel().copy()
    calls = 0
    started = time.monotonic()

    def objective(parameters):
        nonlocal latest, calls
        if time.monotonic() >= deadline:
            raise TimeoutError("Intention probe reached its deadline")
        calls += 1
        weights = parameters.reshape(width + 1, class_count)
        logits = values @ weights[:-1] + weights[-1]
        log_probs = logits - logsumexp(logits, axis=1, keepdims=True)
        loss = -log_probs[np.arange(len(targets)), targets].mean()
        loss += regularization * np.square(weights[:-1]).sum() / 2
        residual = np.exp(log_probs)
        residual[np.arange(len(targets)), targets] -= 1
        residual /= len(targets)
        gradient = np.vstack(
            (values.T @ residual + regularization * weights[:-1], residual.sum(axis=0))
        )
        if not np.isfinite(loss) or not np.isfinite(gradient).all():
            raise ValueError("Nonfinite intention probe objective")
        latest = parameters.copy()
        return loss, gradient.ravel()

    iterations = 0
    try:
        result = minimize(
            objective,
            latest,
            method="L-BFGS-B",
            jac=True,
            options=dict(maxiter=max_iterations, maxcor=10, ftol=1e-9, gtol=1e-5),
        )
        latest = result.x
        iterations = result.nit
        status = (
            "converged"
            if result.success
            else "iteration_bound"
            if result.status == 1
            else "solver_failed"
        )
    except TimeoutError:
        status = "wall_bound"
    weights = latest.reshape(width + 1, class_count)
    model = dict(
        classes=classes,
        columns=columns,
        scales=scales,
        weights=weights[:-1].copy(),
        bias=weights[-1].copy(),
    )
    report = dict(
        status=status,
        iterations=iterations,
        objective_calls=calls,
        seconds=time.monotonic() - started,
        samples=len(labels),
        active_columns=width,
        class_counts={str(c): int(n) for c, n in zip(classes, counts, strict=True)},
    )
    return model, report


def probe_logits(model, matrix):
    values = matrix[:, model["columns"]].multiply(1 / model["scales"]).tocsr()
    return values @ model["weights"] + model["bias"]


def probe_metrics(model, matrix, labels, macro_ids):
    """Absent classes are errors; exact macro recall; CE probability floor1e-12."""
    from scipy.special import logsumexp

    logits = probe_logits(model, matrix)
    ranked = model["classes"][np.argsort(-logits, axis=1, kind="stable")[:, :3]]
    predicted = ranked[:, 0]
    log_probs = logits - logsumexp(logits, axis=1, keepdims=True)
    lookup = {int(c): i for i, c in enumerate(model["classes"])}
    target_logs = np.array(
        [
            max(log_probs[i, lookup[int(label)]], np.log(1e-12))
            if int(label) in lookup
            else np.log(1e-12)
            for i, label in enumerate(labels)
        ]
    )
    correct = predicted == labels
    top3 = (ranked == labels[:, None]).any(axis=1)
    macro = np.isin(labels, list(macro_ids))
    selected_macro = np.isin(predicted, list(macro_ids))

    def rate(numerator, denominator):
        return float(numerator / denominator) if denominator else None

    return dict(
        rows=len(labels),
        cross_entropy=float(-target_logs.mean()),
        top1=float(correct.mean()),
        top3=float(top3.mean()),
        macro_rows=int(macro.sum()),
        macro_exact_recall=rate((correct & macro).sum(), macro.sum()),
        macro_family_recall=rate((selected_macro & macro).sum(), macro.sum()),
        macro_false_positive_rate=rate((selected_macro & ~macro).sum(), (~macro).sum()),
        absent_training_abilities={
            str(c): int((labels == c).sum())
            for c in np.unique(labels)
            if int(c) not in lookup
        },
        per_ability={
            str(c): dict(
                rows=int((labels == c).sum()),
                top1_correct=int((correct & (labels == c)).sum()),
                top3_correct=int((top3 & (labels == c)).sum()),
            )
            for c in np.unique(labels)
        },
    )
