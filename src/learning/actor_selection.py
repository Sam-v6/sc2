"""Individual learned membership for arbitrary current own-unit groups."""

import numpy as np
from src.learning.global_imitation import coordinate_signs
from src.learning.imitation import unit_features


def construction_products(game_data):
    builds = {
        a["ability_id"]
        for a in game_data["abilities"]
        if a.get("friendly_name", "").startswith("Build ")
    }
    products = {}
    for unit in game_data["units"]:
        ability = unit.get("ability_id")
        if unit.get("race") == 1 and ability in builds:
            products.setdefault(str(ability), []).append(unit["unit_id"])
    return products


def worker_construction_features(state, unit, products):
    """Relate an SCV's first build order to its currently visible foundation."""
    result = np.zeros(5, dtype=np.float32)
    orders = unit.get("orders", [])
    types = products.get(str(orders[0]["ability_id"]), []) if orders else []
    if unit["unit_type"] != 45 or not types:
        return result
    result[0] = 1
    visible = [
        u
        for u in state["units"]
        if u.get("observed", True) and u.get("display_type", 1) == 1
    ]
    order = orders[0]
    point = order.get("target_world_space_pos")
    target = next(
        (u for u in visible if u["tag"] == order.get("target_unit_tag")), None
    )
    point = (
        [point["x"], point["y"]]
        if point
        else target["position"][:2]
        if target
        else None
    )
    if point is None:
        return result
    result[1] = 1
    result[4] = min(np.linalg.norm(np.asarray(unit["position"][:2]) - point) / 32, 2)
    foundations = [
        u
        for u in visible
        if u["alliance"] == 1
        and u["unit_type"] in types
        and np.linalg.norm(np.asarray(u["position"][:2]) - point) <= 1
    ]
    if foundations:
        foundation = min(
            foundations,
            key=lambda u: np.linalg.norm(np.asarray(u["position"][:2]) - point),
        )
        result[2:4] = [1, foundation.get("build_progress", 1)]
    return result


def actor_features(
    state, unit, index, unit_types, abilities, origin, context, build_products=None
):
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
    parts = (
        features,
        order_ability,
        target_type,
        target_point,
        [index / 200.0, selected],
        context,
    )
    if build_products is not None:
        parts += (worker_construction_features(state, unit, build_products),)
    return np.concatenate(parts).astype(np.float32)


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


def group_features(
    state, group, unit_types, abilities, origin, context, build_products=None
):
    from src.learning.teacher_states import own_actors

    indices = {u["tag"]: i for i, u in enumerate(own_actors(state))}
    rows = [
        actor_features(
            state,
            u,
            indices[u["tag"]],
            unit_types,
            abilities,
            origin,
            context,
            build_products,
        )
        for u in group
    ]
    return np.concatenate(
        (np.stack(rows).mean(axis=0), [np.log1p(len(group)) / 3.0])
    ).astype(np.float32)
