"""Translate converter-normalized resource identities in supervised labels only."""

from dataclasses import replace
from copy import deepcopy
from math import floor
from src.learning.gameplay import Command


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


def refinery_snapshot_label(*, event, action, actor, resources, map_resource,
                            resource_types, raw_name):
    """Label a zero-tag neutral snapshot only through observed/snapshot and original-map geometry."""
    target = event['m_data'].get('TargetUnit')
    if (event['m_cmdFlags'] != 256 or action['ability'] != 320
            or action['target_type'] != 1 or len(action['tags']) != 1
            or actor['tag'] != action['tags'][0] or actor['alliance'] != 1
            or actor['name'] != 'SCV' or raw_name.replace(' ', '') != 'BuildRefinery'
            or event['m_abil']['m_abilCmdIndex'] != 2 or target is None
            or target['m_tag'] != 0 or target['m_snapshotControlPlayerId'] != 0
            or target['m_snapshotUpkeepPlayerId'] != 0):
        return None
    point = [target['m_snapshotPoint'][axis] / 4096 for axis in ('x', 'y')]
    candidates = [u for u in resources if u['alliance'] == 3
                  and u.get('display_type', 1) in (1, 2) and not u.get('is_blip', False)
                  and u['unit_type'] in resource_types and u['position'][:2] == point]
    if len(candidates) != 1 or candidates[0]['tag'] != action['target']:
        return None
    name = resource_types[candidates[0]['unit_type']]
    if (map_resource['_gameloop'] != 0 or map_resource['m_upkeepPlayerId'] != 0
            or map_resource['m_controlPlayerId'] != 0
            or map_resource['m_unitTypeName'].decode() != name
            or [map_resource['m_x'], map_resource['m_y']] != list(map(floor, point))):
        return None
    return Command(320, tuple(action['tags']), target_unit=action['target']), dict(
        kind='neutral_snapshot_target_equivalence', source_event=deepcopy(event),
        resource=deepcopy(candidates[0]),
        map_resource=dict(deepcopy(map_resource), m_unitTypeName=name),
        snapshot_type_link='uninterpreted', evidence_is_label_only=True,
        target_observed=candidates[0].get('display_type', 1) == 1,
        target_requires_representation_check=True,
    )
