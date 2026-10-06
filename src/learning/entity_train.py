"""CPU-only supervised joint command fit on disjoint terminal human replays."""

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from src.learning.actor_selection import construction_products
from src.learning.entity_audit import audit_commands
from src.learning.entity_encoder import JointEntityEncoder
from src.learning.entity_examples import replay_examples
from src.learning.entity_policy import JointEntityPolicy

DELAYS = (0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_datasets(train, validation):
    sources, seen = [], set()
    if not train:
        raise ValueError("At least one teaching replay is required")
    for role, paths in (("teaching", train), ("diagnostic", validation)):
        for directory in paths:
            receipt = json.loads((directory / "dataset.json").read_text())
            if (
                receipt["status"] != "completed"
                or receipt.get("disable_fog") is not False
                or receipt.get("alignment") != "state_at_action_loop_minus_one"
                or not receipt.get("teacher_kind", "").startswith("human")
                or receipt["player"]["player_info"]["race_actual"] != 1
            ):
                raise ValueError("Use complete fog-safe human Terran demonstrations")
            unresolved = {
                item["event"]["_gameloop"]
                for item in receipt.get("issued_command_audit", {}).get(
                    "unresolved_events", []
                )
            }
            if unresolved:
                with gzip.open(directory / "examples.jsonl.gz", "rt") as stream:
                    for row in map(json.loads, stream):
                        gap = row["next_action_delay"]
                        if gap is not None and any(
                            row["action_loop"] < loop < row["action_loop"] + gap
                            for loop in unresolved
                        ):
                            raise ValueError(
                                "Mask timing gaps crossing unresolved human events"
                            )
            identity = receipt["sha256"]
            if identity in seen:
                raise ValueError("A replay may occur in only one split and view")
            seen.add(identity)
            sources.append(
                dict(
                    dataset=str(directory.absolute()),
                    replay_sha256=identity,
                    role=role,
                    bindings={
                        str(directory / name): digest(directory / name)
                        for name in ("dataset.json", "static.json", "examples.jsonl.gz")
                    },
                )
            )
    return sources


def collect(paths, counts, spatial=False):
    examples, reports = [], []
    for directory in paths:
        static = json.loads((directory / "static.json").read_text())["game_data"]
        actual = [
            max(x[key] for x in static[name]) + 1
            for name, key in (
                ("units", "unit_id"),
                ("abilities", "ability_id"),
                ("upgrades", "upgrade_id"),
            )
        ]
        if actual != list(counts):
            raise ValueError("All replay datasets must use the same engine vocabulary")
        start = len(examples)
        examples.extend(
            replay_examples(
                directory,
                *counts,
                DELAYS,
                construction_products(static),
                spatial=spatial,
            )
        )
        receipt = json.loads((directory / "dataset.json").read_text())
        expected = receipt["issued_command_audit"]["matched_issued_commands"]
        if len(examples) - start != expected:
            raise ValueError(
                "Converted command count differs from terminal replay receipt"
            )
        excluded = Counter(reason for _, _, _, reason in examples[start:] if reason)
        reports.append(
            dict(
                dataset=str(directory),
                commands=len(examples) - start,
                exclusions=dict(excluded),
            )
        )
    return examples, reports


class Adam:
    def __init__(self, policy, rate):
        self.policy, self.rate, self.updates = policy, rate, 0
        self.m = {k: np.zeros_like(v) for k, v in policy.parameters.items()}
        self.v = {k: np.zeros_like(v) for k, v in policy.parameters.items()}

    def step(self, batch):
        if not batch:
            raise ValueError("A supervised batch must contain examples")
        gradients = {k: np.zeros_like(v) for k, v in self.policy.parameters.items()}
        loss = 0.0
        for inputs, label in batch:
            value, current = self.policy.loss_and_gradients(inputs, label)
            loss += value / len(batch)
            for name in gradients:
                gradients[name] += current[name] / len(batch)
        norm = np.sqrt(sum(float(np.square(g).sum()) for g in gradients.values()))
        if not np.isfinite(loss) or not np.isfinite(norm):
            raise ValueError("Nonfinite supervised loss or gradient")
        self.updates += 1
        scale = min(1.0, 5 / max(norm, 1e-8))
        for name, parameter in self.policy.parameters.items():
            gradient = gradients[name] * scale
            self.m[name] *= 0.9
            self.m[name] += 0.1 * gradient
            self.v[name] *= 0.999
            self.v[name] += 0.001 * gradient**2
            parameter -= (
                self.rate
                * self.m[name]
                / (1 - 0.9**self.updates)
                / (np.sqrt(self.v[name] / (1 - 0.999**self.updates)) + 1e-8)
            )
        return loss


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", nargs="+", type=Path, required=True)
    parser.add_argument("--validation", nargs="*", type=Path, default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, required=True)
    parser.add_argument(
        "--refinement",
        action="store_true",
        help="Selected-set ranking and cell-conditioned tile loss",
    )
    parser.add_argument(
        "--actor-cutoff",
        action="store_true",
        help="Learn a context-conditioned unit-selection cutoff",
    )
    parser.add_argument(
        "--actor-count",
        action="store_true",
        help="Learn variable unit-group size from human command labels",
    )
    parser.add_argument(
        "--spatial", action="store_true", help="Learn from full-resolution map patches"
    )
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--hidden", type=int, default=32)
    parser.add_argument("--rate", type=float, default=0.001)
    parser.add_argument("--seed", type=int, default=7000)
    parser.add_argument("--wall-seconds", type=float, required=True)
    args = parser.parse_args()
    if (
        min(args.epochs, args.batch_size, args.hidden, args.rate, args.wall_seconds)
        <= 0
    ):
        parser.error("Training sizes, rate and wall bound must be positive")
    if args.output.exists():
        parser.error("Use a fresh output directory for a frozen experiment")
    sources = validate_datasets(args.train, args.validation)
    static = json.loads((args.train[0] / "static.json").read_text())["game_data"]
    counts = [
        max(x[key] for x in static[name]) + 1
        for name, key in (
            ("units", "unit_id"),
            ("abilities", "ability_id"),
            ("upgrades", "upgrade_id"),
        )
    ]
    source_files = [
        Path(__file__),
        *[
            Path(__file__).with_name(name + ".py")
            for name in (
                "entity_spatial",
                "spatial_construction",
                "global_imitation",
                "entity_encoder",
                "entity_examples",
                "entity_policy",
                "entity_audit",
                "teacher_states",
                "gameplay",
                "actor_selection",
            )
        ],
    ]
    code_before = {str(p.absolute()): digest(p) for p in source_files}
    configuration = dict(
        sources=sources,
        code_before=code_before,
        vocabulary=counts,
        epochs=args.epochs,
        batch_size=args.batch_size,
        hidden=args.hidden,
        rate=args.rate,
        refinement=args.refinement,
        actor_cutoff=args.actor_cutoff,
        actor_count=args.actor_count,
        spatial=args.spatial,
        seed=args.seed,
        wall_seconds=args.wall_seconds,
        delays=DELAYS,
        point_tolerance=1,
        sampling="Uniform commands, shuffled each epoch",
        scope="Fixed human supervised experiment; no RL or native game; validation is reused diagnostic",
    )
    args.output.mkdir(parents=True)
    (args.output / "configuration.json").write_text(
        json.dumps(configuration, indent=2) + "\n"
    )
    start = time.monotonic()
    teaching, teaching_reports = collect(args.train, counts, spatial=args.spatial)
    validation, validation_reports = collect(
        args.validation, counts, spatial=args.spatial
    )
    fitting = [(inputs, label) for inputs, label, _, _ in teaching if label is not None]
    if not fitting:
        raise ValueError("No representable teaching commands")
    sample = fitting[0][0]["encoder"]
    policy = JointEntityPolicy(
        JointEntityEncoder(
            sample[0].shape[1],
            len(sample[3]),
            sample[5].shape[1],
            counts[0],
            counts[1],
            hidden=args.hidden,
            seed=args.seed,
        ),
        DELAYS,
        seed=args.seed + 1,
        refinement=args.refinement,
        actor_cutoff=args.actor_cutoff,
        actor_count=args.actor_count,
        spatial_features=fitting[0][0]["point_features"].shape[1]
        if args.spatial
        else 2,
    )
    optimizer = Adam(policy, args.rate)
    rng = np.random.default_rng(args.seed + 2)
    fit_start = time.monotonic()
    history = []
    status = "completed"
    for epoch in range(args.epochs):
        order = rng.permutation(len(fitting))
        total_loss, processed = 0.0, 0
        for begin in range(0, len(order), args.batch_size):
            if time.monotonic() - fit_start >= args.wall_seconds:
                status = "wall_bound"
                break
            batch = [fitting[int(i)] for i in order[begin : begin + args.batch_size]]
            loss = optimizer.step(batch)
            total_loss += loss * len(batch)
            processed += len(batch)
        record = dict(
            epoch=epoch + 1,
            commands=processed,
            mean_loss=total_loss / max(processed, 1),
            updates=optimizer.updates,
            seconds=time.monotonic() - fit_start,
        )
        history.append(record)
        with (args.output / "progress.jsonl").open("a") as stream:
            stream.write(json.dumps(record) + "\n")
        print(json.dumps(record), flush=True)
        if status != "completed":
            break
    policy.save(
        args.output / "policy.npz",
        dict(configuration=configuration, updates=optimizer.updates, status=status),
    )
    checkpoint_before = digest(args.output / "policy.npz")
    report = dict(
        status=status,
        history=history,
        optimizer_updates=optimizer.updates,
        teaching_sources=teaching_reports,
        validation_sources=validation_reports,
        teaching=audit_commands(policy, teaching),
        validation=audit_commands(policy, validation),
        checkpoint_sha256=checkpoint_before,
        elapsed_seconds=time.monotonic() - start,
    )
    after = validate_datasets(args.train, args.validation)
    code_after = {str(p.absolute()): digest(p) for p in source_files}
    report["bindings_unchanged"] = (
        sources == after
        and code_before == code_after
        and checkpoint_before == digest(args.output / "policy.npz")
    )
    if not report["bindings_unchanged"]:
        raise ValueError("Experiment inputs/code or evaluated checkpoint changed")
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            dict(
                status=status,
                updates=optimizer.updates,
                seconds=report["elapsed_seconds"],
                teaching_complete=report["teaching"]["predicted"]["complete"],
                validation_complete=report["validation"]["predicted"]["complete"],
            )
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
