"""Scripted spending rules applied after strategy targets (attributed as scripted, not learned)."""

PRODUCTION = (18, 132, 130, 21, 27, 28)  # townhalls, Barracks, Factory, Starport


def depot_limit(state):
    """Depots allowed in construction at once: one, plus one per three ready production buildings."""
    ready = sum(u['alliance'] == 1 and u['unit_type'] in PRODUCTION and u.get('build_progress', 1) == 1
                for u in state['units'])
    return 1 + ready // 3


def spend_float(targets, state):
    """Raise production targets while unspent resources pile up on two or more bases.

    Minerals add Barracks; gas adds tanks and Factories.
    """
    player = state['player']
    bases = sum(u['alliance'] == 1 and u['unit_type'] in (18, 132, 130) and u.get('build_progress', 1) == 1
                for u in state['units'])
    if bases < 2 or player['food_used'] >= 190:
        return targets
    targets = dict(targets)
    if player['minerals'] >= 700:
        targets['barracks'] = min(16, targets['barracks'] + min(8, (player['minerals'] - 400) // 300))
    if player['vespene'] >= 500:
        targets['tanks'] = min(16, targets['tanks'] + (player['vespene'] - 200) // 150)
        targets['factories'] = min(4, max(targets['factories'], 2) + (player['vespene'] >= 1000))
    return targets


def saturation(targets, state):
    """Cap SCVs at what ready bases can mine (22 each, plus 6 to transfer) and,
    while gas piles up and minerals do not, cap gas mining at 6 SCVs."""
    player = state['player']
    bases = sum(u['alliance'] == 1 and u['unit_type'] in (18, 132, 130) and u.get('build_progress', 1) == 1
                for u in state['units'])
    targets = dict(targets, workers=min(targets['workers'], 22 * bases + 6))
    if player['vespene'] >= 800 and player['minerals'] < 400:
        targets['gas_workers'] = min(targets['gas_workers'], 6)
    return targets


def rush_seen(state):
    """An early Marine rush: 4+ enemy Marines seen before 150 s or 3+ Barracks before 180 s."""
    seconds = state['game_loop'] / 22.4
    enemy = [u['unit_type'] for u in state['units'] if u['alliance'] == 4]
    return (seconds < 150 and enemy.count(48) >= 4) or (seconds < 180 and enemy.count(21) >= 3)


def rush_response(targets, state, rush):
    """After a seen rush, stay on one base with at least three Barracks until 300 s."""
    if not rush or state['game_loop'] / 22.4 >= 300:
        return targets
    return dict(targets, bases=1, barracks=max(targets['barracks'], 3))
