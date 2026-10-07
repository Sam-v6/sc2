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
        self.assertFalse(ledger.recent)

    def test_observed_order_consumes_and_queue_prevents_duplicate_worker(self):
        ledger = ProductionIntents()
        ledger.plan({'worker': 1}, {}, 0)
        ticket = ledger.reserve('worker', 10, 0)
        ledger.acknowledge(ticket, True)
        ledger.reconcile({(10, 'worker')}, {10}, 48)
        ledger.plan({'worker': 1}, {'worker': 1}, 48)
        self.assertFalse(ledger.requests())
        ledger.plan({'worker': 1}, {}, 336)
        self.assertFalse(ledger.requests())
        ledger.plan({'worker': 1}, {}, 1056)
        self.assertEqual(ledger.requests(), ['worker'])
        self.assertNotEqual(ledger.reserve('worker', 10, 1056), ticket)

    def test_expiry_requires_later_observation_but_accepts_fresh_positive_forecast(self):
        ledger = ProductionIntents()
        ledger.plan({'tank': 1}, {}, 0)
        first = next(iter(ledger.intents))
        ledger.reconcile(set(), set(), 1008)
        ledger.plan({'tank': 1}, {}, 1008)
        self.assertFalse(ledger.requests())
        ledger.plan({'tank': 1}, {}, 1056)
        second = next(iter(ledger.intents))
        self.assertNotEqual(first, second)
        self.assertEqual(ledger.intents[second]['expires'], 2064)
        self.assertEqual(ledger.remaining('barracks'), 0)

    def test_expired_disappeared_forecast_does_not_rearm_itself(self):
        ledger = ProductionIntents()
        ledger.plan({'tank': 1}, {}, 0)
        ledger.reconcile(set(), set(), 1008)
        ledger.plan({}, {}, 1056)
        self.assertFalse(ledger.requests())

    def test_one_actor_is_never_assigned_twice(self):
        ledger = ProductionIntents()
        ledger.plan({'a': 1, 'b': 1}, {}, 0)
        ledger.reserve('a', 10, 0)
        with self.assertRaises(ValueError):
            ledger.reserve('b', 10, 0)

    def test_reservation_preserves_priority_without_hardcoded_families(self):
        self.assertEqual(remaining_budget((85, 0), (100, 0)), (0, 0))
        self.assertEqual(remaining_budget((600, 200), (400, 300)), (200, 0))

    def fulfil(self, ledger, goal, loop, actor=10):
        ticket = ledger.reserve(goal, actor, loop)
        ledger.acknowledge(ticket, True)
        ledger.reconcile({(actor, goal)}, {actor}, loop+8)

    def test_standing_count_cannot_repeat_fulfilment_within_forecast_horizon(self):
        ledger = ProductionIntents()
        ledger.plan({'depot': 1}, {}, 0)
        self.fulfil(ledger, 'depot', 0)
        ledger.plan({'depot': 1}, {}, 48)
        self.assertFalse(ledger.requests())
        ledger.plan({'depot': 1}, {}, 1008)
        self.assertFalse(ledger.requests())
        ledger.plan({'depot': 1}, {}, 1016)
        self.assertEqual(ledger.requests(), ['depot'])

    def test_count_increase_allows_new_work_and_families_are_independent(self):
        ledger = ProductionIntents()
        ledger.plan({'marine': 1}, {}, 0)
        self.fulfil(ledger, 'marine', 0)
        ledger.plan({'marine': 2, 'depot': 1}, {}, 48)
        self.assertEqual(set(ledger.requests()), {'marine', 'depot'})

    def test_engine_queue_and_recent_fulfilment_are_not_charged_twice(self):
        ledger = ProductionIntents()
        ledger.plan({'marine': 2}, {}, 0)
        self.fulfil(ledger, 'marine', 0)
        ledger.plan({'marine': 2}, {'marine': 1}, 48)
        self.assertEqual(ledger.requests(), ['marine'])
