"""Individual learned membership for arbitrary current own-unit groups."""

import numpy as np
from src.learning.global_imitation import coordinate_signs
from src.learning.imitation import unit_features


def actor_features(state, unit, index, unit_types, abilities, origin, context):
    features = unit_features(state, unit, unit_types)
    signs = coordinate_signs(state, origin)
    features[7:9] = (np.asarray(unit["position"][:2]) - origin) * signs / 128.0
    features[19:21] *= signs
    orders = unit.get("orders", [])
    order_ability = np.zeros(abilities, dtype=np.float32)
    target_type = np.zeros(len(unit_types) + 1, dtype=np.float32)
    target_point = np.zeros(2, dtype=np.float32)
    if orders:
        order = orders[0]
        ability = order.get("ability_id", 0)
        if ability < abilities:
            order_ability[ability] = 1.0
        if order.get("target_unit_tag"):
            target = next(
                (u for u in state["units"] if u["tag"] == order["target_unit_tag"]),
                None,
            )
            if target:
                target_type[
                    unit_types.index(target["unit_type"]) + 1
                    if target["unit_type"] in unit_types
                    else 0
                ] = 1.0
                target_point = (
                    (np.asarray(target["position"][:2]) - origin) * signs / 128.0
                )
        elif order.get("target_world_space_pos"):
            point = order["target_world_space_pos"]
            target_point = (
                (np.asarray([point["x"], point["y"]]) - origin) * signs / 128.0
            )
    last = state.get("recent_commands", [])
    selected = float(bool(last) and unit["tag"] in last[-1]["units"])
    return np.concatenate(
        (
            features,
            order_ability,
            target_type,
            target_point,
            [index / 200.0, selected],
            context,
        )
    ).astype(np.float32)


def select_actors(actors, logits, available, ability):
    eligible = [
        (unit, logits[index, 1] - logits[index, 0])
        for index, unit in enumerate(actors)
        if ability in available.get(unit["tag"], set())
    ]
    if not eligible:
        return []
    selected = [unit for unit, score in eligible if score > 0.0]
    # Every issued non-wait command needs an actor; there is no group-size cap.
    return selected or [max(eligible, key=lambda pair: pair[1])[0]]


def group_features(state, group, unit_types, abilities, origin, context):
    from src.learning.teacher_states import own_actors

    indices = {u["tag"]: i for i, u in enumerate(own_actors(state))}
    rows = [
        actor_features(
            state, u, indices[u["tag"]], unit_types, abilities, origin, context
        )
        for u in group
    ]
    return np.concatenate(
        (np.stack(rows).mean(axis=0), [np.log1p(len(group)) / 3.0])
    ).astype(np.float32)
