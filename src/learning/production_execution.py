"""Native catalogue mapping and queue accounting for human outcome goals."""

from collections import Counter
import math


def goal_catalog(data, names):
    abilities = {a['ability_id']: a for a in data['abilities']}
    units = {u['name']: u for u in data['units']}
    upgrades = {u['name']: u for u in data['upgrades']}
    result = {}
    for name in names:
        category, product = name.split(':', 1)
        row = (units if category == 'unit' else upgrades)[product]
        ability = row['ability_id']
        if category == 'upgrade' and abilities[ability].get('available') is False:
            active = [a for a in abilities.values() if a.get('available') is True
                      and a.get('friendly_name') == abilities[ability].get('friendly_name')]
            if len(active) != 1:
                raise ValueError('No unique active research ability for ' + product)
            ability = active[0]['ability_id']
        minerals = row.get('mineral_cost', 0)
        if product in ('OrbitalCommand', 'PlanetaryFortress'):
            minerals -= units['CommandCenter']['mineral_cost']
        result[name] = dict(ability=ability, descriptor=abilities[ability],
                            minerals=minerals, gas=row.get('vespene_cost', 0),
                            unit_type=row.get('unit_id'), upgrade=row.get('upgrade_id'))
    return result


def canonical(ability, catalog):
    return catalog.get(ability, {}).get('remaps_to_ability_id') or ability


def order_goals(unit, goals, catalog, unit_names):
    """Resolve generic addon aliases with the producer's actual native type."""
    parent = unit_names.get(unit['unit_type'], '').removesuffix('Flying')
    result = []
    for order in unit.get('orders', []):
        matches = [name for name, info in goals.items()
                   if canonical(info['ability'], catalog)
                   == canonical(order['ability_id'], catalog)]
        if len(matches) > 1:
            matches = [name for name in matches
                       if goals[name]['descriptor'].get('friendly_name', '').endswith(' ' + parent)]
        if len(matches) == 1:
            result.append((matches[0], order))
    return result


def queued_work(state, goals, catalog, unit_names):
    """Already-started foundations aren't future starts; active orders still echo."""
    queued = Counter()
    active = set()
    own = [u for u in state['units'] if u['alliance'] == 1]
    for unit in own:
        for goal, order in order_goals(unit, goals, catalog, unit_names):
            active.add((unit['tag'], goal))
            descriptor = goals[goal]['descriptor']
            if descriptor.get('friendly_name', '').startswith('Build '):
                point = order.get('target_world_space_pos')
                radius = 1 if point else 6
                target = next((u for u in state['units']
                               if u['tag'] == order.get('target_unit_tag')), None)
                if target is not None:
                    point = dict(zip(('x', 'y'), target['position'][:2]))
                    radius = 1
                point = [point['x'], point['y']] if point else unit['position'][:2]
                started = any(u['unit_type'] == goals[goal]['unit_type']
                              and math.dist(u['position'][:2], point) < radius
                              for u in own)
                if started:
                    continue
            queued[goal] += 1
    return dict(queued), active


def eligible_actors(state, ability, available, catalog, unit_names):
    wanted = canonical(ability, catalog)
    friendly = catalog.get(ability, {}).get('friendly_name', '')
    addon_parent = (friendly.rsplit(' ', 1)[-1]
                    if friendly.startswith(('Build TechLab ', 'Build Reactor '))
                    else None)
    candidates = []
    for unit in state['units']:
        if unit['alliance'] != 1 or unit.get('build_progress', 1) < 1:
            continue
        if addon_parent and unit_names.get(unit['unit_type']) != addon_parent:
            continue
        if wanted not in {canonical(a, catalog) for a in available.get(unit['tag'], ())}:
            continue
        if unit_names.get(unit['unit_type']) == 'SCV':
            if any(catalog.get(o['ability_id'], {}).get('friendly_name', '').startswith('Build ')
                   for o in unit.get('orders', [])):
                continue
        elif unit.get('orders'):
            continue  # One production order per structure; no queue flooding.
        candidates.append(unit)
    return candidates
