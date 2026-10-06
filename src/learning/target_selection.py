"""Score current unit targets using ability identity and actor-relative geometry."""

import numpy as np
from src.learning.global_imitation import coordinate_signs


def target_features(state, group, ability, unit_types, ability_count, origin):
    units = [u for u in state["units"] if u.get("observed", True)]
    lookup = {kind: index + 1 for index, kind in enumerate(unit_types)}
    count = len(unit_types) + 1
    rows = np.zeros((len(units), 2 * count + ability_count + 5 + 16), np.float32)
    actors = np.asarray([u["position"][:2] for u in group])
    center = actors.mean(axis=0)
    composition = np.zeros(count)
    for actor in group:
        composition[lookup.get(actor["unit_type"], 0)] += 1 / len(group)
    signs = coordinate_signs(state, origin)
    selected = {u["tag"] for u in group}
    history = state.get("recent_commands", [])
    for index, unit in enumerate(units):
        position = np.asarray(unit["position"][:2])
        rows[index, lookup.get(unit["unit_type"], 0)] = 1
        rows[index, count : 2 * count] = composition
        rows[index, 2 * count + ability] = 1
        rows[index, 2 * count + ability_count + unit["alliance"]] = 1
        orders = [o for actor in group for o in actor.get("orders", [])]
        rows[index, -16:] = [
            *((position - center) * signs / 128),
            np.linalg.norm(position - center) / 128,
            np.linalg.norm(actors - position, axis=1).min() / 128,
            unit.get("health", 0) / max(unit.get("health_max", 1), 1),
            unit.get("shield", 0) / 500,
            unit.get("energy", 0) / 200,
            unit.get("weapon_cooldown", 0) / 64,
            unit.get("build_progress", 1),
            float(unit.get("is_flying", False)),
            unit.get("mineral_contents", 0) / 1800,
            unit.get("vespene_contents", 0) / 2250,
            float(unit["tag"] in selected),
            sum(o.get("target_unit_tag") == unit["tag"] for o in orders)
            / max(len(orders), 1),
            float(bool(history) and history[-1].get("target_unit") == unit["tag"]),
            np.log1p(len(group)) / 3,
        ]
    return units, rows


def select_target(policy, features, units):
    if not units:
        return None
    logits = policy.predict(features)["ability"]
    return units[int((logits[:, 1] - logits[:, 0]).argmax())]["tag"]
