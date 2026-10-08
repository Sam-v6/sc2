"""Label-only canonical addon execution from narrowly verified source effects.

This does not interpret replay flags or add future tracker effects to observations.
The native fixture verifies own-position/no-target equivalence for landed producers.
"""

from copy import deepcopy
from src.learning.gameplay import Command


def in_place_addon_label(*, event, action, actors, selected, starts, player, raw_name):
    if event["m_cmdFlags"] != 0x1000100 or action["target_type"] != 0:
        return None
    product = {3682: "TechLab", 3683: "Reactor"}.get(action["ability"])
    if (
        product is None
        or len(action["tags"]) != 1
        or "TargetPoint" not in event["m_data"]
    ):
        return None
    actor = next((u for u in actors if u["tag"] == action["tags"][0]), None)
    if (
        actor is None
        or actor["alliance"] != 1
        or actor["is_flying"]
        or actor["build_progress"] != 1
        or actor["name"] not in ("Barracks", "Factory", "Starport")
    ):
        return None
    parent = actor["name"]
    if raw_name.replace(" ", "") != "Build" + parent + product or event["m_abil"][
        "m_abilCmdIndex"
    ] != (product == "Reactor"):
        return None
    selected = set(selected or [])
    eligible = [
        u
        for u in actors
        if u["tag"] & 0xFFFFFFFF in selected
        and u["alliance"] == 1
        and u["name"].removesuffix("Flying") == parent
    ]
    if len(eligible) != 1 or eligible[0]["tag"] != actor["tag"]:
        return None
    point = [event["m_data"]["TargetPoint"][axis] / 4096 for axis in ("x", "y")]
    if point != actor["position"][:2]:
        return None
    expected = [point[0] + 2.5, point[1] - 0.5]
    matching = [
        e
        for e in starts
        if e["_gameloop"] == event["_gameloop"]
        and e["m_upkeepPlayerId"] == player
        and e["m_unitTypeName"].decode() == parent + product
        and [e["m_x"], e["m_y"]] == expected
    ]
    if len(matching) != 1:
        return None
    return Command(action["ability"], tuple(action["tags"])), dict(
        kind="observed_in_place_addon_equivalence",
        source_event=deepcopy(event),
        actor=deepcopy(actor),
        selected=sorted(selected),
        addon_start=dict(
            deepcopy(matching[0]), m_unitTypeName=matching[0]["m_unitTypeName"].decode()
        ),
        canonical_target="none",
        flag_semantics="uninterpreted",
        effect_is_label_only=True,
    )
