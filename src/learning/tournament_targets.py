"""Translate converter-normalized resource identities in supervised labels only."""

from dataclasses import replace


def normalized_resource_target(command, event, state, original_type, resource_types):
    """Require a causal tracker type and unique exact visible resource position.

    Converter resource tags are stable first-observed IDs, unlike live engine
    tags. Never use this label translation in native command execution.
    """
    target = event["m_data"].get("TargetUnit")
    if (
        command.target_unit is None
        or target is None
        or command.target_unit & 0xFFFFFFFF != target["m_tag"]
        or original_type not in resource_types
        or target["m_snapshotControlPlayerId"] != 0
        or target["m_snapshotUpkeepPlayerId"] != 0
        or any(u["tag"] == command.target_unit for u in state["units"])
    ):
        return command, None
    point = [target["m_snapshotPoint"][axis] / 4096 for axis in ("x", "y")]
    candidates = [
        u
        for u in state["units"]
        if u["alliance"] == 3
        and u["unit_type"] == original_type
        and u.get("display_type", 1) == 1
        and u.get("observed", True)
        and not u.get("is_blip", False)
        and list(u["position"][:2]) == point
    ]
    if len(candidates) != 1:
        return command, None
    source_tag = candidates[0]["tag"]
    return replace(command, target_unit=source_tag), dict(
        original_tag=command.target_unit,
        source_tag=source_tag,
        unit_type=original_type,
        position=point,
    )
