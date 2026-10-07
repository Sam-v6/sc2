"""One frozen paired human-imitation source comparison; no RL."""

import hashlib
from collections import Counter
import gzip
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch

from src.learning.actor_selection import construction_products
from src.learning.entity_audit import audit_commands
from src.learning.entity_train import collect, validate_datasets
from src.learning.goal_first_policy import GoalFirstPolicy
from src.learning.goal_first_train import (
    fit_goal_first,
    prediction_history_examples,
    teaching_support,
)
from src.learning.teacher_states import teacher_states

ROOT = Path("logs/roadmap")
OUT = ROOT / "repaired-production-imitation-01"
TRAIN = ("294", "870", "955", "839", "991", "523")
HELD = ("887", "920", "851")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def ability_metrics(examples, predictions, macro_ids):
    labels = np.array([c.ability for _, _, c, _ in examples])
    predicted = np.array([p["ability"] for p in predictions])
    macro = np.isin(labels, list(macro_ids))
    selected = np.isin(predicted, list(macro_ids))
    correct = labels == predicted
    return dict(
        rows=len(labels),
        macro_rows=int(macro.sum()),
        ability_correct=int(correct.sum()),
        macro_correct=int((macro & correct).sum()),
        macro_recall=float((macro & correct).sum() / macro.sum()),
        macro_false_positives=int((~macro & selected).sum()),
        macro_false_positive_rate=float((~macro & selected).sum() / (~macro).sum()),
    )


assert not OUT.exists()
assert os.environ["CUDA_VISIBLE_DEVICES"] == ""
assert os.environ["OPENBLAS_NUM_THREADS"] == os.environ["OMP_NUM_THREADS"] == "2"
torch.set_num_threads(2)
torch.set_num_interop_threads(2)
config_path = ROOT / "joint-professional-fit-05/configuration.json"
config = read(config_path)
sources = [s for s in config["sources"] if s["role"] == "teaching"]
paths = {Path(s["dataset"]).name: Path(s["dataset"]) for s in sources}
assert set(paths) == set(TRAIN + HELD)
train, held = ([paths[g] for g in names] for names in (TRAIN, HELD))
bindings = {str(config_path): sha(config_path)}
for source in sources:
    bindings.update(source["bindings"])
code_paths = [
    *config["code_before"],
    "src/learning/goal_first_policy.py",
    "src/learning/goal_first_train.py",
    "src/learning/entity_type_status.py",
    __file__,
    os.environ["SC2_IMITATION_WATCHDOG"],
    "docs/superpowers/plans/2026-10-06-repaired-production-imitation.md",
]
bindings.update({str(p): sha(p) for p in code_paths})
for path, digest in bindings.items():
    assert sha(path) == digest
started = time.monotonic()
validated = validate_datasets(train, held, missing_fields=True)
games = {}
for game in TRAIN + HELD:
    games[game] = collect(
        [paths[game]], config["vocabulary"], spatial=True, missing_fields=True
    )[0]
    print(
        json.dumps(dict(stage="loaded", game=game, rows=len(games[game]))), flush=True
    )
original = [e for g in TRAIN for e in games[g]]
validation = [e for g in HELD for e in games[g]]
repaired_paths = {g: ROOT / "pro-demonstrations-production-08" / g for g in TRAIN}
repaired_sources = validate_datasets(
    list(repaired_paths.values()), [], missing_fields=True
)
for directory in repaired_paths.values():
    for filename in ("dataset.json", "static.json", "examples.jsonl.gz"):
        path = directory / filename
        bindings[str(path)] = sha(path)
repaired_games = {}
for game in TRAIN:
    repaired_games[game] = collect(
        [repaired_paths[game]], config["vocabulary"], spatial=True, missing_fields=True
    )[0]
    print(
        json.dumps(
            dict(stage="loaded_repaired", game=game, rows=len(repaired_games[game]))
        ),
        flush=True,
    )
repaired = [e for g in TRAIN for e in repaired_games[g]]
original_fit = [(x, y) for x, y, _, _ in original if y is not None]
repaired_fit = [(x, y) for x, y, _, _ in repaired if y is not None]
assert len(original) == 3400 and len(repaired) == 3546 and len(validation) == 1113
assert len(original_fit) == 3398 and len(repaired_fit) == 3544
# Compare the same newly recovered human command rows under both models.
recovered_indices = []
offset = 0
for game in TRAIN:
    with gzip.open(paths[game] / "examples.jsonl.gz", "rt") as stream:
        old_keys = {
            (r["action_loop"], r["source_sequence"]) for r in map(json.loads, stream)
        }
    with gzip.open(repaired_paths[game] / "examples.jsonl.gz", "rt") as stream:
        new_rows = list(map(json.loads, stream))
    recovered_indices.extend(
        offset + i
        for i, r in enumerate(new_rows)
        if (r["action_loop"], r["source_sequence"]) not in old_keys
    )
    offset += len(new_rows)
assert len(recovered_indices) == 146
fit_lookup = {
    raw_index: fit_index
    for fit_index, raw_index in enumerate(
        i for i, e in enumerate(repaired) if e[1] is not None
    )
}
recovered_fitting_indices = [fit_lookup[i] for i in recovered_indices]
recovered = [repaired[i] for i in recovered_indices]
x = original_fit[0][0]
entities, types, orders, scene, history, roles = x["encoder"]
dimensions = (
    entities.shape[1],
    len(scene),
    roles.shape[1],
    *config["vocabulary"][:2],
    x["point_features"].shape[1],
)
base = GoalFirstPolicy(
    dimensions, (0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512), hidden=64, seed=8156
)
candidate = GoalFirstPolicy(dimensions, base.delays, hidden=64, seed=8156)
support = teaching_support(base, original_fit + repaired_fit)
for p in (base, candidate):
    p.clear_unseen_inputs(support)
assert all(
    torch.equal(value, candidate.state_dict()[name])
    for name, value in base.state_dict().items()
)
assert base.predict(x) == candidate.predict(x)
rng = np.random.default_rng(8157)
sample_indices = [
    rng.choice(len(repaired_fit), len(original_fit), replace=False).tolist()
    for _ in range(30)
]
check_rng = np.random.default_rng(8157)
assert sample_indices == [
    check_rng.choice(len(repaired_fit), len(original_fit), replace=False).tolist()
    for _ in range(30)
]
assert all(len(set(indices)) == 3398 for indices in sample_indices)
assert len(set(i for indices in sample_indices for i in indices)) == 3544
static = read(train[0] / "static.json")["game_data"]
macro_ids = {
    a["ability_id"]
    for a in static["abilities"]
    if any(
        k in a.get("friendly_name", "").upper()
        for k in ("BUILD ", "TRAIN ", "RESEARCH ")
    )
}
contract = dict(
    preflight_receipt_sha256=sha(
        ROOT / "repaired-production-imitation-01.preflight.json"
    )
    if (ROOT / "repaired-production-imitation-01.preflight.json").exists()
    else None,
    preflight_reporting_amendment="Executed preflight snapshot preserved; final initialization/sampling assertions repeat before fitting. Post-review change labels planned exposure and calculates actual exposure.",
    bindings=bindings,
    sources=validated + repaired_sources,
    train=TRAIN,
    held=HELD,
    vocabulary=config["vocabulary"],
    dimensions=dimensions,
    hidden=64,
    seed=8156,
    shuffle_seed=8156,
    epochs=30,
    optimizer_seconds_per_arm=600,
    batch_size=16,
    rate=0.001,
    support_neutralization="Union of both teaching-only source versions; identical initial weights.",
    original_training_rows=len(original),
    repaired_training_rows=len(repaired),
    fitting_rows_per_epoch=len(original_fit),
    sample_seed=8157,
    sample_indices=sample_indices,
    recovered_indices=recovered_indices,
    recovered_fitting_indices=recovered_fitting_indices,
    planned_recovered_presentations={
        str(i): sum(i in indices for indices in sample_indices)
        for i in recovered_fitting_indices
    },
    held_rows=len(validation),
    arms=["original", "repaired"],
    macro_ids=sorted(macro_ids),
    runtime=dict(
        executable=sys.executable,
        torch=torch.__version__,
        numpy=np.__version__,
        threads=2,
        cpu=True,
        cuda_initialized=torch.cuda.is_initialized(),
    ),
    gates=dict(
        matched_epochs=30,
        macro_recall_gain=0.10,
        complete_fraction_gain=0.05,
        max_false_positive_increase=0.05,
        own_macro_recall_gain=0.10,
        recovered_ability_gain=0.25,
        recovered_complete_gain=0.25,
    ),
    history="Original causal human event-slot history for supervised teaching and ordinary audits; final-policy history on unchanged human states is diagnostic only.",
    scope="Fresh matched-budget source-intervention human fits; three held games have prior development diagnostic use. No774/reserved/native/RL; no acceptance or promotion.",
)
if os.environ.get("SC2_REPAIRED_PRODUCTION_PREFLIGHT_ONLY") == "1":
    assert all(sha(p) == digest for p, digest in bindings.items())
    write(
        ROOT / "repaired-production-imitation-01.preflight.json",
        dict(
            status="preflight_passed_no_fit",
            contract=contract,
            initial_base_weight_parity=True,
            initial_teaching_prediction_parity=True,
            optimizer_updates=0,
        ),
    )
    print(
        json.dumps(
            dict(status="preflight_passed_no_fit", fitting_rows=len(original_fit))
        ),
        flush=True,
    )
    sys.exit(0)
OUT.mkdir()
np.savez_compressed(OUT / "teaching-support.npz", **support)
contract["support_sha256"] = sha(OUT / "teaching-support.npz")
write(OUT / "contract.json", contract)
for name, p in [("original", base), ("repaired", candidate)]:
    arm = OUT / name
    arm.mkdir()
    p.save(
        arm / "initial.npz",
        dict(contract_sha256=sha(OUT / "contract.json"), stage="initial", arm=name),
    )
    print(
        json.dumps(
            dict(
                stage="fit_started",
                arm=name,
                parameters=sum(v.numel() for v in p.parameters()),
            )
        ),
        flush=True,
    )
    fitting = (
        original_fit
        if name == "original"
        else [repaired_fit[i] for i in sample_indices[0]]
    )

    def refresh(policy, epoch, deadline):
        if time.monotonic() >= deadline:
            raise TimeoutError("Sample selection deadline")
        return [repaired_fit[i] for i in sample_indices[epoch]]

    fitted = fit_goal_first(
        p,
        fitting,
        epochs=30,
        batch_size=16,
        rate=0.001,
        seconds=600,
        seed=8156,
        refresh_examples=refresh if name == "repaired" else None,
    )
    assert fitted["updates"] <= 6390 and fitted["presentations"] <= 101940
    actual_exposure = Counter()
    if name == "repaired":
        replay_rng = np.random.default_rng(8156)
        recovered_set = set(recovered_fitting_indices)
        for epoch in fitted["history"]:
            order = replay_rng.permutation(len(original_fit))
            seen = epoch["presentations"]
            sampled = sample_indices[epoch["epoch"] - 1]
            actual_exposure.update(
                sampled[j] for j in order[:seen] if sampled[j] in recovered_set
            )
    fitted["actual_recovered_presentations"] = {
        str(i): actual_exposure[i] for i in recovered_fitting_indices
    }
    assert (
        sum(epoch["presentations"] for epoch in fitted["history"])
        == fitted["presentations"]
    )
    write(arm / "fit.json", fitted)
    p.save(
        arm / "policy.npz",
        dict(
            contract_sha256=sha(OUT / "contract.json"),
            fit_status=fitted["status"],
            arm=name,
        ),
    )
    loaded, _ = GoalFirstPolicy.load(arm / "policy.npz")
    report = dict(
        checkpoint_sha256=sha(arm / "policy.npz"),
        teaching=audit_commands(p, original if name == "original" else repaired),
        common_repaired_teaching=audit_commands(p, repaired),
        recovered=audit_commands(p, recovered),
        held=audit_commands(p, validation),
        commands=[],
        ability={},
        own_history={},
    )
    evaluation_games = dict(repaired_games, **{g: games[g] for g in HELD})
    for game in TRAIN + HELD:
        predictions = []
        for index, (inputs, label, command, reason) in enumerate(
            evaluation_games[game]
        ):
            prediction = p.predict(inputs)
            assert prediction == loaded.predict(inputs)
            predictions.append(prediction)
            report["commands"].append(
                dict(
                    game=game,
                    row=index,
                    prediction=prediction,
                    command=command.as_dict(),
                    exclusion=reason,
                )
            )
        report["ability"][game] = ability_metrics(
            evaluation_games[game], predictions, macro_ids
        )
    report["recovered_families"] = {}
    for ability in sorted({c.ability for _, _, c, _ in recovered}):
        examples = [e for e in recovered if e[2].ability == ability]
        report["recovered_families"][str(ability)] = dict(
            name=next(
                a["friendly_name"]
                for a in static["abilities"]
                if a["ability_id"] == ability
            ),
            audit=audit_commands(p, examples),
        )
    ordinary_held = [r["prediction"] for r in report["commands"] if r["game"] in HELD]
    report["held_ability"] = ability_metrics(validation, ordinary_held, macro_ids)
    own_predictions = []
    for game in HELD:
        rebuilt, records = prediction_history_examples(
            p,
            games[game],
            teacher_states(paths[game]),
            config["vocabulary"],
            construction_products(read(paths[game] / "static.json")["game_data"]),
        )
        assert all(
            loaded.predict(inputs) == r["prediction"]
            for (inputs, _, _, _), r in zip(rebuilt, records, strict=True)
        )
        report["own_history"][game] = dict(
            audit=audit_commands(p, rebuilt),
            ability=ability_metrics(
                rebuilt, [r["prediction"] for r in records], macro_ids
            ),
        )
        own_predictions.extend(r["prediction"] for r in records)
        write(arm / f"{game}-own-history.json", records)
    report["own_held_ability"] = ability_metrics(validation, own_predictions, macro_ids)
    write(arm / "report.json", report)
    print(
        json.dumps(
            dict(
                stage="arm_finished",
                arm=name,
                fit_status=fitted["status"],
                epochs=fitted["epochs_completed"],
                held_macro=report["held_ability"]["macro_recall"],
                held_complete=report["held"]["predicted"]["complete"],
                own_macro=report["own_held_ability"]["macro_recall"],
            )
        ),
        flush=True,
    )
a, b = (read(OUT / name / "report.json") for name in ("original", "repaired"))
fa, fb = (read(OUT / name / "fit.json") for name in ("original", "repaired"))
gates = dict(
    matched_epochs=fa["epochs_completed"] == fb["epochs_completed"] == 30
    and fa["status"] == fb["status"] == "completed"
    and fa["updates"] == fb["updates"] == 6390
    and fa["presentations"] == fb["presentations"] == 101940,
    macro_recall_gain=b["held_ability"]["macro_recall"]
    >= a["held_ability"]["macro_recall"] + 0.10,
    complete_gain=b["held"]["predicted"]["complete"] / len(validation)
    >= a["held"]["predicted"]["complete"] / len(validation) + 0.05,
    false_positives=b["held_ability"]["macro_false_positive_rate"]
    <= a["held_ability"]["macro_false_positive_rate"] + 0.05,
    own_macro_recall_gain=b["own_held_ability"]["macro_recall"]
    >= a["own_held_ability"]["macro_recall"] + 0.10,
    recovered_ability_gain=b["recovered"]["predicted"]["ability"] / 146
    >= a["recovered"]["predicted"]["ability"] / 146 + 0.25,
    recovered_complete_gain=b["recovered"]["predicted"]["complete"] / 146
    >= a["recovered"]["predicted"]["complete"] / 146 + 0.25,
)
assert (
    all(sha(p) == digest for p, digest in bindings.items())
    and not torch.cuda.is_initialized()
)
comparison = dict(
    status="completed",
    gates=gates,
    all_gates_passed=all(gates.values()),
    contract_sha256=sha(OUT / "contract.json"),
    arm_bindings={
        name: {
            file: sha(OUT / name / file)
            for file in ["initial.npz", "fit.json", "policy.npz", "report.json"]
        }
        for name in ("original", "repaired")
    },
    seconds=time.monotonic() - started,
    bindings_unchanged=True,
    promoted=False,
    native_games=0,
    rl_updates=0,
)
write(OUT / "comparison.json", comparison)
print(json.dumps(comparison), flush=True)
