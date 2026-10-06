"""Physical production-space reservations, with no strategic goal generation."""

from dataclasses import replace
from s2clientprotocol import query_pb2 as query, common_pb2 as common
from src.learning.placement import candidates, resolve_placements

PRODUCERS = (21, 27, 28)


def clear_site(point, radius, reserved):
    return all(abs(point[0] - x) >= radius + r or abs(point[1] - y) >= radius + r
               for x, y, r in reserved)


def reservations(state, units, catalog):
    reserved = []
    for unit in state['units']:
        if unit['alliance'] != 1:
            continue
        x, y = unit['position'][:2]
        if unit['unit_type'] in PRODUCERS:
            reserved.extend([(x, y, 2.5), (x + 2.5, y - .5, 1)])
        for order in unit.get('orders', []):
            info = catalog.get(order['ability_id'], {})
            point = order.get('target_world_space_pos')
            if info.get('is_building') and point:
                reserved.append((point['x'], point['y'], info.get('footprint_radius', 1)))
    return reserved


async def resolve_production_placement(client, command, catalog, state, unit_type, reserved):
    info = catalog[command.ability]
    addon = info.get('friendly_name', '').startswith(('Build TechLab', 'Build Reactor'))
    if not info.get('is_building') or command.target_unit is not None:
        return await resolve_placements(client, [command], catalog, state)
    depot = next(a for a, row in catalog.items() if row.get('friendly_name') == 'Build SupplyDepot')
    if addon:
        actor = next(u for u in state['units'] if u['tag'] == command.units[0])
        x, y = actor['position'][:2]
        points = [(x + 2.5, y - .5)]
        checks = [(depot, points[0], 0)]
    else:
        origin = tuple(round(x * 2) / 2 for x in command.target_point)
        width, height = state['map_size']
        search = set(candidates(command.target_point, state))
        search.update((origin[0]+x, origin[1]+y) for x in range(-20, 21, 2)
                      for y in range(-20, 21, 2)
                      if 0 <= origin[0]+x < width and 0 <= origin[1]+y < height)
        search = sorted(search, key=lambda p: (sum((a-b)**2 for a,b in zip(p, origin)), p))
        points = [p for p in search
                  if clear_site(p, info.get('footprint_radius', 1), reserved)
                  and (unit_type not in PRODUCERS or clear_site((p[0]+2.5, p[1]-.5), 1, reserved))]
        checks = [(command.ability, p, command.units[0]) for p in points]
        if unit_type in PRODUCERS:
            checks += [(depot, (p[0]+2.5, p[1]-.5), 0) for p in points]
    if not points:
        return [], [dict(source='production_clearance', rejected='reserved_space')]
    response = (await client._execute(query=query.RequestQuery(
        placements=[query.RequestQueryBuildingPlacement(ability_id=a, placing_unit_tag=tag,
                    target_pos=common.Point2D(x=p[0], y=p[1])) for a, p, tag in checks],
        ignore_resource_requirements=True))).query
    codes = [p.result for p in response.placements]
    if len(codes) != len(checks):
        raise ValueError('Incomplete production placement response')
    index = next((i for i in range(len(points)) if codes[i] == 1 and
                  (addon or unit_type not in PRODUCERS or codes[i+len(points)] == 1)), None)
    trace = dict(source='production_clearance', addon=addon, checked=len(checks),
                 selected=points[index] if index is not None else None,
                 rejected=None if index is not None else 'native_placement')
    if index is None:
        return [], [trace]
    return [command if addon else replace(command, target_point=points[index])], [trace]


def claimed_geysers(state, catalog):
    claimed = set()
    for unit in state['units']:
        if unit['alliance'] != 1:
            continue
        for order in unit.get('orders', []):
            if not catalog.get(order['ability_id'], {}).get('is_building'):
                continue
            if order.get('target_unit_tag'):
                claimed.add(order['target_unit_tag'])
            point = order.get('target_world_space_pos')
            if point:
                claimed.update(u['tag'] for u in state['units'] if u['alliance'] == 3
                               and u.get('vespene_contents', 0) > 0
                               and abs(u['position'][0]-point['x']) < 1
                               and abs(u['position'][1]-point['y']) < 1)
    return claimed
