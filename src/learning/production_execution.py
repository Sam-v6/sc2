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


def command_point(command, state):
    """Resolve point and observed unit targets consistently for builder travel."""
    if command.target_point is not None:
        return command.target_point
    target = next((u for u in state['units'] if u['tag'] == command.target_unit), None)
    return tuple(target['position'][:2]) if target else None


def builder_approach_points(command, state):
    """A unit target blocks its centre; query outside its observed footprint."""
    if command.target_point is not None:
        return [command.target_point]
    target = next((u for u in state['units'] if u['tag'] == command.target_unit), None)
    if target is None:
        return []
    x, y = target['position'][:2]
    radius = target.get('radius', 1.5) + .5
    return [(x + dx * radius, y + dy * radius)
            for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]


def waiting_for_supply(error, state, catalog):
    if (error['result'] != 13 or not catalog.get(error['ability_id'], {}).get('friendly_name', '').startswith('Train ')):
        return False
    return any(u['tag'] == error['unit_tag'] and u['alliance'] == 1
               and any(o['ability_id'] == error['ability_id'] and o.get('progress', 0) == 0
                       for o in u.get('orders', [])) for u in state['units'])


def worker_constructing(unit, state, catalog):
    foundations = {u['tag'] for u in state['units']
                   if u['alliance'] == 1 and u.get('build_progress', 1) < 1}
    return any(catalog.get(o['ability_id'], {}).get('friendly_name', '').startswith('Build ')
               or o.get('target_unit_tag') in foundations for o in unit.get('orders', []))


def queried_command_ability(ability, available, catalog):
    """Use exact availability; resolve generic Cancel Last only when unique."""
    if ability in available:
        return ability
    if ability != 3671:
        return None
    matches = [a for a in available if canonical(a, catalog) == ability]
    return matches[0] if len(matches) == 1 else None


def queued_supply(state, data):
    """Reserve supply for observed waiting train orders, excluding active progress."""
    catalog = {a['ability_id']: a for a in data['abilities']}
    food = {}
    for unit in data['units']:
        ability = canonical(unit.get('ability_id'), catalog)
        food[ability] = max(food.get(ability, 0), unit.get('food_required', 0))
    return sum(food.get(canonical(order['ability_id'], catalog), 0)
               for unit in state['units'] if unit['alliance'] == 1
               for order in unit.get('orders', [])
               if order.get('progress', 0) == 0
               and catalog.get(order['ability_id'], {}).get('friendly_name', '').startswith('Train '))


def command_cost(ability, data):
    """Price actual production; flying transitions do not repurchase the building."""
    catalog = {a['ability_id']: a for a in data['abilities']}
    name = catalog[ability].get('friendly_name', '')
    if name.startswith('Research '):
        rows = [u for u in data['upgrades'] if u.get('ability_id') == ability
                or catalog.get(u.get('ability_id'), {}).get('friendly_name') == name]
    elif name.startswith(('Build ', 'Train ')) or name in ('Morph OrbitalCommand', 'Morph PlanetaryFortress'):
        rows = [u for u in data['units'] if u.get('ability_id') == ability]
        if not rows:
            rows = [u for u in data['units'] if u.get('ability_id') is not None
                    and canonical(u['ability_id'], catalog) == canonical(ability, catalog)]
    else:
        return 0, 0
    prices = {(u.get('mineral_cost', 0), u.get('vespene_cost', 0)) for u in rows}
    if len(prices) != 1:
        raise ValueError('No unique production price for ' + name)
    minerals, gas = prices.pop()
    if name in ('Morph OrbitalCommand', 'Morph PlanetaryFortress'):
        minerals -= next(u['mineral_cost'] for u in data['units'] if u['name'] == 'CommandCenter')
    return minerals, gas


def resource_affordable_choices(probabilities, prices, minerals, gas):
    """Filter immediate single-product costs; unknown prices are not guessed."""
    return {ability: probability for ability, probability in probabilities.items()
            if ability not in prices
            or (prices[ability][0] <= minerals and prices[ability][1] <= gas)}


def affordable_production_intent(probabilities, prices, minerals, gas):
    """Wait for the preferred product instead of purchasing a cheaper fallback."""
    if not probabilities:
        return None
    ability = max(probabilities, key=probabilities.get)
    price = prices.get(ability)
    if price is None or price[0] > minerals or price[1] > gas:
        return None
    return ability


def unreserved_resources(player, commitments, prices):
    """Keep accepted but unacknowledged production costs reserved per request."""
    costs = [prices[ability] for ability in commitments]
    return (max(0, player['minerals'] - sum(cost[0] for cost in costs)),
            max(0, player['vespene'] - sum(cost[1] for cost in costs)))


def order_goals(unit, goals, catalog, unit_names):
    """Keep specific order identities; resolve generic addons by producer type."""
    parent = unit_names.get(unit['unit_type'], '').removesuffix('Flying')
    result = []
    for order in unit.get('orders', []):
        matches = [name for name, info in goals.items()
                   if canonical(info['ability'], catalog)
                   == canonical(order['ability_id'], catalog)]
        if len(matches) > 1:
            exact = [name for name in matches
                     if goals[name]['ability'] == order['ability_id']]
            matches = exact or [name for name in matches
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


def eligible_actors(state, ability, available, catalog, unit_names, *, max_train_orders=1):
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
        actor_abilities = available.get(unit['tag'], ())
        if wanted not in {canonical(a, catalog) for a in actor_abilities}:
            continue
        # Specific research tiers share a generic alias; tier one does not grant tier two.
        if (friendly.startswith('Research ') and ability not in actor_abilities
                and wanted not in actor_abilities):
            continue
        if unit_names.get(unit['unit_type']) == 'SCV':
            if worker_constructing(unit, state, catalog):
                continue
        elif unit.get('orders'):
            orders = unit['orders']
            if (not friendly.startswith('Train ') or len(orders) >= max_train_orders
                    or any(not catalog.get(o['ability_id'], {}).get('friendly_name', '')
                           .startswith('Train ') for o in orders)):
                continue
        candidates.append(unit)
    return candidates
