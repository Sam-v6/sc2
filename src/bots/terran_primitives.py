"""Fog-safe worker and combat execution shared by Terran controllers."""

import math
from collections import Counter

from src.learning.gameplay import Command


def scripted_attack(state, attacking):
    power = sum({48: 1, 32: 3, 33: 3}.get(u['unit_type'], 0)
                for u in state['units'] if u['alliance'] == 1 and u.get('health', 0) > 0)
    if power >= 40:
        return True
    return attacking and power >= 20


def destination_reached(positions, destination):
    return bool(positions) and sum(math.dist(p, destination) < 8 for p in positions) > len(positions)/2


def changes_order(unit, command):
    if command.ability == 23 and command.target_point is not None and math.dist(unit['position'][:2], command.target_point) < 2:
        return False
    for order in unit.get('orders', []):
        if order['ability_id'] != command.ability:
            continue
        if command.target_unit is not None and order.get('target_unit_tag') == command.target_unit:
            return False
        point = order.get('target_world_space_pos')
        if command.target_point is not None and point and math.dist((point['x'], point['y']), command.target_point) < .25:
            return False
        if command.target_unit is None and command.target_point is None:
            return False
    return True


def scripted_targets(state):
    own = [u for u in state['units'] if u['alliance'] == 1]
    counts = Counter(u['unit_type'] for u in own)
    ready = Counter(u['unit_type'] for u in own if u.get('build_progress', 1) == 1)
    bases = max(1, sum(ready[k] for k in (18, 132, 130)))
    workers = counts[45]
    player = state['player']
    gas_workers = min(12, 3*ready[20])
    if player['vespene'] > 400 and player['minerals'] < 200:
        gas_workers = 0
    barracks = 6 if bases >= 2 else 3 if workers >= 20 else 1
    needed_supply = max(6, 2*sum(ready[k] for k in (21, 27, 28)))
    supply = int(player['food_cap'] < 200 and player['food_cap']-player['food_used'] < needed_supply)
    return dict(workers=min(64, 20*bases+3*ready[20]),
                bases=3 if workers >= 42 else 2 if workers >= 18 and ready[21] else 1,
                barracks=barracks, factories=2 if workers >= 40 else int(workers >= 22 and ready[21] > 0),
                starports=int(workers >= 30 and ready[27] > 0),
                engineering_bays=int(workers >= 32),
                refineries=4 if workers >= 40 and ready[27] else 2 if ready[27] else int(counts[21] > 0),
                gas_workers=gas_workers, supply=supply,
                tanks=min(8, max(2, counts[48]//6)))


def distance(a, b):
    return math.dist(a['position'][:2], b['position'][:2])


def mining_commands(state, gas_workers, protected=()):
    own = [u for u in state['units'] if u['alliance'] == 1]
    enemies = [u for u in state['units'] if u['alliance'] == 4 and u.get('display_type', 1) == 1]
    bases = [u for u in own if u['unit_type'] in (18, 132, 130) and u.get('build_progress', 1) == 1
             and not u.get('is_flying') and not any(distance(u, e) < 10 for e in enemies)]
    if not bases:
        return []
    patches = [u for u in state['units'] if u['alliance'] == 3 and u.get('mineral_contents', 0) > 0
               and any(distance(u, b) < 10 for b in bases)]
    if not patches:
        patches = [u for u in state['units']
                   if u['alliance'] == 3 and u.get('mineral_contents', 0) > 0
                   and u.get('observed', True) and u.get('display_type', 1) == 1
                   and not any(distance(u, e) < 10 for e in enemies)]
    gas = [u for u in own if u['unit_type'] == 20 and u.get('build_progress', 1) == 1
           and u.get('vespene_contents', 0) > 0 and any(distance(u, b) < 10 for b in bases)]
    workers = [u for u in own if u['unit_type'] == 45 and u['tag'] not in protected
               and (not u.get('orders') or all(o['ability_id'] in (295, 3666) for o in u['orders']))]
    current = {w['tag']: w.get('orders', [{}])[-1].get('target_unit_tag') if w.get('orders') else None
               for w in workers}
    used, commands = set(), []
    def assign(worker, target):
        used.add(worker['tag'])
        if current[worker['tag']] != target['tag']:
            commands.append(Command(295, (worker['tag'],), target_unit=target['tag']))
    for refinery in sorted(gas, key=lambda u: u['tag']):
        quota = min(3, gas_workers)
        gas_workers -= quota
        existing = [w for w in workers if current[w['tag']] == refinery['tag']]
        for worker in existing[:quota]:
            assign(worker, refinery)
        shortage = max(0, quota - max(len(existing), refinery.get('assigned_harvesters', 0)))
        available = sorted((w for w in workers if w['tag'] not in used), key=lambda w: distance(w, refinery))
        for worker in available[:shortage]:
            assign(worker, refinery)
    loads = Counter()
    targets = {p['tag']: p for p in patches}
    for worker in workers:
        tag = current[worker['tag']]
        if worker['tag'] not in used and tag in targets and loads[tag] < 2:
            assign(worker, targets[tag])
            loads[tag] += 1
    for worker in workers:
        if worker['tag'] in used or not patches:
            continue
        target = min(patches, key=lambda p: (loads[p['tag']] >= 2, loads[p['tag']], distance(worker, p)))
        assign(worker, target)
        loads[target['tag']] += 1
    return commands


def worker_defense_commands(state, types, protected=()):
    """Pull SCVs against ground attackers at a base when the nearby army is weaker.

    Pulls twice the supply deficit plus one from idle, mining or already-fighting SCVs;
    builders and injured SCVs stay out.
    Released workers become idle when their target dies and resume mining.
    """
    own = [u for u in state['units'] if u['alliance'] == 1]
    bases = [u for u in own if u['unit_type'] in (18, 132, 130) and u.get('build_progress', 1) == 1]
    threats = [e for e in state['units'] if e['alliance'] == 4 and e.get('display_type', 1) == 1
               and not e.get('is_flying') and e.get('health', 1) > 0
               and 8 not in types.get(e['unit_type'], {}).get('attributes', [])
               and any(w['type'] in (1, 3) for w in types.get(e['unit_type'], {}).get('weapons', []))
               and any(distance(e, b) < 12 for b in bases)]
    if not threats:
        return []
    enemy = sum(types[e['unit_type']].get('food_required', 1) for e in threats)
    army = sum(types.get(u['unit_type'], {}).get('food_required', 0) for u in own
               if u['unit_type'] != 45 and any(distance(u, b) < 15 for b in bases))
    # A ready Bunker fights like about four Marines plus its cargo.
    army += sum(4 + u.get('cargo_space_taken', 0) for u in own
                if u['unit_type'] == 24 and u.get('build_progress', 1) == 1 and any(distance(u, b) < 15 for b in bases))
    if army >= enemy:
        return []
    workers = sorted((u for u in own if u['unit_type'] == 45 and u['tag'] not in protected
                      and u.get('health', 45) >= 20
                      and all(o['ability_id'] in (23, 295, 296, 3666, 3667) for o in u.get('orders', []))),
                     key=lambda u: min(distance(u, e) for e in threats))
    commands = []
    for worker in workers[:math.ceil(2*(enemy - army)) + 1]:
        target = min(threats, key=lambda e: distance(worker, e))
        command = Command(23, (worker['tag'],), target_unit=target['tag'])
        if changes_order(worker, command):
            commands.append(command)
    return commands


def combat_command(unit, enemies, types, destination, can_walk):
    if unit.get('health', 0) <= 0 or 5 in unit.get('buff_ids', []):
        # Graviton Beam disables commands until the unit is released.
        return None
    if unit['unit_type'] in (32, 33) and any(o['ability_id'] in (388, 390) for o in unit.get('orders', [])):
        return None
    visible = [e for e in enemies if e.get('display_type', 1) == 1 and e['alliance'] == 4
               and types[e['unit_type']].get('name') not in ('KD8Charge', 'AdeptPhaseShift') and e.get('health', 0) > 0]
    if unit['unit_type'] in (689, 734):
        if any(o['ability_id'] in (2554, 2556, 2558, 2560) for o in unit.get('orders', [])):
            return None
        targets = [e for e in visible if e.get('observed', True) and not e.get('is_flying')
                   and 8 not in types[e['unit_type']].get('attributes', [])
                   and e.get('cloak', 0) in (2, 3) and distance(unit, e) < 10]
        if unit['unit_type'] == 734:
            return None if targets else Command(2560, (unit['tag'],))
        if targets:
            target = min(targets, key=lambda e: distance(unit, e))
            length = distance(unit, target)
            point = tuple(a + (b-a)*min(1, 5/length) for a, b in
                          zip(unit['position'][:2], target['position'][:2])) if length else tuple(target['position'][:2])
            return Command(2558, (unit['tag'],), target_point=point)
    ground = [e for e in visible if not e.get('is_flying')]
    nearest = min((distance(unit, e) for e in ground), default=100)
    if unit['unit_type'] == 33 and 5 < nearest < 13:
        return Command(388, (unit['tag'],))
    if unit['unit_type'] == 32 and nearest > 17:
        return Command(390, (unit['tag'],))
    weapons = types[unit['unit_type']].get('weapons', [])
    compatible = []
    for enemy in visible:
        if enemy.get('cloak', 0) not in (2, 3):
            continue
        ranges = [w['range'] for w in weapons if w['type'] in (3, 2 if enemy.get('is_flying') else 1)]
        if ranges:
            compatible.append((enemy, max(ranges)))
    in_range = [(e, r) for e, r in compatible
                if distance(unit, e) <= r + unit.get('radius', .5) + e.get('radius', .5)
                and (unit['unit_type'] != 32 or 3 <= distance(unit, e) <= r)]
    if in_range:
        enemy, attack_range = min(in_range, key=lambda pair: (distance(unit, pair[0]), pair[0].get('health', 1)))
        threat_range = max((w['range'] for w in types[enemy['unit_type']].get('weapons', [])
                            if w['type'] in (3, 2 if unit.get('is_flying') else 1)), default=0)
        if unit['unit_type'] != 32 and unit.get('weapon_cooldown', 0) > 0 and attack_range > threat_range + 1:
            dx = unit['position'][0] - enemy['position'][0]
            dy = unit['position'][1] - enemy['position'][1]
            length = math.hypot(dx, dy)
            if length:
                retreat = (unit['position'][0] + 2*dx/length, unit['position'][1] + 2*dy/length)
                if unit.get('is_flying') or can_walk(retreat):
                    return Command(16, (unit['tag'],), target_point=retreat)
        return Command(23, (unit['tag'],), target_unit=enemy['tag'])
    if unit['unit_type'] == 32:
        return None
    return Command(23, (unit['tag'],), target_point=tuple(destination))
