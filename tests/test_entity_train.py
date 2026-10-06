import gzip
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from tests import test_entity_policy

try:
    from src.learning.entity_train import Adam, validate_datasets
except ImportError:
    Adam = validate_datasets = None


class EntityTrainTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(Adam, "joint supervised trainer is missing")

    def dataset(self, root, name, replay_hash, status="completed"):
        directory = root / name
        directory.mkdir()
        (directory / "dataset.json").write_text(
            json.dumps(
                dict(
                    status=status,
                    sha256=replay_hash,
                    disable_fog=False,
                    alignment="state_at_action_loop_minus_one",
                    teacher_kind="human_unverified",
                    player={"player_info": {"race_actual": 1}},
                )
            )
        )
        (directory / "static.json").write_text("{}")
        (directory / "examples.jsonl.gz").write_bytes(b"placeholder")
        return directory

    def test_split_rejects_the_same_replay_even_under_different_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            train = self.dataset(root, "train", "same-replay")
            validation = self.dataset(root, "other-view", "same-replay")
            with self.assertRaises(ValueError):
                validate_datasets([train], [validation])

    def test_partial_or_fog_disabled_demonstrations_cannot_train(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            partial = self.dataset(root, "partial", "different", status="wall_timeout")
            with self.assertRaises(ValueError):
                validate_datasets([partial], [])
            complete = self.dataset(root, "complete", "complete")
            receipt = json.loads((complete / "dataset.json").read_text())
            receipt["disable_fog"] = True
            (complete / "dataset.json").write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):
                validate_datasets([complete], [])

    def test_disjoint_terminal_human_sources_have_bound_input_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            train = self.dataset(root, "train", "train-replay")
            validation = self.dataset(root, "validation", "validation-replay")
            sources = validate_datasets([train], [validation])
            self.assertEqual(sources[0]["role"], "teaching")
            self.assertEqual(sources[1]["role"], "diagnostic")
            self.assertEqual(len(sources[0]["bindings"]), 3)
            self.assertTrue(
                all(len(digest) == 64 for digest in sources[0]["bindings"].values())
            )

    def test_partial_professional_source_requires_its_encoder_and_phase_proof(self):
        from src.learning.entity_train import digest

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = self.dataset(root, "professional", "pro-replay")
            evidence = root / "phase-evidence.bin"
            evidence.write_bytes(b"original timing evidence")
            proof = root / "phase.json"
            proof.write_text(
                json.dumps(
                    dict(
                        status="verified_native_phase_and_converter_buffer_contract",
                        bindings={str(evidence): digest(evidence)},
                    )
                )
            )
            receipt = json.loads((directory / "dataset.json").read_text())
            receipt.update(
                alignment="state_at_issue_loop_before_effect",
                teacher_kind="human_professional_partial",
                requires_missing_fields=True,
                training_eligible=True,
                source_phase_proof=str(proof),
                source_replay=str(proof),
                sha256=digest(proof),
                source_bindings={str(proof): digest(proof)},
                code_bindings={str(proof): digest(proof)},
            )
            (directory / "dataset.json").write_text(json.dumps(receipt))
            row = dict(
                action_loop=10,
                source_sequence=0,
                next_action_delay=None,
                commands=[dict(ability=3, units=[1])],
                observation=dict(
                    game_loop=10,
                    history_quality="event_slots",
                    recent_commands=[],
                    unknown_fields=dict(world=["command_history"]),
                ),
            )
            with gzip.open(directory / "examples.jsonl.gz", "wt") as stream:
                stream.write(json.dumps(row) + "\n")
            receipt["corpus_bindings"] = {
                name: digest(directory / name)
                for name in ("static.json", "examples.jsonl.gz")
            }
            (directory / "dataset.json").write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):
                validate_datasets([directory], [])
            sources = validate_datasets([directory], [], missing_fields=True)
            self.assertEqual(sources[0]["role"], "teaching")
            original = dict(receipt)
            receipt.update(
                alignment="state_at_action_loop_minus_one", training_eligible=False
            )
            (directory / "dataset.json").write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, "professional"):
                validate_datasets([directory], [], missing_fields=True)
            receipt = original
            (directory / "dataset.json").write_text(json.dumps(receipt))
            evidence.write_bytes(b"changed timing evidence")
            with self.assertRaisesRegex(ValueError, "binding"):
                validate_datasets([directory], [], missing_fields=True)
            evidence.write_bytes(b"original timing evidence")
            original_examples = (directory / "examples.jsonl.gz").read_bytes()
            (directory / "examples.jsonl.gz").write_bytes(b"changed corpus")
            with self.assertRaisesRegex(ValueError, "corpus binding"):
                validate_datasets([directory], [], missing_fields=True)
            (directory / "examples.jsonl.gz").write_bytes(original_examples)
            proof.write_text("{}")
            with self.assertRaisesRegex(ValueError, "binding"):
                validate_datasets([directory], [], missing_fields=True)

    def test_supervised_optimizer_reduces_joint_loss_and_updates_shared_embeddings(
        self,
    ):
        fixture = test_entity_policy.EntityPolicyTests()
        fixture.setUp()
        policy, inputs, label = fixture.policy, fixture.inputs, fixture.label
        initial, _ = policy.loss_and_gradients(inputs, label)
        original = policy.encoder.parameters["types"].copy()
        optimizer = Adam(policy, rate=0.01)
        for _ in range(50):
            optimizer.step([(inputs, label)])
        final, _ = policy.loss_and_gradients(inputs, label)
        self.assertLess(final, initial / 2)
        self.assertGreater(
            np.linalg.norm(policy.encoder.parameters["types"] - original), 0
        )
        self.assertEqual(optimizer.updates, 50)

    def timing_dataset(self, root, gap, unresolved_loop):
        directory = self.dataset(root, "timing", "timing-replay")
        receipt = json.loads((directory / "dataset.json").read_text())
        receipt["issued_command_audit"] = {
            "unresolved_events": [{"event": {"_gameloop": unresolved_loop}}]
        }
        (directory / "dataset.json").write_text(json.dumps(receipt))
        with gzip.open(directory / "examples.jsonl.gz", "wt") as stream:
            stream.write(
                json.dumps({"action_loop": 10, "next_action_delay": gap}) + "\n"
            )
        return directory

    def test_unresolved_human_event_cannot_cross_a_labeled_timing_gap(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = self.timing_dataset(Path(temporary), 20, 15)
            with self.assertRaises(ValueError):
                validate_datasets([directory], [])

    def test_masked_unknown_timing_remains_a_usable_human_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = self.timing_dataset(Path(temporary), None, 15)
            self.assertEqual(len(validate_datasets([directory], [])), 1)

    def test_events_at_gap_boundaries_do_not_invalidate_known_delay(self):
        for loop in (10, 30):
            with self.subTest(loop=loop), tempfile.TemporaryDirectory() as temporary:
                directory = self.timing_dataset(Path(temporary), 20, loop)
                self.assertEqual(len(validate_datasets([directory], [])), 1)


if __name__ == "__main__":
    unittest.main()
