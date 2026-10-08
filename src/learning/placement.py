"""Resolve modeled construction points against actual engine placement rules."""

from dataclasses import replace
import math
from s2clientprotocol import query_pb2 as query, common_pb2 as common


def candidates(point, state):
    points = {tuple(point)}
    aligned = tuple(round(axis * 2) / 2 for axis in point)
    for x in range(-8, 9):
        for y in range(-8, 9):
            points.add((aligned[0] + x / 2, aligned[1] + y / 2))
    # Resource-requiring construction can use only currently visible resource
    # positions. These remain candidates, never a chosen expansion/build order.
    points.update(
        tuple(u["position"][:2])
        for u in state["units"]
        if u["alliance"] == 3 and u.get("vespene_contents", 0) > 0
    )
    width, height = state["map_size"]
    return sorted(
        (p for p in points if 0 <= p[0] < width and 0 <= p[1] < height),
        key=lambda p: (math.dist(p, point), p),
    )


async def resolve_placements(client, commands, catalog, state, ranked_points=None):
    resolved = []
    trace = []
    for command in commands:
        descriptor = catalog[command.ability]
        unit_target = command.target_point is None and command.target_unit is not None
        if not descriptor.get("is_building") or (
            command.target_point is None and not unit_target
        ):
            resolved.append(command)
            continue
        target = None
        if unit_target:
            target = next(
                (
                    u
                    for u in state["units"]
                    if u["tag"] == command.target_unit
                    and u.get("observed", True)
                    and u.get("display_type", 1) == 1
                ),
                None,
            )
            if target is None:
                trace.append(
                    dict(
                        ability=command.ability,
                        units=list(command.units),
                        requested_target_unit=command.target_unit,
                        source="engine_unit_target_placement",
                        rejected="unobserved_construction_target",
                    )
                )
                continue
        learned = (
            not unit_target
            and ranked_points is not None
            and (command.ability, command.units) in ranked_points
        )
        points = (
            [tuple(target["position"][:2])]
            if unit_target
            else (
                ranked_points[(command.ability, command.units)]
                if learned
                else candidates(command.target_point, state)
            )
        )
        request = query.RequestQuery(
            placements=[
                query.RequestQueryBuildingPlacement(
                    ability_id=command.ability,
                    placing_unit_tag=command.units[0],
                    target_pos=common.Point2D(x=p[0], y=p[1]),
                )
                for p in points
            ],
            ignore_resource_requirements=False,
        )
        response = (await client._execute(query=request)).query
        if len(response.placements) != len(points):
            raise ValueError("Incomplete engine placement response")
        index = next(
            (i for i, p in enumerate(response.placements) if p.result == 1), None
        )
        row = {
            "ability": command.ability,
            "units": list(command.units),
            "requested_point": list(points[0] if unit_target else command.target_point),
            "source": "learned_spatial_candidates"
            if learned
            else "local_engine_placement",
        }
        if unit_target:
            row.update(
                source="engine_unit_target_placement",
                requested_target_unit=command.target_unit,
                placement_result=response.placements[0].result,
            )
        if index is None:
            row["rejected"] = (
                "invalid_unit_target_placement"
                if unit_target
                else (
                    "no_legal_spatial_candidate"
                    if learned
                    else "no_legal_local_placement"
                )
            )
        elif unit_target:
            resolved.append(command)
            row["issued_target_unit"] = command.target_unit
            row["validated_target_point"] = list(points[0])
        else:
            resolved.append(replace(command, target_point=points[index]))
            row["issued_point"] = list(points[index])
            row["adjustment_tiles"] = math.dist(command.target_point, points[index])
        trace.append(row)
    return resolved, trace
