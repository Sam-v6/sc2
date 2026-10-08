import unittest
from src.learning.production_inventory import Inventory, stock_counts, stock_aliases


def event(kind, loop, **fields):
    return dict(_event='NNet.Replay.Tracker.'+kind, _gameloop=loop, **fields)


def unit_event(kind, loop, name, player=1, tag=1):
    return event(kind, loop, m_unitTagIndex=tag, m_unitTagRecycle=0,
                 m_unitTypeName=name.encode(), m_upkeepPlayerId=player)


class InventoryTests(unittest.TestCase):
    def test_alias_modes_and_hierarchical_town_halls(self):
        data = {'units': [dict(unit_id=18, name='CommandCenter'),
                          dict(unit_id=19, name='SupplyDepot'),
                          dict(unit_id=47, name='SupplyDepotLowered', unit_alias=19),
                          dict(unit_id=132, name='OrbitalCommand'),
                          dict(unit_id=134, name='OrbitalCommandFlying', unit_alias=132),
                          dict(unit_id=53, name='Hellion'), dict(unit_id=484, name='HellionTank')]}
        aliases = stock_aliases(data)
        self.assertEqual(aliases['SupplyDepotLowered'], 'SupplyDepot')
        self.assertEqual(aliases['OrbitalCommandFlying'], 'OrbitalCommand')
        self.assertEqual(aliases['HellionTank'], 'Hellion')
        counts = stock_counts(['OrbitalCommandFlying', 'SupplyDepotLowered', 'HellionTank'], [], aliases)
        self.assertEqual(counts['unit:CommandCenter'], 1)
        self.assertEqual(counts['unit:OrbitalCommand'], 1)
        self.assertEqual(counts['unit:SupplyDepot'], 1)

    def test_foundation_birth_duplicate_morph_death_and_capture(self):
        aliases = {'SupplyDepotLowered': 'SupplyDepot'}
        tracker = Inventory(1, aliases)
        tracker.apply(unit_event('SUnitInitEvent', 0, 'SupplyDepot'))
        tracker.apply(unit_event('SUnitBornEvent', 10, 'SupplyDepot'))
        self.assertEqual(tracker.counts()['unit:SupplyDepot'], 1)
        tracker.apply(event('SUnitTypeChangeEvent', 20, m_unitTagIndex=1, m_unitTagRecycle=0, m_unitTypeName=b'SupplyDepotLowered'))
        self.assertEqual(tracker.counts()['unit:SupplyDepot'], 1)
        tracker.apply(event('SUnitOwnerChangeEvent', 30, m_unitTagIndex=1, m_unitTagRecycle=0, m_upkeepPlayerId=2))
        self.assertEqual(tracker.counts().get('unit:SupplyDepot', 0), 0)
        tracker.apply(event('SUnitOwnerChangeEvent', 40, m_unitTagIndex=1, m_unitTagRecycle=0, m_upkeepPlayerId=1))
        self.assertEqual(tracker.counts()['unit:SupplyDepot'], 1)
        tracker.apply(event('SUnitDiedEvent', 50, m_unitTagIndex=1, m_unitTagRecycle=0))
        self.assertEqual(tracker.counts().get('unit:SupplyDepot', 0), 0)

    def test_upgrade_owner_and_binary_quantity(self):
        tracker = Inventory(1, {})
        tracker.apply(event('SUpgradeEvent', 0, m_playerId=2, m_count=1, m_upgradeTypeName=b'Stimpack'))
        self.assertFalse(tracker.counts())
        tracker.apply(event('SUpgradeEvent', 10, m_playerId=1, m_count=1, m_upgradeTypeName=b'Stimpack'))
        tracker.apply(event('SUpgradeEvent', 20, m_playerId=1, m_count=2, m_upgradeTypeName=b'Stimpack'))
        self.assertEqual(tracker.counts()['upgrade:Stimpack'], 1)

    def test_observation_inventory_includes_owned_memory_and_deduplicates_tags(self):
        from src.learning.production_inventory import observation_stock
        data = dict(units=[dict(unit_id=45, name='SCV'), dict(unit_id=18, name='CommandCenter')], upgrades=[])
        state = dict(units=[dict(tag=1, unit_type=45, alliance=1)],
                     owned_memory=[dict(tag=1, unit_type=45, alliance=1), dict(tag=2, unit_type=45, alliance=1)], upgrades=[])
        self.assertEqual(observation_stock(state, data)['unit:SCV'], 2)
