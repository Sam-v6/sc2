"""Project partial tournament observations through the native fog filter.

These states remain ineligible for the legacy encoder until explicit missing-field
features and feature-minimap geometry are supported. Original command labels
and completed-upgrade chronology are reconciled separately by the importer.
"""

import numpy as np
from s2clientprotocol import sc2api_pb2 as pb


FIELDS = {
    **{
        name: name
        for name in (
            "health",
            "health_max",
            "shield",
            "shield_max",
            "energy_max",
            "weapon_cooldown",
            "radius",
            "build_progress",
            "assigned_harvesters",
            "ideal_harvesters",
            "is_blip",
            "is_flying",
            "is_burrowed",
            "is_powered",
        )
    },
    "heading": "facing",
    "cargo": "cargo_space_taken",
    "cargo_max": "cargo_space_max",
    "cloak_state": "cloak",
    "tgtId": "engaged_target_tag",
}


def partial_observation(record, index, map_size, view, upgrade_ids=None, own_deaths=()):
    """Preserve known values; map size must come from the verified original map."""
    packet = pb.ResponseObservation()
    obs = packet.observation
    obs.game_loop = int(record["steps"]["game_loop"][index])
    obs.player_common.player_id = record["header"]["player"]
    for source, target in (
        ("minerals", "minerals"),
        ("gas", "vespene"),
        ("cap", "food_cap"),
        ("army", "food_army"),
        ("workers", "food_workers"),
    ):
        setattr(obs.player_common, target, int(record["steps"][source][index]))
    obs.raw_data.player.upgrade_ids.extend(() if upgrade_ids is None else upgrade_ids)
    obs.raw_data.event.dead_units.extend(own_deaths)
    cargo = {}
    for name in ("units", "neutral"):
        block = record[name]
        fields = block["fields"]
        for i in np.flatnonzero(block["step"] == index):
            unit = obs.raw_data.units.add(
                tag=int(fields["id"][i]),
                unit_type=int(fields["unitType"][i]),
                display_type=int(fields["observation"][i]),
                alliance=int(fields["alliance"][i]) if name == "units" else 3,
            )
            unit.pos.x, unit.pos.y, unit.pos.z = map(float, fields["pos"][i])
            if "is_blip" in fields:
                unit.is_blip = bool(fields["is_blip"][i])
            if unit.display_type != 1 or unit.is_blip:
                continue
            for source, target in FIELDS.items():
                if source in fields:
                    value = fields[source][i].item()
                    if isinstance(value, float) and not np.isfinite(value):
                        raise ValueError("Nonfinite tournament unit observation")
                    setattr(unit, target, value)
            if name == "units":
                cargo[unit.tag] = bool(fields["in_cargo"][i])
                unit.buff_ids.extend(
                    int(fields[k][i]) for k in ("buff0", "buff1") if fields[k][i]
                )
                for k in range(4):
                    order = fields[f"order{k}"][i]
                    if not order["ability"]:
                        continue
                    target = unit.orders.add(
                        ability_id=int(order["ability"]),
                        progress=float(order["progress"]),
                    )
                    if order["target_unit"]:
                        target.target_unit_tag = int(order["target_unit"])
                    elif order["x"] or order["y"]:
                        target.target_world_space_pos.x = int(order["x"])
                        target.target_world_space_pos.y = int(order["y"])
    for name in ("visibility", "creep"):
        grid = record["images"][name][index]
        image = getattr(obs.raw_data.map_state, name)
        image.size.x, image.size.y = grid.shape[1], grid.shape[0]
        image.bits_per_pixel = 8 if name == "visibility" else 1
        image.data = (
            grid.tobytes() if name == "visibility" else np.packbits(grid).tobytes()
        )
    state = view.observe(packet, visibility_world_size=map_size)
    for unit in state["units"]:
        if unit["tag"] in cargo:
            unit["in_cargo"] = cargo[unit["tag"]]
    state["map_size"] = list(map_size)
    state["unknown_fields"] = {
        "player": ["food_used", "idle_worker_count", "army_count"],
        "units": [
            "energy",
            "owner",
            "add_on_tag",
            "passengers",
            "buffs_beyond_two",
            "orders_beyond_four",
            "order_target_presence_at_origin",
            "order_target_point_precision",
            "neutral_resource_kind_and_current_contents",
        ],
        "world": ["effects", "radar_sweeps", "dead_units", "command_history"],
    }
    if upgrade_ids is None:
        state["unknown_fields"]["world"].append("upgrades")
    for image in state["map"].values():
        image.update(
            coordinate_system="feature_minimap",
            world_size=list(map_size),
            transform="world_y_flip_then_uniform_max_dimension_scale",
        )
    # Keep the decoder's partiality explicit rather than pretending native grids.
    state["source_grid_resolution"] = [128, 128]
    return state
