import unittest
from src.learning.production_intents import ProductionIntents, remaining_budget


class IntentTests(unittest.TestCase):
    def test_request_survives_zero_forecast_and_is_unique(self):
        ledger = ProductionIntents()
        ledger.plan({'depot': 3}, {}, 0)
        ledger.plan({'depot': 3}, {}, 48)
        ledger.plan({}, {}, 96)
        self.assertEqual(ledger.requests(), ['depot'])
        self.assertEqual(len(ledger.intents), 1)
        self.assertEqual(ledger.remaining('depot'), 1)

    def test_rejection_loss_and_timeout_reuse_id_and_deadline(self):
        ledger = ProductionIntents()
        ledger.plan({'worker': 1}, {}, 0)
        first = ledger.reserve('worker', 10, 0)
        ledger.acknowledge(first, False)
        self.assertEqual(ledger.reserve('worker', 11, 48), first)
        ledger.acknowledge(first, True)
        ledger.reconcile(set(), set(), 96)
        self.assertEqual(ledger.reserve('worker', 12, 96), first)
        ledger.acknowledge(first, True)
        ledger.reconcile(set(), {12}, 224)
        self.assertEqual(ledger.intents[first]['expires'], 1008)
        self.assertFalse(ledger.pending)

    def test_observed_order_consumes_and_queue_prevents_duplicate_worker(self):
        ledger = ProductionIntents()
        ledger.plan({'worker': 1}, {}, 0)
        ticket = ledger.reserve('worker', 10, 0)
        ledger.acknowledge(ticket, True)
        ledger.reconcile({(10, 'worker')}, {10}, 48)
        ledger.plan({'worker': 1}, {'worker': 1}, 48)
        self.assertFalse(ledger.requests())
        ledger.plan({'worker': 1}, {}, 336)
        self.assertEqual(ledger.requests(), ['worker'])
        self.assertNotEqual(ledger.reserve('worker', 10, 336), ticket)

    def test_expiry_requires_a_later_zero_to_positive_transition(self):
        ledger = ProductionIntents()
        ledger.plan({'tank': 1}, {}, 0)
        ledger.reconcile(set(), set(), 1008)
        ledger.plan({'tank': 1}, {}, 1008)
        ledger.plan({'tank': 1}, {}, 1056)
        self.assertFalse(ledger.requests())
        ledger.plan({}, {}, 1104)
        ledger.plan({'tank': 1}, {}, 1152)
        self.assertEqual(ledger.requests(), ['tank'])
        self.assertEqual(next(iter(ledger.intents.values()))['expires'], 2160)
        self.assertEqual(ledger.remaining('barracks'), 0)

    def test_one_actor_is_never_assigned_twice(self):
        ledger = ProductionIntents()
        ledger.plan({'a': 1, 'b': 1}, {}, 0)
        ledger.reserve('a', 10, 0)
        with self.assertRaises(ValueError):
            ledger.reserve('b', 10, 0)

    def test_reservation_preserves_priority_without_hardcoded_families(self):
        self.assertEqual(remaining_budget((85, 0), (100, 0)), (0, 0))
        self.assertEqual(remaining_budget((600, 200), (400, 300)), (200, 0))
