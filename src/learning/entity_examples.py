"""Compact causal inputs and reversible labels for human raw commands."""

import json

import numpy as np

from src.learning.actor_selection import worker_construction_features
from src.learning.gameplay import Command


def state_inputs(
    state,
    unit_count,
    ability_count,
    upgrade_count=0,
    products=None,
    cell_size=8,
    terrain=None,
):
    size = np.asarray(state["map_size"], dtype=float)
    loop = state.get("decision_loop", state["game_loop"])
    history = state.get("recent_commands", [])[-32:]
    if any(c["game_loop"] > loop for c in history):
        raise ValueError("Command history must precede the decision")
    visible = [
        u
        for u in state["units"]
        if u.get("observed", True) and u.get("display_type", 1) == 1
    ]
    known = {u["tag"]: dict(u, observed=True) for u in visible}
    for u in state.get("owned_memory", []):
        known.setdefault(
            u["tag"],
            {
                k: u[k]
                for k in ("tag", "unit_type", "position", "alliance", "last_seen_loop")
                if k in u
            },
        )
    for u in state.get("memory", []):
        known.setdefault(
            u["tag"],
            dict(
                tag=u["tag"],
                unit_type=u["unit_type"],
                position=u["position"],
                alliance=4,
                last_seen_loop=u.get("last_seen_loop"),
            ),
        )
    units = [known[tag] for tag in sorted(known)]
    tags = tuple(u["tag"] for u in units)
    features, types, orders = [], [], []
    actor_mask, target_mask = [], []
    for unit in units:
        observed = unit.get("observed", False)
        own = unit["alliance"] == 1
        actor_mask.append(own)
        target_mask.append(observed)
        kind = unit["unit_type"]
        if not 0 <= kind < unit_count:
            raise ValueError("Unit type outside engine vocabulary")
        queue = unit.get("orders", [])
        order = queue[0] if queue else {}
        ability = order.get("ability_id", 0)
        if not 0 <= ability < ability_count:
            raise ValueError("Order ability outside engine vocabulary")
        types.append(kind)
        orders.append(ability)
        position = np.asarray(unit["position"][:2]) / size
        target = known.get(order.get("target_unit_tag"))
        point = order.get("target_world_space_pos")
        target_position = (
            [point["x"], point["y"]]
            if point
            else target["position"][:2]
            if target
            else [0, 0]
        )
        age = (
            loop - unit.get("last_seen_loop", loop)
            if unit.get("last_seen_loop") is not None
            else 0
        )
        row = [
            *position,
            float(own),
            float(unit["alliance"] == 4),
            float(unit["alliance"] == 3),
            float(observed),
            max(age, 0) / 1344,
            unit.get("health", 0) / 1000,
            unit.get("health", 0) / max(unit.get("health_max", 1), 1),
            unit.get("shield", 0) / 500,
            unit.get("energy", 0) / 200,
            unit.get("build_progress", 0),
            unit.get("weapon_cooldown", 0) / 64,
            float(unit.get("is_flying", False)),
            float(unit.get("is_burrowed", False)),
            unit.get("mineral_contents", 0) / 1800,
            unit.get("vespene_contents", 0) / 2250,
            unit.get("assigned_harvesters", 0) / 24,
            unit.get("ideal_harvesters", 0) / 24,
            len(queue) / 5,
            order.get("progress", 0),
            *(np.asarray(target_position) / size),
            float(bool(point) or target is not None),
            float(not queue),
            *worker_construction_features(state, unit, products or {}),
        ]
        references = np.zeros((32, 2), dtype=np.float32)
        for i, command in enumerate(history, 32 - len(history)):
            references[i] = [
                float(unit["tag"] in command["units"]),
                float(unit["tag"] == command.get("target_unit")),
            ]
        features.append([*row, *references.ravel()])
    # Thirty compact numeric fields plus all 32 actor/target references.
    entity_features = np.asarray(features, np.float32).reshape(len(units), 94)
    roles = []
    for command in history:
        point = command.get("target_point") or command.get("target_position")
        target = known.get(command.get("target_unit"))
        if not point and target:
            point = target["position"][:2]
        mode = (
            3
            if command.get("autocast")
            else 1
            if command.get("target_unit") is not None
            else 2
            if command.get("target_point") is not None
            else 0
        )
        roles.append(
            [
                float(command.get("queue", False)),
                *[float(mode == i) for i in range(4)],
                *(np.asarray(point or [0, 0])[:2] / size),
                np.log1p(len(command["units"])) / 3,
                max(loop - command["game_loop"], 0) / 1344,
            ]
        )
    player = state["player"]
    scene = [
        loop / 13440,
        *(size / 256),
        *[
            player.get(k, 0) / scale
            for k, scale in (
                ("minerals", 2000),
                ("vespene", 2000),
                ("food_cap", 200),
                ("food_used", 200),
                ("food_army", 200),
                ("food_workers", 100),
                ("idle_worker_count", 100),
                ("army_count", 200),
            )
        ],
        len(visible) / 200,
        sum(actor_mask) / 200,
    ]
    upgrades = np.zeros(upgrade_count, np.float32)
    for upgrade in state.get("upgrades", []):
        if not 0 <= upgrade < upgrade_count:
            raise ValueError("Upgrade outside engine vocabulary")
        upgrades[upgrade] = 1
    axes = []
    radii = []
    for extent in size:
        starts = np.arange(0, extent, cell_size)
        ends = np.minimum(starts + cell_size, extent)
        axes.append((starts + ends) / 2)
        radii.append((ends - starts) / 2)
    world_points = np.array([(x, y) for y in axes[1] for x in axes[0]], np.float32)
    point_radii = np.array([(x, y) for y in radii[1] for x in radii[0]], np.float32)
    inputs = dict(
        encoder=(
            entity_features,
            np.array(types, int),
            np.array(orders, int),
            np.concatenate((scene, upgrades)).astype(np.float32),
            np.array([c["ability"] for c in history], int),
            np.asarray(roles, np.float32).reshape(len(history), 9),
        ),
        tags=tags,
        actor_mask=np.array(actor_mask, bool),
        target_mask=np.array(target_mask, bool),
        points=world_points / size,
        world_points=world_points,
        point_radii=point_radii,
    )
    if terrain is not None:
        from src.learning.entity_spatial import spatial_features

        inputs["point_features"] = spatial_features(
            state, terrain, world_points, point_radii, cell_size
        )
    return inputs


def command_label(command, inputs, delays, delay):
    command.to_proto()
    tags = inputs["tags"]
    if any(
        tag not in tags or not inputs["actor_mask"][tags.index(tag)]
        for tag in command.units
    ):
        raise ValueError("Unknown or ineligible human actor")
    label = dict(
        ability=command.ability,
        actors=tuple(tags.index(tag) for tag in command.units),
        mode=3
        if command.autocast
        else 1
        if command.target_unit is not None
        else 2
        if command.target_point is not None
        else 0,
        queue=int(command.queue),
        delay=None
        if delay is None
        else int(np.argmin(abs(np.asarray(delays) - delay))),
    )
    if command.target_unit is not None:
        if (
            command.target_unit not in tags
            or not inputs["target_mask"][tags.index(command.target_unit)]
        ):
            raise ValueError("Human target is outside observed candidates")
        label["target"] = tags.index(command.target_unit)
    elif command.target_point is not None:
        point = np.asarray(command.target_point)
        offsets = (point - inputs["world_points"]) / inputs["point_radii"]
        cells = np.flatnonzero(np.all(abs(offsets) <= 1 + 1e-6, axis=1))
        if not len(cells):
            raise ValueError("Human point is outside map candidates")
        label["point"] = int(cells[0])
        label["offset"] = offsets[cells[0]]
    return label


def decode_command(prediction, inputs):
    tags = inputs["tags"]
    mode = prediction["mode"]
    point = None
    if mode == 2:
        index = prediction["point"]
        point = tuple(
            float(x)
            for x in inputs["world_points"][index]
            + np.asarray(prediction["offset"]) * inputs["point_radii"][index]
        )
    return Command(
        prediction["ability"],
        tuple(tags[i] for i in prediction["actors"]),
        target_unit=tags[prediction["target"]] if mode == 1 else None,
        target_point=point,
        queue=bool(prediction["queue"]) if mode != 3 else False,
        autocast=mode == 3,
    )


def replay_examples(
    directory,
    unit_count,
    ability_count,
    upgrade_count,
    delays,
    products=None,
    spatial=False,
):
    """Keep all burst commands; only the last inherits the next event gap.

    Unrepresentable labels are returned as None with an explicit exclusion reason.
    Each burst uses the recorded pre-command observation. Earlier commands in
    that same burst become known history, without inventing new observations.
    """
    from src.learning.teacher_states import teacher_states, remember_command

    terrain = (
        json.loads((directory / "static.json").read_text())["terrain"]
        if spatial
        else None
    )
    for row, state in teacher_states(directory):
        state = dict(
            state,
            decision_loop=row["action_loop"],
            recent_commands=list(state["recent_commands"]),
        )
        for index, raw in enumerate(row["commands"]):
            inputs = state_inputs(
                state,
                unit_count,
                ability_count,
                upgrade_count,
                products,
                terrain=terrain,
            )
            command = Command(
                **dict(
                    raw,
                    units=tuple(raw["units"]),
                    target_point=tuple(raw["target_point"])
                    if raw.get("target_point") is not None
                    else None,
                )
            )
            delay = row["next_action_delay"] if index == len(row["commands"]) - 1 else 0
            try:
                label = command_label(command, inputs, delays, delay)
                exclusion = None
            except ValueError as error:
                label, exclusion = None, str(error)
            yield inputs, label, command, exclusion
            state["recent_commands"].append(
                remember_command(raw, state, row["action_loop"])
            )
