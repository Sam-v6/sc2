"""Supervised own production outcomes; future chronology is label-only data."""

from collections import Counter


def production_outcomes(events, player, products, conversions, upgrades):
    """Count new tags once, paid conversions once, and first own upgrades.

    Starting units/upgrades, captures, completion, deaths and reversible mode
    changes are not new production. Building outcomes mean construction starts;
    trained unit outcomes mean births; upgrades/conversions mean completions.
    These distinct timings describe demonstrated outcomes, not command intentions.
    """
    owners = {}
    seen = set()
    converted = set()
    researched = set()
    outcomes = []
    previous = -1
    for event in events:
        loop = event['_gameloop']
        if loop < previous:
            raise ValueError('Tracker events must be chronological')
        previous = loop
        kind = event['_event'].rsplit('.', 1)[-1]
        if kind == 'SUpgradeEvent' and event['m_playerId'] == player:
            name = event['m_upgradeTypeName'].decode()
            if event['m_count'] > 0 and name not in researched:
                researched.add(name)
                if loop > 0 and name in upgrades:
                    outcomes.append((loop, 'upgrade:' + name))
        if 'm_unitTagIndex' not in event:
            continue
        tag = (event['m_unitTagIndex'] << 18) | event['m_unitTagRecycle']
        if kind in ('SUnitBornEvent', 'SUnitInitEvent'):
            owners[tag] = event['m_upkeepPlayerId']
            name = event['m_unitTypeName'].decode()
            if name in conversions:
                converted.add((tag, name))
            if tag not in seen:
                seen.add(tag)
                if owners[tag] == player and loop > 0 and name in products:
                    outcomes.append((loop, 'unit:' + name))
        elif kind == 'SUnitOwnerChangeEvent':
            owners[tag] = event['m_upkeepPlayerId']
            seen.add(tag)  # Capturing a unit never makes it newly produced.
        elif kind == 'SUnitTypeChangeEvent' and owners.get(tag) == player:
            name = event['m_unitTypeName'].decode()
            key = (tag, name)
            if name in conversions and key not in converted:
                converted.add(key)
                if loop > 0:
                    outcomes.append((loop, 'unit:' + name))
        elif kind == 'SUnitDiedEvent':
            owners.pop(tag, None)
    return outcomes


def window_counts(outcomes, loop, horizon_loops):
    """Count outcomes in [loop,loop+horizon), matching pre-effect observations."""
    return dict(Counter(name for time, name in outcomes
                        if loop <= time < loop + horizon_loops))
