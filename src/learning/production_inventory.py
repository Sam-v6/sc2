"""Living own inventory labels; future tracker state is never an input feature."""

from collections import Counter


def stock_aliases(data):
    units = {u['unit_id']: u for u in data['units']}
    aliases = {}
    for row in units.values():
        canonical = row
        while canonical.get('unit_alias'):
            canonical = units[canonical['unit_alias']]
        aliases[row['name']] = canonical['name']
    if 'HellionTank' in aliases and 'Hellion' in aliases:
        aliases['HellionTank'] = 'Hellion'
    return aliases


def stock_counts(names, upgrades, aliases):
    counts = Counter('unit:'+aliases.get(name, name) for name in names)
    counts['unit:CommandCenter'] += counts['unit:OrbitalCommand'] + counts['unit:PlanetaryFortress']
    for upgrade in upgrades:
        counts['upgrade:'+upgrade] = 1
    return +counts


def observation_stock(state, data):
    units = {u['unit_id']: u['name'] for u in data['units']}
    upgrades = {u['upgrade_id']: u['name'] for u in data['upgrades']}
    known = {u['tag']: u for u in state.get('owned_memory', [])}
    known.update({u['tag']: u for u in state['units'] if u['alliance'] == 1})
    return stock_counts((units[u['unit_type']] for u in known.values()),
                        (upgrades[u] for u in state['upgrades']), stock_aliases(data))


class Inventory:
    def __init__(self, player, aliases):
        self.player, self.aliases = player, aliases
        self.units, self.upgrades = {}, set()

    def apply(self, event):
        kind = event['_event'].rsplit('.', 1)[-1]
        if kind == 'SUpgradeEvent' and event['m_playerId'] == self.player and event['m_count'] > 0:
            self.upgrades.add(event['m_upgradeTypeName'].decode())
        if 'm_unitTagIndex' not in event:
            return
        tag = (event['m_unitTagIndex'], event['m_unitTagRecycle'])
        if kind in ('SUnitBornEvent', 'SUnitInitEvent'):
            self.units[tag] = dict(name=event['m_unitTypeName'].decode(), owner=event['m_upkeepPlayerId'])
        elif kind == 'SUnitTypeChangeEvent':
            self.units[tag]['name'] = event['m_unitTypeName'].decode()
        elif kind == 'SUnitOwnerChangeEvent':
            self.units[tag]['owner'] = event['m_upkeepPlayerId']
        elif kind == 'SUnitDiedEvent':
            del self.units[tag]

    def counts(self):
        return stock_counts((u['name'] for u in self.units.values() if u['owner'] == self.player),
                            self.upgrades, self.aliases)
