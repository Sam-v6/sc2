"""Verified Terran execution helpers; production requests remain learned.

Attack timing/destinations and gas assignment here are declared scripted assists
for the production-imitation experiment, not a learned full-game strategy.
"""
import math

from src.bots.terran_primitives import combat_command, mining_commands, changes_order, destination_reached, scripted_targets
from src.learning.gameplay import Command
from src.learning.production_execution import queued_supply


def supply_assistance_needed(state, data):
    own = [u for u in state['units'] if u['alliance'] == 1]
    if any(u['unit_type'] == 19 and u.get('build_progress', 1) < 1
           or any(o['ability_id'] == 319 for o in u.get('orders', [])) for u in own):
        return False
    player = dict(state['player'])
    player['food_used'] += queued_supply(state, data)
    return bool(scripted_targets(dict(state, player=player))['supply'])


def ground_army(state, types):
    return [u for u in state['units'] if u['alliance'] == 1 and u.get('health', 0) > 0
            and u['unit_type'] not in (45, 268) and 8 not in types[u['unit_type']].get('attributes', [])
            and any(w['type'] in (1, 3) for w in types[u['unit_type']].get('weapons', []))]


def scripted_army_destination(state, types, start, enemy_start, center, expansions, attacking, search_index):
    army = ground_army(state, types)
    power = sum(types[u['unit_type']].get('food_required', 1) for u in army)
    attacking = power >= 40 or (attacking and power >= 20)
    enemies = [u for u in state['units'] if u['alliance'] == 4 and u.get('display_type', 1) == 1]
    bases = [u for u in state['units'] if u['alliance'] == 1 and u['unit_type'] in (18, 132, 130)]
    threats = [e for e in enemies if any(w['type'] in (1, 3) for w in types[e['unit_type']].get('weapons', []))
               and any(math.dist(e['position'][:2], b['position'][:2]) < 22 for b in bases)]
    if threats:
        return tuple(min(threats, key=lambda e: math.dist(e['position'][:2], start))['position'][:2]), attacking, search_index
    if not attacking:
        length = math.dist(start, center)
        return tuple(a+12*(b-a)/length for a, b in zip(start, center)), attacking, search_index
    structures = [e for e in enemies if 8 in types[e['unit_type']].get('attributes', [])]
    centroid = tuple(sum(u['position'][i] for u in army)/len(army) for i in range(2)) if army else start
    if structures:
        return tuple(min(structures, key=lambda e: math.dist(e['position'][:2], centroid))['position'][:2]), attacking, search_index
    search = [enemy_start] + sorted(expansions, key=lambda p: math.dist(p, enemy_start))
    target = search[search_index % len(search)]
    if destination_reached([u['position'][:2] for u in army], target):
        search_index += 1
    return tuple(target), attacking, search_index


def primitive_assistance(state, selected, types, catalog, destination, can_walk, mining, landing_points=(), landing_hold=None):
    own = [u for u in state['units'] if u['alliance'] == 1 and u.get('health', 0) > 0]
    enemies = [u for u in state['units'] if u['alliance'] == 4]
    claimed, commands = set(selected), []
    if landing_hold is None:
        landing_hold = set()
    if not landing_points:
        landing_hold.clear()
    landing_hold.intersection_update(u['tag'] for u in own)
    def append(unit, command):
        if unit['tag'] not in claimed and 5 not in unit.get('buff_ids', []) and command and changes_order(unit, command):
            commands.append(command)
            claimed.add(unit['tag'])
    # Keep the space clear throughout flight, not only at the placement query.
    for unit in own:
        if (unit['tag'] in claimed or unit.get('is_flying')
                or 8 in types[unit['unit_type']].get('attributes', [])):
            continue
        margin = 1.5 + unit.get('radius', .5) + .75
        point = unit['position'][:2]
        if not any(abs(point[0]-x) < margin and abs(point[1]-y) < margin
                   for x, y in landing_points):
            if unit['tag'] in landing_hold:
                claimed.add(unit['tag'])
            continue
        candidates = [(x+dx, y+dy) for x, y in landing_points
                      for dx, dy in ((margin+.5, 0), (-margin-.5, 0),
                                     (0, margin+.5), (0, -margin-.5))]
        free = [p for p in candidates if can_walk(p) and
                all(abs(p[0]-x) >= margin or abs(p[1]-y) >= margin
                    for x, y in landing_points) and
                all(math.dist(p, building['position'][:2]) >
                    building.get('radius', 1.8125) + unit.get('radius', .5) + .25
                    for building in own if not building.get('is_flying')
                    and 8 in types[building['unit_type']].get('attributes', []))]
        if free:
            target = min(free, key=lambda p: math.dist(point, p))
            append(unit, Command(16, (unit['tag'],), target_point=target))
            claimed.add(unit['tag'])
            landing_hold.add(unit['tag'])
    army = ground_army(state, types)
    centroid = tuple(sum(u['position'][i] for u in army)/len(army) for i in range(2)) if army else destination
    if mining:
        workers = [u for u in own if u['unit_type'] == 45 and u['tag'] not in claimed
                   and (not u.get('orders') or all(o['ability_id'] in (295, 3666) for o in u['orders']))]
        for building in own:
            kind = building['unit_type']
            if kind == 19 and building.get('build_progress', 1) == 1:
                append(building, Command(556, (building['tag'],)))
            if kind == 132 and building.get('energy', 0) >= 50:
                patches = [p for p in state['units'] if p['alliance'] == 3 and p.get('mineral_contents', 0) > 0
                           and math.dist(p['position'][:2], building['position'][:2]) < 10]
                if patches:
                    append(building, Command(171, (building['tag'],), target_unit=max(patches, key=lambda p: p['mineral_contents'])['tag']))
            info = types[kind]
            if (8 in info.get('attributes', []) and building.get('build_progress', 1) < 1
                    and not info.get('name', '').endswith(('TechLab', 'Reactor'))):
                assigned = any(o.get('target_unit_tag') == building['tag'] or
                               (catalog.get(o['ability_id'], {}).get('is_building') and o.get('target_world_space_pos')
                                and math.dist((o['target_world_space_pos']['x'], o['target_world_space_pos']['y']), building['position'][:2]) < 1)
                               for u in own if u['unit_type'] == 45 for o in u.get('orders', []))
                free = [w for w in workers if w['tag'] not in claimed]
                if not assigned and free:
                    worker = min(free, key=lambda w: math.dist(w['position'][:2], building['position'][:2]))
                    append(worker, Command(1, (worker['tag'],), target_unit=building['tag']))
        gas = 3*sum(u['unit_type'] == 20 and u.get('build_progress', 1) == 1 for u in own)
        if state['player'].get('vespene', 0) > 400 and state['player'].get('minerals', 0) < 200:
            gas = 0
        commands.extend(mining_commands(state, gas, claimed))
        claimed.update(tag for c in commands for tag in c.units)
    injured = [u for u in own if 3 in types[u['unit_type']].get('attributes', [])
               and u.get('health', 0) < u.get('health_max', 0)]
    for unit in own:
        kind, tag = unit['unit_type'], unit['tag']
        if tag in claimed or kind in (45, 268) or 8 in types[kind].get('attributes', []):
            continue
        if kind == 54:
            target = min(injured, key=lambda u: math.dist(u['position'][:2], unit['position'][:2])) if injured and unit.get('energy', 0) > 0 else None
            append(unit, Command(386, (tag,), target_unit=target['tag']) if target else Command(16, (tag,), target_point=centroid))
            continue
        if not types[kind].get('weapons'):
            continue
        if kind in (48, 51) and 15 in state['upgrades'] and unit['health'] > .65*unit.get('health_max', unit['health']):
            buff, ability = (27, 380) if kind == 48 else (24, 253)
            if buff not in unit.get('buff_ids', []) and any(math.dist(unit['position'][:2], e['position'][:2]) < 8 for e in enemies):
                append(unit, Command(ability, (tag,)))
        target = destination
        if kind == 35:
            air = [e for e in enemies if e.get('is_flying') and e.get('cloak') in (2, 3) and e.get('health', 0) > 0]
            target = min(air, key=lambda e: math.dist(e['position'][:2], unit['position'][:2]))['position'][:2] if air else centroid
        append(unit, combat_command(unit, enemies, types, target, can_walk))
    return commands
