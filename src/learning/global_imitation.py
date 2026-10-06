"""Shared command decisions with learned unit groups, spatial arguments and timing."""

import numpy as np
from collections import Counter
from src.learning.imitation import unit_features, action_labels


def coordinate_signs(state, origin):
    return np.where(np.asarray(origin) > np.asarray(state["map_size"]) / 2.0, -1.0, 1.0)


def entity_summary(state, unit_types, abilities, origin, canonical, semantics=False):
    lookup = {kind: index for index, kind in enumerate(unit_types)}
    summary = np.zeros((2, len(unit_types), 12 if semantics else 10), dtype=np.float32)
    orders = np.zeros(abilities, dtype=np.float32)
    signs = coordinate_signs(state, origin) if canonical else np.ones(2)
    for unit in state["units"]:
        if unit["alliance"] not in (1, 4) or unit["unit_type"] not in lookup:
            continue
        side = 0 if unit["alliance"] == 1 else 1
        position = (np.asarray(unit["position"][:2]) - origin) * signs / 128.0
        queue = unit.get("orders", [])
        summary[side, lookup[unit["unit_type"]]] += np.array(
            [
                1.0,
                *position,
                unit.get("health", 0) / max(unit.get("health_max", 1), 1),
                unit.get("energy", 0) / 200.0,
                unit.get("weapon_cooldown", 0) / 64.0,
                unit.get("build_progress", 1.0),
                len(queue) / 5.0,
                queue[0].get("progress", 0) if queue else 0.0,
                float(not queue),
            ]
            + (
                [
                    unit.get("assigned_harvesters", 0) / 24.0,
                    unit.get("ideal_harvesters", 0) / 24.0,
                ]
                if semantics
                else []
            )
        )
        if side == 0:
            for order in queue:
                ability = order.get("ability_id", 0)
                if ability < abilities:
                    orders[ability] += 0.05
    counts = summary[:, :, :1].copy()
    summary[:, :, 1:] /= np.maximum(counts, 1.0)
    summary[:, :, 0] *= 0.05
    return np.concatenate((summary.ravel(), orders))


def global_features(
    state,
    unit_types,
    abilities,
    canonical=False,
    summarize=False,
    semantics=False,
    upgrade_count=0,
):
    own = [u for u in state["units"] if u["alliance"] == 1]
    bases = [u for u in own if u["unit_type"] in (18, 36, 130, 132, 134)]
    origin = (
        np.asarray(min(bases or own, key=lambda u: u["tag"])["position"][:2])
        if own
        else np.zeros(2)
    )
    proxy = {
        "tag": 0,
        "unit_type": 0,
        "position": [*origin, 0.0],
        "health": 0.0,
        "health_max": 1.0,
    }
    lookup = {kind: index for index, kind in enumerate(unit_types)}
    enemies = np.zeros(len(unit_types), dtype=np.float32)
    for unit in state["units"]:
        if unit["alliance"] == 4 and unit["unit_type"] in lookup:
            enemies[lookup[unit["unit_type"]]] += 0.05
    history = np.zeros(abilities * 2, dtype=np.float32)
    for index, command in enumerate(reversed(state.get("recent_commands", [])[-2:])):
        if command["ability"] < abilities:
            history[index * abilities + command["ability"]] = 1.0
    entity = unit_features(state, proxy, unit_types)
    if canonical:
        entity[7:9] = 0.0
        entity[19:21] *= coordinate_signs(state, origin)
    components = [entity, enemies, history]
    if summarize:
        components.append(
            entity_summary(state, unit_types, abilities, origin, canonical, semantics)
        )
    if semantics:
        signs = coordinate_signs(state, origin) if canonical else np.ones(2)
        roles = np.zeros(
            (4, abilities + 2 * (len(unit_types) + 1) + 14), dtype=np.float32
        )
        kind_index = {kind: index + 1 for index, kind in enumerate(unit_types)}
        for index, command in enumerate(
            reversed(state.get("recent_commands", [])[-4:])
        ):
            row = roles[index]
            ability = command["ability"]
            if 0 <= ability < abilities:
                row[ability] = 1
            actor_types = command.get("actor_types", [])
            for kind in actor_types:
                row[abilities + kind_index.get(kind, 0)] += 1 / max(len(actor_types), 1)
            offset = abilities + len(unit_types) + 1
            row[offset + kind_index.get(command.get("target_type", 0), 0)] = 1
            offset += len(unit_types) + 1
            alliance = command.get("target_alliance", 0)
            if 0 <= alliance < 5:
                row[offset + alliance] = 1
            mode = (
                3
                if command.get("autocast")
                else 2
                if command.get("target_unit") is not None
                else 1
                if command.get("target_point") is not None
                else 0
            )
            row[offset + 5 + mode] = 1
            position = command.get("target_position", [])
            if position:
                row[offset + 9 : offset + 11] = (
                    (np.asarray(position[:2]) - origin) * signs / 128
                )
            row[offset + 11 :] = [
                float(command.get("queue", False)),
                np.log1p(len(command.get("units", []))) / 3,
                max(0, state["game_loop"] - command["game_loop"]) / 1344,
            ]
        upgrades = np.zeros(upgrade_count, dtype=np.float32)
        for upgrade in state.get("upgrades", []):
            if 0 <= upgrade < upgrade_count:
                upgrades[upgrade] = 1
        components.extend((roles.ravel(), upgrades))
    return np.concatenate(components), origin


def global_labels(command, state, unit_types, origin, delay, canonical=False):
    known = {
        u["tag"]: u
        for u in state["units"] + state.get("owned_memory", [])
        if u["alliance"] == 1
    }
    actors = [known[tag] for tag in command["units"] if tag in known]
    if len(actors) != len(command["units"]):
        raise ValueError("Unresolved own actor in global demonstration")
    labels, point = action_labels(
        command, state, {"position": origin}, unit_types, delay
    )
    dominant = Counter(u["unit_type"] for u in actors).most_common(1)[0][0]
    labels["actor_type"] = (
        unit_types.index(dominant) + 1 if dominant in unit_types else 0
    )
    actor_position = np.asarray([u["position"][:2] for u in actors]).mean(axis=0)
    points = np.concatenate(
        (point, (actor_position - origin) / 128.0, [np.log1p(len(actors)) / 3.0])
    )
    if canonical:
        signs = coordinate_signs(state, origin)
        points[:2] *= signs
        points[2:4] *= signs
    return labels, points.astype(np.float32)


def select_group(state, output, available, ability, unit_types, origin):
    actors = [
        u
        for u in state["units"] + state.get("owned_memory", [])
        if u["alliance"] == 1 and ability in available.get(u["tag"], set())
    ]
    if not actors:
        return []
    lookup = {kind: index + 1 for index, kind in enumerate(unit_types)}
    location = np.asarray(origin) + 128 * output["point"][0, 2:4]

    def score(unit):
        return (
            output["actor_type"][0, lookup.get(unit["unit_type"], 0)]
            - 5 * np.linalg.norm(np.asarray(unit["position"][:2]) - location) / 128.0
        )

    log_count = np.clip(output["point"][0, 4] * 3.0, 0.0, np.log1p(len(actors)))
    count = max(1, int(round(np.expm1(log_count))))
    return sorted(actors, key=score, reverse=True)[:count]
