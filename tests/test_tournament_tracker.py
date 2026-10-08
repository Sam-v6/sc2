import unittest
from src.learning.tournament_tracker import CausalTracker


def event(kind, loop, **kwargs):
    return dict(_event="NNet.Replay.Tracker." + kind, _gameloop=loop, **kwargs)


class TournamentTrackerTests(unittest.TestCase):
    def test_only_own_deaths_upgrades_and_neutral_types_are_exposed_causally(self):
        tag = dict(m_unitTagIndex=7, m_unitTagRecycle=1)
        enemy = dict(m_unitTagIndex=8, m_unitTagRecycle=1)
        neutral = dict(m_unitTagIndex=9, m_unitTagRecycle=1)
        events = [
            event(
                "SUnitBornEvent", 0, **tag, m_upkeepPlayerId=1, m_unitTypeName=b"Marine"
            ),
            event(
                "SUnitBornEvent",
                0,
                **enemy,
                m_upkeepPlayerId=2,
                m_unitTypeName=b"Marine",
            ),
            event(
                "SUnitBornEvent",
                0,
                **neutral,
                m_upkeepPlayerId=0,
                m_unitTypeName=b"MineralField",
            ),
            event(
                "SUpgradeEvent",
                2,
                m_playerId=2,
                m_upgradeTypeName=b"Stimpack",
                m_count=1,
            ),
            event(
                "SUpgradeEvent",
                3,
                m_playerId=1,
                m_upgradeTypeName=b"Stimpack",
                m_count=1,
            ),
            event("SUnitDiedEvent", 4, **enemy),
            event("SUnitDiedEvent", 5, **tag),
        ]
        tracker = CausalTracker(
            events,
            1,
            dict(
                units=[
                    dict(name="Marine", unit_id=48),
                    dict(name="MineralField", unit_id=341),
                ],
                upgrades=[dict(name="Stimpack", upgrade_id=15)],
            ),
        )
        self.assertEqual(tracker.advance(1), set())
        self.assertEqual(tracker.own_types, {(7 << 18) | 1: 48})
        self.assertEqual(tracker.neutral_types, {(9 << 18) | 1: 341})
        tracker.advance(2)
        self.assertEqual(tracker.upgrades, set())
        tracker.advance(3)
        self.assertEqual(tracker.upgrades, set())
        self.assertEqual(tracker.advance(4), set())
        self.assertEqual(tracker.upgrades, {15})
        self.assertEqual(tracker.advance(5), set())
        self.assertEqual(tracker.advance(6), {(7 << 18) | 1})
        self.assertEqual(tracker.own_types, {})
        with self.assertRaises(ValueError):
            tracker.advance(4)

    def test_ownership_changes_remove_own_death_access(self):
        tag = dict(m_unitTagIndex=7, m_unitTagRecycle=1)
        tracker = CausalTracker(
            [
                event(
                    "SUnitBornEvent",
                    0,
                    **tag,
                    m_upkeepPlayerId=1,
                    m_unitTypeName=b"Marine",
                ),
                event("SUnitOwnerChangeEvent", 2, **tag, m_upkeepPlayerId=2),
                event("SUnitDiedEvent", 3, **tag),
            ],
            1,
            dict(units=[dict(name="Marine", unit_id=48)], upgrades=[]),
        )
        tracker.advance(0)
        self.assertEqual(tracker.advance(3), set())
        self.assertEqual(tracker.own_types, {})
