import unittest

from src.learning import tournament_history
from src.learning.gameplay import Command


class TournamentHistoryTests(unittest.TestCase):
    def test_unmatched_events_occupy_history_slots_and_mask_crossing_delay(self):
        events = [
            dict(_gameloop=loop, m_sequence=i)
            for i, loop in enumerate((10, 12, 15, 15))
        ]
        accepted = [
            dict(loop=10, sequence=0, command=Command(3, (1,))),
            dict(loop=15, sequence=2, command=Command(4, (1,))),
            dict(loop=15, sequence=3, command=Command(5, (1,))),
        ]
        rows = list(tournament_history.history_rows(events, accepted))
        self.assertEqual(len(rows), 3)
        self.assertIsNone(rows[0]["next_action_delay"])
        self.assertEqual(rows[1]["next_action_delay"], 0)
        self.assertIsNone(rows[2]["next_action_delay"])
        self.assertEqual(rows[1]["recent_commands"][0]["ability"], 3)
        self.assertTrue(rows[1]["recent_commands"][0]["verified"])
        self.assertEqual(
            rows[1]["recent_commands"][1], dict(game_loop=12, unknown=True)
        )
        self.assertEqual(
            [c.get("ability") for c in rows[2]["recent_commands"]], [3, None, 4]
        )

    def test_chronology_and_unbound_accepted_events_are_rejected(self):
        with self.assertRaises(ValueError):
            list(
                tournament_history.history_rows(
                    [
                        dict(_gameloop=12, m_sequence=0),
                        dict(_gameloop=10, m_sequence=1),
                    ],
                    [],
                )
            )
        with self.assertRaises(ValueError):
            list(
                tournament_history.history_rows(
                    [], [dict(loop=10, sequence=0, command=Command(3, (1,)))]
                )
            )

    def test_unit_target_history_freezes_the_original_human_snapshot_position(self):
        events = [
            dict(
                _gameloop=10,
                m_sequence=0,
                m_data=dict(
                    TargetUnit=dict(m_snapshotPoint=dict(x=41984, y=14336, z=0))
                ),
            ),
            dict(_gameloop=14, m_sequence=1),
        ]
        accepted = [
            dict(loop=10, sequence=0, command=Command(3, (1,), target_unit=2)),
            dict(loop=14, sequence=1, command=Command(4, (1,))),
        ]
        rows = list(tournament_history.history_rows(events, accepted))
        self.assertEqual(rows[1]["recent_commands"][0]["target_position"], [10.25, 3.5])
