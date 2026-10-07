"""Scripted spending rules applied after strategy targets (attributed as scripted, not learned)."""

PRODUCTION = (18, 132, 130, 21, 27, 28)  # townhalls, Barracks, Factory, Starport


def depot_limit(state):
    """Depots allowed in construction at once: one, plus one per three ready production buildings."""
    ready = sum(u['alliance'] == 1 and u['unit_type'] in PRODUCTION and u.get('build_progress', 1) == 1
                for u in state['units'])
    return 1 + ready // 3


def spend_float(targets, state):
    """Raise the Barracks target while unspent minerals pile up on two or more bases."""
    player = state['player']
    bases = sum(u['alliance'] == 1 and u['unit_type'] in (18, 132, 130) and u.get('build_progress', 1) == 1
                for u in state['units'])
    if bases < 2 or player['minerals'] < 700 or player['food_used'] >= 190:
        return targets
    return dict(targets, barracks=min(16, targets['barracks'] + min(8, (player['minerals'] - 400) // 300)))
