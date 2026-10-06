"""Availability features for partial replay observations and native gameplay."""

import numpy as np


PLAYER_FIELDS = (
    "minerals",
    "vespene",
    "food_cap",
    "food_used",
    "food_army",
    "food_workers",
    "idle_worker_count",
    "army_count",
)
UNIT_FIELDS = {
    7: ("health",),
    8: ("health", "health_max"),
    9: ("shield",),
    10: ("energy",),
    11: ("build_progress",),
    12: ("weapon_cooldown",),
    13: ("is_flying",),
    14: ("is_burrowed",),
    15: ("mineral_contents",),
    16: ("vespene_contents",),
    17: ("assigned_harvesters",),
    18: ("ideal_harvesters",),
}


def without_unknown_values(state):
    unknown = state.get("unknown_fields", {})
    world = unknown.get("world", [])
    if "command_history" in world and state.get("recent_commands"):
        raise ValueError("Unknown command history cannot supply verified references")
    omitted = set(unknown.get("units", []))
    if "neutral_resource_kind_and_current_contents" in omitted:
        omitted.update(("mineral_contents", "vespene_contents"))
    return dict(
        state,
        player={
            k: v
            for k, v in state["player"].items()
            if k not in unknown.get("player", [])
        },
        units=[
            {k: v for k, v in unit.items() if k not in omitted}
            for unit in state["units"]
        ],
        upgrades=[] if "upgrades" in world else state.get("upgrades", []),
    )


def append_availability(state, units, encoder):
    entities, types, orders, scene, history, roles = encoder
    unknown = state.get("unknown_fields", {})
    omitted = set(unknown.get("units", []))
    world = unknown.get("world", [])
    masks = np.ones_like(entities)
    for i, unit in enumerate(units):
        observed = unit.get("observed", False)
        if not observed:
            masks[i, 7:30] = 0
        for column, fields in UNIT_FIELDS.items():
            if omitted.intersection(fields):
                masks[i, column] = 0
        if "neutral_resource_kind_and_current_contents" in omitted:
            masks[i, 15:17] = 0
        queue = unit.get("orders", [])
        if "orders_beyond_four" in omitted and len(queue) >= 4:
            masks[i, 19] = 0
        if (
            "order_target_point_precision" in omitted
            and queue
            and queue[0].get("target_world_space_pos")
        ):
            masks[i, 21:23] = 0
            masks[i, 26:30] = 0
        if (
            "order_target_presence_at_origin" in omitted
            and queue
            and not (
                queue[0].get("target_unit_tag")
                or queue[0].get("target_world_space_pos")
            )
        ):
            masks[i, 21:24] = 0
            masks[i, 26:30] = 0
        if "command_history" in world:
            masks[i, 30:] = 0
    scene_mask = np.ones_like(scene)
    for i, name in enumerate(PLAYER_FIELDS, 3):
        if name in unknown.get("player", []):
            scene_mask[i] = 0
    if "upgrades" in world:
        scene_mask[13:] = 0
    # Unknown values never reach the model, even when a source supplied them.
    return (
        np.concatenate((np.where(masks, entities, 0), masks), axis=1),
        types,
        orders,
        np.concatenate((np.where(scene_mask, scene, 0), scene_mask)),
        history,
        roles,
    )
