"""Optional supervised actor-head optimization with frozen, compact features."""

import time

import numpy as np


def actor_weights(policy):
    return np.column_stack(
        (
            policy.heads["actor"],
            policy.heads["actor_geometry"],
            policy.heads["actor_cutoff"],
        )
    ).astype(np.float64)


def actor_cache(policy, examples):
    if not (policy.actor_geometry and policy.actor_cutoff and policy.refinement) or (
        policy.actor_count or policy.actor_nonlinear or policy.actor_context_query
    ):
        raise ValueError(
            "Actor fitting requires the linear geometry/cutoff score family"
        )
    contexts, features, gold, counts = [], [], [], []
    for inputs, label in examples:
        scores, c = policy._forward(inputs, label["ability"], tuple(label["actors"]))
        eligible = np.flatnonzero(inputs["actor_mask"])
        f = np.column_stack(
            (
                c["entities"][eligible],
                c["actor_geometry"][eligible],
                np.ones(len(eligible)),
            )
        ).astype(np.float64)
        np.testing.assert_allclose(
            f @ (c["conditioned"] @ actor_weights(policy)),
            scores["actor"][eligible],
            atol=2e-5,
            rtol=2e-5,
        )
        contexts.append(c["conditioned"])
        features.append(f)
        gold.append(np.isin(eligible, label["actors"]).astype(float))
        counts.append(len(eligible))
    if not counts:
        raise ValueError("Actor fitting requires teaching examples")
    return dict(
        contexts=np.asarray(contexts, np.float64),
        features=np.concatenate(features),
        gold=np.concatenate(gold),
        counts=np.asarray(counts),
        starts=np.cumsum([0, *counts[:-1]]),
        owners=np.repeat(np.arange(len(counts)), counts),
    )


def actor_objective(weights, cache):
    if not np.isfinite(weights).all():
        raise ValueError("Nonfinite actor weights")
    c = cache
    logits = np.sum(c["features"] * (c["contexts"] @ weights)[c["owners"]], axis=1)
    starts, owners, gold = c["starts"], c["owners"], c["gold"]
    selected = np.add.reduceat(gold, starts)
    sums = np.add.reduceat(gold * logits, starts)
    maxima = np.maximum.reduceat(logits, starts)
    exponentials = np.exp(logits - maxima[owners])
    totals = np.add.reduceat(exponentials, starts)
    bce = np.add.reduceat(np.logaddexp(0, logits) - gold * logits, starts) / c["counts"]
    rank = np.log(totals) + maxima - sums / selected - np.log(selected)
    delta = (
        (np.exp(-np.logaddexp(0, -logits)) - gold) / c["counts"][owners]
        + exponentials / totals[owners]
        - gold / selected[owners]
    )
    per_command = np.add.reduceat(c["features"] * delta[:, None], starts, axis=0)
    gradient = c["contexts"].T @ per_command / len(starts)
    loss = float(np.mean(bce + rank))
    if not np.isfinite(loss) or not np.isfinite(gradient).all():
        raise ValueError("Nonfinite actor objective/gradient")
    return loss, gradient


def fit_actor_heads(policy, cache, *, optimizer, iterations, seconds):
    """Update only selection heads; a wall bound retains the best evaluated point."""
    if policy.actor_context_query:
        raise ValueError(
            "The linear actor fitter does not support context query residuals"
        )
    if optimizer not in ("adam", "lbfgs") or iterations <= 0 or seconds <= 0:
        raise ValueError("Choose a bounded Adam or L-BFGS actor fit")
    initial = actor_weights(policy)
    initial_loss = actor_objective(initial, cache)[0]
    weights = initial.copy()
    best, best_loss = weights.copy(), initial_loss
    evaluations = updates = 0
    start = time.monotonic()

    class WallBound(Exception):
        pass

    def evaluate(vector):
        nonlocal evaluations, best, best_loss
        if time.monotonic() - start >= seconds:
            raise WallBound
        matrix = vector.reshape(initial.shape)
        value, gradient = actor_objective(matrix, cache)
        evaluations += 1
        if value < best_loss:
            best, best_loss = matrix.copy(), value
        return value, gradient.ravel()

    status, message = "completed", None
    try:
        if optimizer == "adam":
            m, v = np.zeros_like(weights), np.zeros_like(weights)
            for step in range(1, iterations + 1):
                _, g = evaluate(weights.ravel())
                g = g.reshape(weights.shape)
                g *= min(1.0, 5 / max(np.linalg.norm(g), 1e-8))
                m = 0.9 * m + 0.1 * g
                v = 0.999 * v + 0.001 * g**2
                weights -= (
                    0.001
                    * (m / (1 - 0.9**step))
                    / (np.sqrt(v / (1 - 0.999**step)) + 1e-8)
                )
                updates = step
        else:
            from scipy.optimize import minimize

            def callback(vector):
                nonlocal updates
                updates += 1
                if time.monotonic() - start >= seconds:
                    raise WallBound

            result = minimize(
                evaluate,
                initial.ravel(),
                jac=True,
                method="L-BFGS-B",
                callback=callback,
                options=dict(maxiter=iterations, maxls=20, gtol=1e-8, ftol=1e-12),
            )
            weights = result.x.reshape(initial.shape)
            updates, message = int(result.nit), str(result.message)
            if not result.success:
                status = "iteration_bound" if result.status == 1 else "solver_stopped"
    except WallBound:
        status, weights = "wall_bound", best
    elapsed = time.monotonic() - start
    if not np.isfinite(weights).all():
        raise ValueError("Nonfinite fitted actor weights")
    h = initial.shape[0]
    policy.heads["actor"][:] = weights[:, :h]
    policy.heads["actor_geometry"][:] = weights[:, h : h + 4]
    policy.heads["actor_cutoff"][:] = weights[:, -1]
    actual = actor_weights(policy)
    return dict(
        status=status,
        message=message,
        iterations=updates,
        evaluations=evaluations,
        optimizer_seconds=elapsed,
        initial_objective=initial_loss,
        final_objective=actor_objective(actual, cache)[0],
        parameter_norm=float(np.linalg.norm(actual)),
        parameter_max=float(np.abs(actual).max()),
    )
