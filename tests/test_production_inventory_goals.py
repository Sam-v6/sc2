import unittest
from types import SimpleNamespace as NS
import numpy as np
from src.learning.production_inventory_goals import (
    HumanGoalLibrary,
    InventoryIntents,
    opponent_selected_race,
    inventory_queued,
)


class InventoryGoalsTests(unittest.TestCase):
    def library(self):
        return HumanGoalLibrary(
            ["unit:SCV", "unit:Barracks"],
            np.array([[0, 12, 1], [100, 20, 1], [100, 20, 1]]),
            np.array([[15, 1], [24, 3], [24, 7]]),
            np.ones(3),
            [
                dict(game="a", row=0, loop=0),
                dict(game="b", row=1, loop=2240),
                dict(game="c", row=2, loop=2240),
            ],
            {"a": "Terr", "b": "Zerg", "c": "Prot"},
            {"Terr": 1, "Zerg": 1, "Prot": 1, "unknown": 1},
            "hash",
        )

    def test_public_requested_race_not_assigned_random_race(self):
        players = [
            NS(player_id=1, race_requested=1, race_actual=1),
            NS(player_id=2, race_requested=4, race_actual=2),
        ]
        self.assertEqual(opponent_selected_race(NS(player_info=players), 1), "unknown")
        players[1].race_requested = 3
        self.assertEqual(opponent_selected_race(NS(player_info=players), 1), "Prot")

    def test_one_actual_vector_race_condition_and_hold(self):
        lib = self.library()
        targets, source = lib.select(
            2240, {"unit:SCV": 20, "unit:CommandCenter": 1}, "Zerg"
        )
        self.assertEqual(targets, {"unit:SCV": 24, "unit:Barracks": 3})
        self.assertEqual(source["game"], "b")
        later, held = lib.select(
            2248, {"unit:SCV": 100, "unit:CommandCenter": 5}, "Zerg"
        )
        self.assertEqual(later, targets)
        self.assertEqual(held, source)
        self.assertEqual(source["future_loop"], 3248)
        targets, source = lib.select(
            3248, {"unit:SCV": 100, "unit:CommandCenter": 5}, "Zerg"
        )
        self.assertEqual(targets, {})
        self.assertFalse(source["supported"])

    def test_unknown_uses_all_cohorts_and_deterministic_first_tie(self):
        targets, source = self.library().select(
            2240, {"unit:SCV": 20, "unit:CommandCenter": 1}, "unknown"
        )
        self.assertEqual(targets["unit:Barracks"], 3)
        self.assertEqual(source["game"], "b")

    def test_satisfied_or_removed_unissued_intent_retires(self):
        ledger = InventoryIntents()
        ledger.plan({"barracks": 2, "marine": 1}, {}, 0)
        ledger.plan({"barracks": 1}, {"barracks": 1}, 48)
        self.assertFalse(ledger.requests())
        self.assertEqual([e["event"] for e in ledger.events].count("retired"), 2)

    def test_accepted_work_survives_new_target_and_stock_can_rearm_immediately(self):
        ledger = InventoryIntents()
        ledger.plan({"marine": 3}, {}, 0)
        ticket = ledger.reserve("marine", 10, 0)
        ledger.acknowledge(ticket, True)
        ledger.plan({}, {}, 8)
        self.assertIn(ticket, ledger.pending)
        ledger.reconcile({(10, "marine")}, {10}, 48)
        ledger.plan({"marine": 2}, {"marine": 1}, 48)
        self.assertEqual(ledger.requests(), ["marine"])
        self.assertFalse(ledger.recent)
        ledger.plan({"marine": 1}, {"marine": 1}, 96)
        self.assertFalse(ledger.requests())

    def test_remembered_foundation_not_counted_as_future_build_or_stale_order(self):
        goals = {
            "unit:Barracks": dict(
                ability=321,
                unit_type=21,
                descriptor=dict(friendly_name="Build Barracks"),
            )
        }
        state = dict(
            units=[
                dict(
                    tag=1,
                    alliance=1,
                    unit_type=45,
                    position=[0, 0],
                    orders=[
                        dict(ability_id=321, target_world_space_pos=dict(x=8, y=8))
                    ],
                )
            ],
            owned_memory=[
                dict(
                    tag=2,
                    alliance=1,
                    unit_type=21,
                    position=[8, 8],
                    build_progress=0.5,
                    orders=[dict(ability_id=321)],
                )
            ],
        )
        queued, active = inventory_queued(state, goals, {}, {})
        self.assertEqual(queued, {})
        self.assertEqual(active, {(1, "unit:Barracks")})
