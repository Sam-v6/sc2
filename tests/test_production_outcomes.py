import unittest

from src.learning.production_outcomes import production_outcomes, window_counts


def event(kind, loop, **values):
    return dict(_event='NNet.Replay.Tracker.' + kind, _gameloop=loop, **values)


def unit(kind, loop, tag, name, owner=1):
    values = dict(m_unitTagIndex=tag, m_unitTagRecycle=1, m_unitTypeName=name.encode())
    if kind in ('SUnitBornEvent', 'SUnitInitEvent'):
        values['m_upkeepPlayerId'] = owner
    return event(kind, loop, **values)


class ProductionOutcomeTests(unittest.TestCase):
    def test_own_new_production_not_initial_completion_modes_or_capture(self):
        events = [
            unit('SUnitBornEvent', 0, 1, 'SCV'),
            unit('SUnitInitEvent', 2, 2, 'Barracks'),
            unit('SUnitBornEvent', 3, 3, 'Marine', owner=2),
            event('SUnitOwnerChangeEvent', 4, m_unitTagIndex=3,
                  m_unitTagRecycle=1, m_upkeepPlayerId=1),
            event('SUnitDoneEvent', 5, m_unitTagIndex=2, m_unitTagRecycle=1),
            unit('SUnitBornEvent', 6, 4, 'Marine'),
            unit('SUnitBornEvent', 7, 4, 'Marine'),
            unit('SUnitTypeChangeEvent', 8, 2, 'BarracksFlying'),
            unit('SUnitTypeChangeEvent', 9, 2, 'Barracks'),
            unit('SUnitBornEvent', 10, 5, 'CommandCenter'),
            unit('SUnitTypeChangeEvent', 11, 5, 'OrbitalCommand'),
            unit('SUnitTypeChangeEvent', 12, 5, 'OrbitalCommandFlying'),
            unit('SUnitTypeChangeEvent', 13, 5, 'OrbitalCommand'),
            event('SUnitDiedEvent', 14, m_unitTagIndex=4, m_unitTagRecycle=1),
        ]
        self.assertEqual(production_outcomes(events, 1, {'SCV', 'Marine', 'Barracks', 'CommandCenter'}, {'OrbitalCommand'}, {'Stimpack'}),
                         [(2, 'unit:Barracks'), (6, 'unit:Marine'),
                          (10, 'unit:CommandCenter'), (11, 'unit:OrbitalCommand')])

    def test_upgrade_deduplication_and_pre_effect_horizon_boundaries(self):
        events = [event('SUpgradeEvent', loop, m_playerId=owner,
                        m_upgradeTypeName=b'Stimpack', m_count=count)
                  for loop, owner, count in [(0, 1, 1), (1, 2, 1), (2, 1, 0)]]
        events += [event('SUpgradeEvent', loop, m_playerId=1,
                         m_upgradeTypeName=b'Shield', m_count=1) for loop in (3, 4)]
        outcomes = production_outcomes(events, 1, set(), set(), {'Stimpack', 'Shield'})
        self.assertEqual(outcomes, [(3, 'upgrade:Shield')])
        self.assertEqual(window_counts([(2, 'unit:Marine'), (3, 'upgrade:Shield'),
                                       (4, 'unit:Marine')], 2, 2),
                         {'unit:Marine': 1, 'upgrade:Shield': 1})

    def test_out_of_order_tracker_rejected(self):
        with self.assertRaises(ValueError):
            production_outcomes([unit('SUnitBornEvent', 3, 1, 'SCV'),
                                 unit('SUnitBornEvent', 2, 2, 'SCV')],
                                1, {'SCV'}, set(), set())

    def test_initial_conversion_is_not_recounted_after_landing(self):
        events = [unit('SUnitBornEvent', 0, 1, 'OrbitalCommand'),
                  unit('SUnitTypeChangeEvent', 3, 1, 'OrbitalCommandFlying'),
                  unit('SUnitTypeChangeEvent', 4, 1, 'OrbitalCommand')]
        self.assertEqual(production_outcomes(events, 1, set(), {'OrbitalCommand'}, set()), [])
