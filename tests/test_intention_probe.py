import importlib.util
import unittest
import time

import numpy as np


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy absent")
class IntentionProbeTests(unittest.TestCase):
    def setUp(self):
        from tests.test_entity_examples import EntityExamplesTests
        from src.learning.entity_examples import state_inputs

        fixture = EntityExamplesTests()
        fixture.setUp()
        self.inputs = state_inputs(fixture.state, 8, 12, missing_fields=True)

    def test_state_excludes_history_references_and_preserves_native_counts(self):
        from src.learning.intention_probe import probe_features

        state, history = probe_features(self.inputs, 8, 12)
        encoder = [a.copy() for a in self.inputs["encoder"]]
        encoder[0][:, 30:94] = 1
        encoder[0][:, 124:] = 0
        encoder[4] = np.array([0, 4])
        encoder[5] = np.ones((2, 9))
        changed, changed_history = probe_features(
            dict(self.inputs, encoder=tuple(encoder)), 8, 12
        )
        np.testing.assert_array_equal(state.toarray(), changed.toarray())
        self.assertNotEqual(
            history.toarray().tolist(), changed_history.toarray().tolist()
        )
        # Unknown ability0 is a present unknown event, not padding.
        slot_width = 12 + 11
        self.assertEqual(changed_history[0, 30 * slot_width], 1)
        self.assertEqual(changed_history[0, 30 * slot_width + 12 + 9], 1)
        self.assertEqual(changed_history[0, 30 * slot_width + 12 + 10], 1)
        index = int(np.flatnonzero(encoder[0][:, 2])[0])
        encoder[1][index] = (encoder[1][index] + 1) % 8
        new_state, _ = probe_features(dict(self.inputs, encoder=tuple(encoder)), 8, 12)
        self.assertNotEqual(state.toarray().tolist(), new_state.toarray().tolist())

    def test_masks_and_entity_order_do_not_leak_missing_values(self):
        from src.learning.intention_probe import probe_features

        encoder = [a.copy() for a in self.inputs["encoder"]]
        encoder[0][:, 104] = 0  # Energy availability,94 + column10.
        scene_size = len(encoder[3]) // 2
        encoder[3][scene_size + 3] = 0
        masked = dict(self.inputs, encoder=tuple(encoder))
        expected, _ = probe_features(masked, 8, 12)
        encoder[0][:, 10] = 999
        encoder[3][3] = 999
        poisoned, _ = probe_features(dict(self.inputs, encoder=tuple(encoder)), 8, 12)
        np.testing.assert_array_equal(expected.toarray(), poisoned.toarray())
        for index in (0, 1, 2):
            encoder[index] = encoder[index][::-1].copy()
        reordered, _ = probe_features(dict(self.inputs, encoder=tuple(encoder)), 8, 12)
        np.testing.assert_allclose(expected.toarray(), reordered.toarray(), atol=1e-12)

    def test_fold_only_scaling_learning_and_solver_deadline(self):
        from scipy.sparse import csr_matrix
        from src.learning.intention_probe import fit_probe, probe_logits

        train = csr_matrix([[-2, 0], [-1, 0], [1, 0], [2, 0]], dtype=float)
        labels = np.array([3, 3, 5, 5])
        model, report = fit_probe(
            train,
            labels,
            regularization=0.01,
            max_iterations=100,
            deadline=time.monotonic() + 2,
        )
        self.assertEqual(report["status"], "converged")
        np.testing.assert_array_equal(model["columns"], [0])
        np.testing.assert_allclose(model["scales"], [np.sqrt(2.5)])
        self.assertEqual(
            model["classes"][probe_logits(model, train).argmax(axis=1)].tolist(),
            labels.tolist(),
        )
        held = csr_matrix([[2, 999]], dtype=float)
        clean = csr_matrix([[2, 0]], dtype=float)
        np.testing.assert_array_equal(
            probe_logits(model, held), probe_logits(model, clean)
        )
        expired, report = fit_probe(
            train, labels, regularization=0.01, max_iterations=100, deadline=0
        )
        self.assertEqual(report["status"], "wall_bound")
        self.assertEqual(report["objective_calls"], 0)
        self.assertTrue(np.isfinite(probe_logits(expired, held)).all())

    def test_metrics_include_unseen_labels_and_macro_false_positives(self):
        from scipy.sparse import csr_matrix
        from src.learning.intention_probe import probe_metrics

        model = dict(
            classes=np.array([3, 5]),
            columns=np.array([0]),
            scales=np.array([1]),
            weights=np.array([[-1, 1]]),
            bias=np.array([0, 0]),
        )
        values = csr_matrix([[-2], [2], [2], [2]], dtype=float)
        metrics = probe_metrics(model, values, np.array([3, 5, 7, 3]), {5, 7})
        self.assertEqual(metrics["top1"], 0.5)
        self.assertEqual(metrics["top3"], 0.75)
        self.assertEqual(metrics["macro_exact_recall"], 0.5)
        self.assertEqual(metrics["macro_family_recall"], 1)
        self.assertEqual(metrics["macro_false_positive_rate"], 0.5)
        self.assertEqual(metrics["absent_training_abilities"], {"7": 1})
        self.assertEqual(metrics["per_ability"]["7"]["top1_correct"], 0)
        expected = (
            -2 * np.log(1 / (1 + np.exp(-4)))
            - np.log(1e-12)
            - np.log(1 / (1 + np.exp(4)))
        ) / 4
        self.assertAlmostEqual(metrics["cross_entropy"], expected)
