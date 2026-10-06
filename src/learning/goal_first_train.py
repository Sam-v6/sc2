"""Bounded, CPU-only supervised fitting for the goal-first controller."""

from collections import Counter
import time

import numpy as np
import torch

from src.learning.entity_examples import decode_command, state_inputs
from src.learning.teacher_states import remember_command


def teaching_support(policy, examples):
    features, scene, roles, types, abilities, points = policy.dimensions
    support = {
        k: np.zeros(n, bool)
        for k, n in (
            ("entity", features),
            ("scene", scene),
            ("history_roles", roles),
            ("types", types),
            ("abilities", abilities),
            ("point", points),
        )
    }
    for x, y in examples:
        entities, unit_types, orders, s, history, r = x["encoder"]
        for name, values in (
            ("entity", entities),
            ("scene", s),
            ("history_roles", r),
            ("point", x.get("point_features", x["points"])),
        ):
            values = np.asarray(values)
            support[name] |= (
                np.any(values != 0, axis=0) if values.ndim == 2 else values != 0
            )
        support["types"][unit_types] = True
        support["abilities"][orders] = True
        support["abilities"][history] = True
        support["abilities"][y["ability"]] = True
    support["abilities"][0] = True
    return support


def fit_goal_first(
    policy, examples, *, epochs, batch_size, rate, seconds, seed, refresh_examples=None
):
    """Fit human targets; optional provider(policy, epoch, deadline) rebuilds inputs.

    Providers must check the monotonic deadline and raise TimeoutError on expiry.
    """
    if not examples or min(epochs, batch_size, rate, seconds) <= 0:
        raise ValueError("Choose a bounded supervised fit with teaching examples")
    if any(p.device.type != "cpu" for p in policy.parameters()):
        raise ValueError("Goal-first training requires CPU parameters")
    started = time.monotonic()
    optimizer = torch.optim.Adam(policy.parameters(), lr=rate)
    rng = np.random.default_rng(seed)
    updates = presentations = completed = 0
    history = []
    status = "completed"
    example_count = len(examples)
    policy.train()
    for epoch in range(epochs):
        if refresh_examples is not None:
            if time.monotonic() - started >= seconds:
                status = "wall_bound"
                break
            policy.eval()
            try:
                with torch.no_grad():
                    examples = refresh_examples(policy, epoch, started + seconds)
            except TimeoutError:
                status = "wall_bound"
                break
            if len(examples) != example_count:
                raise ValueError(
                    "Refreshing history must preserve teaching sample count"
                )
            policy.train()
        order = rng.permutation(len(examples))
        totals = Counter()
        seen = 0
        for begin in range(0, len(order), batch_size):
            if time.monotonic() - started >= seconds:
                status = "wall_bound"
                break
            indices = order[begin : begin + batch_size]
            optimizer.zero_grad(set_to_none=True)
            batch_totals = Counter()
            for index in indices:
                if time.monotonic() - started >= seconds:
                    status = "wall_bound"
                    break
                losses = policy.loss(*examples[index])
                loss = sum(losses.values())
                if not torch.isfinite(loss):
                    raise ValueError("Nonfinite supervised loss")
                (loss / len(indices)).backward()
                batch_totals.update({k: float(v.detach()) for k, v in losses.items()})
            if status == "wall_bound" or time.monotonic() - started >= seconds:
                status = "wall_bound"
                optimizer.zero_grad(set_to_none=True)
                break
            torch.nn.utils.clip_grad_norm_(
                policy.parameters(), 5.0, error_if_nonfinite=True
            )
            optimizer.step()
            updates += 1
            seen += len(indices)
            presentations += len(indices)
            totals.update(batch_totals)
        if seen:
            history.append(
                dict(
                    epoch=epoch + 1,
                    presentations=seen,
                    losses={k: v / seen for k, v in totals.items()},
                )
            )
        if status == "wall_bound":
            break
        completed += 1
    policy.eval()
    if any(not torch.isfinite(p).all() for p in policy.parameters()):
        raise ValueError("Nonfinite fitted parameters")
    return dict(
        status=status,
        epochs_completed=completed,
        updates=updates,
        presentations=presentations,
        optimizer_seconds=time.monotonic() - started,
        history=history,
    )


def _history_rows(examples, rows):
    previous_loop = None
    for index, (example, (row, observed)) in enumerate(
        zip(examples, rows, strict=True)
    ):
        command = example[2]
        if observed["game_loop"] != row["action_loop"]:
            raise ValueError("Prediction history requires causal issue-loop states")
        if row["commands"] != [command.as_dict()] or (
            previous_loop is not None and row["action_loop"] < previous_loop
        ):
            raise ValueError(
                "Prediction history requires aligned chronological commands"
            )
        previous_loop = row["action_loop"]
        yield index, example, row, observed


def _history_inputs(original, row, observed, history, vocabulary, products):
    state = dict(
        observed,
        decision_loop=row["action_loop"],
        recent_commands=list(history),
        history_quality="event_slots",
    )
    inputs = state_inputs(state, *vocabulary, products=products, missing_fields=True)
    if inputs["tags"] != original["tags"]:
        raise ValueError("Prediction history changed candidate identity")
    for component in (1, 2, 3):
        np.testing.assert_array_equal(
            inputs["encoder"][component], original["encoder"][component]
        )
    np.testing.assert_array_equal(
        inputs["encoder"][0][:, :30], original["encoder"][0][:, :30]
    )
    np.testing.assert_array_equal(
        inputs["encoder"][0][:, 94:124], original["encoder"][0][:, 94:124]
    )
    for name in (
        "actor_mask",
        "target_mask",
        "entity_positions",
        "points",
        "world_points",
        "point_radii",
    ):
        np.testing.assert_array_equal(inputs[name], original[name])
    if "point_features" in original:
        inputs["point_features"] = original["point_features"]
    return inputs


def retained_history_examples(examples, rows, vocabulary, products):
    """Teaching inputs from previous retained human commands only.

    Match the agent's command window, excluding unresolved source event slots.
    Labels remain unchanged; append each command after constructing its inputs.
    """
    history, rebuilt = [], []
    for _, (original, label, command, exclusion), row, observed in _history_rows(
        examples, rows
    ):
        inputs = _history_inputs(original, row, observed, history, vocabulary, products)
        rebuilt.append((inputs, label, command, exclusion))
        remembered = dict(
            remember_command(command.as_dict(), observed, row["action_loop"]),
            verified=True,
        )
        history = [*history, remembered][-32:]
    return rebuilt


def prediction_history_examples(policy, examples, rows, vocabulary, products):
    """Own predictions at human decision times, on unchanged human game states.

    Rebuild both event embeddings and entity references, removing human history.
    Commands are hypothetical, not engine-executed; this is not a native rollout.
    """
    return _mixed_history_examples(
        policy, examples, rows, vocabulary, products, human_probability=0, seed=0
    )


def mixed_history_examples(
    policy,
    examples,
    rows,
    vocabulary,
    products,
    *,
    human_probability,
    seed,
    deadline=None,
):
    """Supervised inputs with causal human or hypothetical predicted history.

    Labels/world states stay human. Choose which command to remember only after
    constructing the current input; this does not execute commands in SC2.
    A supplied monotonic deadline is checked before each row.
    """
    return _mixed_history_examples(
        policy,
        examples,
        rows,
        vocabulary,
        products,
        human_probability=human_probability,
        seed=seed,
        deadline=deadline,
    )[0]


def _mixed_history_examples(
    policy,
    examples,
    rows,
    vocabulary,
    products,
    *,
    human_probability,
    seed,
    deadline=None,
):
    if not 0 <= human_probability <= 1:
        raise ValueError("Human history probability must be between zero and one")
    rng = np.random.default_rng(seed)
    history, rebuilt, records = [], [], []
    for index, (original, label, command, exclusion), row, observed in _history_rows(
        examples, rows
    ):
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError("History generation reached its deadline")
        inputs = _history_inputs(original, row, observed, history, vocabulary, products)
        prediction = policy.predict(inputs)
        records.append(
            dict(row=index, prior_prediction_events=len(history), prediction=prediction)
        )
        rebuilt.append((inputs, label, command, exclusion))
        if rng.random() < human_probability:
            remembered = dict(
                remember_command(command.as_dict(), observed, row["action_loop"]),
                verified=True,
            )
            history = [*history, remembered][-32:]
        elif prediction is not None:
            actual = decode_command(prediction, inputs)
            remembered = dict(
                actual.as_dict(), game_loop=row["action_loop"], verified=True
            )
            if actual.target_unit is not None:
                remembered["target_position"] = inputs["entity_positions"][
                    inputs["tags"].index(actual.target_unit)
                ].tolist()
            history = [*history, remembered][-32:]
    return rebuilt, records
