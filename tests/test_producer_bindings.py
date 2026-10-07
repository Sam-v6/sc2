import unittest

from src.learning.producer_bindings import ProducerBindings


class ProducerBindingsTests(unittest.TestCase):
    def test_identity_survives_lift_and_landing(self):
        bindings = ProducerBindings()
        bindings.bind(100, 10000000001)
        for kind, flying in [(21, False), (46, True), (21, False)]:
            actor = dict(tag=10000000001, alliance=1, unit_type=kind, is_flying=flying)
            self.assertEqual(bindings.resolve(100, dict(units=[actor])), actor)

    def test_actor_loss_does_not_select_replacement(self):
        bindings = ProducerBindings()
        bindings.bind(100, 1)
        self.assertIsNone(bindings.resolve(100, dict(units=[dict(tag=2, alliance=1)])))
        self.assertIsNone(bindings.resolve(100, dict(units=[dict(tag=1, alliance=4)])))
        self.assertIsNone(bindings.resolve(200, dict(units=[dict(tag=1, alliance=1)])))

    def test_duplicate_and_changed_bindings_rejected(self):
        bindings = ProducerBindings()
        bindings.bind(100, 1)
        bindings.bind(100, 1)
        with self.assertRaises(ValueError):
            bindings.bind(100, 2)
        with self.assertRaises(ValueError):
            bindings.bind(200, 1)
