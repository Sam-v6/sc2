import tempfile
from pathlib import Path
import unittest

from src.learning.tournament_import import check_bindings, digest


class TournamentImportTests(unittest.TestCase):
    def test_changed_source_binding_cannot_enter_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.bin"
            source.write_bytes(b"original")
            receipt = dict(bindings={str(source): digest(source)})
            check_bindings(receipt)
            source.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "Changed source binding"):
                check_bindings(receipt)


class TournamentPlayerIdentityTests(unittest.TestCase):
    def setUp(self):
        from src.learning.tournament_import import replay_user_id

        self.resolve = replay_user_id
        self.details = {
            "m_playerList": [{"m_workingSetSlotId": 4}, {"m_workingSetSlotId": 15}]
        }
        self.init = {
            "m_syncLobbyState": {
                "m_lobbyState": {
                    "m_slots": [
                        {"m_workingSetSlotId": 0, "m_userId": 0},
                        {"m_workingSetSlotId": 4, "m_userId": 3},
                        {"m_workingSetSlotId": 15, "m_userId": 6},
                    ]
                }
            }
        }

    def test_both_players_resolve_past_observers(self):
        self.assertEqual(self.resolve(self.details, self.init, 1), 3)
        self.assertEqual(self.resolve(self.details, self.init, 2), 6)

    def test_invalid_player_cannot_wrap_to_last_detail(self):
        for player in (0, 3):
            with self.assertRaisesRegex(ValueError, "player"):
                self.resolve(self.details, self.init, player)

    def test_missing_or_duplicate_lobby_identity_is_rejected(self):
        slots = self.init["m_syncLobbyState"]["m_lobbyState"]["m_slots"]
        slots.pop()
        with self.assertRaisesRegex(ValueError, "identity"):
            self.resolve(self.details, self.init, 2)
        slots.append(dict(slots[1]))
        with self.assertRaisesRegex(ValueError, "identity"):
            self.resolve(self.details, self.init, 1)

    def test_unassigned_slot_is_rejected(self):
        self.init["m_syncLobbyState"]["m_lobbyState"]["m_slots"][1]["m_userId"] = None
        with self.assertRaisesRegex(ValueError, "identity"):
            self.resolve(self.details, self.init, 1)


class TournamentOwnershipTests(unittest.TestCase):
    def test_foreign_owner_rejected_but_unknown_owner_not_invented(self):
        from types import SimpleNamespace
        from src.learning.tournament_import import verify_owned_identity

        tracker = SimpleNamespace(player=2, owners={123: 1})
        with self.assertRaisesRegex(ValueError, "foreign"):
            verify_owned_identity(tracker, 123, 10, {})
        verify_owned_identity(tracker, 456, 10, {})
        with self.assertRaisesRegex(ValueError, "foreign"):
            verify_owned_identity(tracker, 456, 10, {(10, 456): {1}})
        verify_owned_identity(tracker, 123, 10, {(10, 123): {2}})
        with self.assertRaisesRegex(ValueError, "foreign"):
            verify_owned_identity(tracker, 123, 10, {(11, 123): {2}})

    def test_causal_own_identity_is_retained(self):
        from types import SimpleNamespace
        from src.learning.tournament_import import verify_owned_identity

        tracker = SimpleNamespace(player=2, owners={123: 2})
        verify_owned_identity(tracker, 123, 10, {})
