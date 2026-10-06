import unittest
from src.learning.production_ledger import ProductionLedger


class ProductionLedgerTests(unittest.TestCase):
    def test_no_goal_produces_no_work(self):
        ledger = ProductionLedger()
        ledger.plan({}, {})
        self.assertEqual(ledger.remaining('unit:SCV'), 0)
        with self.assertRaises(ValueError):
            ledger.reserve('unit:SCV', 1, 0)

    def test_pending_acknowledgement_and_observed_queue_do_not_double_count(self):
        ledger = ProductionLedger()
        ledger.plan({'unit:Marine': 2}, {})
        ticket = ledger.reserve('unit:Marine', 1, 0)
        ledger.acknowledge(ticket, True)
        ledger.plan({'unit:Marine': 2}, {})
        self.assertEqual(ledger.remaining('unit:Marine'), 1)
        ledger.reconcile({(1, 'unit:Marine')}, {1}, 1)
        ledger.plan({'unit:Marine': 2}, {'unit:Marine': 1})
        self.assertEqual(ledger.remaining('unit:Marine'), 1)
        self.assertFalse(ledger.pending)

    def test_rejection_and_actor_loss_release_pending_work(self):
        ledger = ProductionLedger()
        ledger.plan({'unit:Barracks': 1}, {})
        ticket = ledger.reserve('unit:Barracks', 1, 0)
        ledger.acknowledge(ticket, False)
        self.assertEqual(ledger.remaining('unit:Barracks'), 1)
        ticket = ledger.reserve('unit:Barracks', 1, 0)
        ledger.acknowledge(ticket, True)
        changes = ledger.reconcile(set(), set(), 1)
        self.assertEqual(changes[ticket], 'actor_lost')
        self.assertEqual(ledger.remaining('unit:Barracks'), 1)

    def test_one_actor_cannot_receive_conflicting_batch_work(self):
        ledger = ProductionLedger()
        ledger.plan({'unit:SCV': 1, 'unit:OrbitalCommand': 1}, {})
        ledger.reserve('unit:SCV', 1, 0)
        with self.assertRaises(ValueError):
            ledger.reserve('unit:OrbitalCommand', 1, 0)

    def test_missing_order_expires_and_cancelled_queue_is_not_fulfilled(self):
        ledger = ProductionLedger()
        ledger.plan({'unit:SCV': 1}, {})
        ticket = ledger.reserve('unit:SCV', 1, 0)
        ledger.acknowledge(ticket, True)
        self.assertFalse(ledger.reconcile(set(), {1}, 127))
        self.assertEqual(ledger.reconcile(set(), {1}, 128)[ticket], 'unobserved_timeout')
        ledger.plan({'unit:SCV': 1}, {})
        self.assertEqual(ledger.remaining('unit:SCV'), 1)

    def test_blocked_prerequisites_do_not_create_other_goals(self):
        ledger = ProductionLedger()
        ledger.plan({'unit:Marine': 3}, {})
        self.assertEqual(ledger.remaining('unit:Barracks'), 0)
        self.assertEqual(ledger.remaining('unit:SupplyDepot'), 0)
        self.assertEqual(ledger.remaining('unit:Marine'), 3)

    def test_observed_queue_cancellation_reopens_goal_on_next_plan(self):
        ledger = ProductionLedger()
        ledger.plan({'unit:SCV': 1}, {'unit:SCV': 1})
        self.assertEqual(ledger.remaining('unit:SCV'), 0)
        ledger.plan({'unit:SCV': 1}, {})
        self.assertEqual(ledger.remaining('unit:SCV'), 1)
