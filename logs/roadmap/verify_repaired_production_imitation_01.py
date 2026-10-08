"""Reconstruct matched source-version imitation artifacts; never refit."""

from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from src.learning.actor_selection import construction_products
from src.learning.entity_audit import audit_commands
from src.learning.entity_train import collect, validate_datasets
from src.learning.goal_first_policy import GoalFirstPolicy
from src.learning.goal_first_train import prediction_history_examples, teaching_support
from src.learning.teacher_states import teacher_states

ROOT = Path("logs/roadmap/repaired-production-imitation-01")


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normal(value):
    return json.loads(json.dumps(value))


contract, comparison = read(ROOT / "contract.json"), read(ROOT / "comparison.json")
assert comparison["contract_sha256"] == sha(ROOT / "contract.json")
assert contract["arms"] == ["original", "repaired"]
assert contract["train"] == ["294", "870", "955", "839", "991", "523"]
assert contract["held"] == ["887", "920", "851"]
assert contract["epochs"] == 30 and contract["optimizer_seconds_per_arm"] == 600
assert contract["rate"] == 0.001 and contract["batch_size"] == 16
assert (
    contract["seed"] == contract["shuffle_seed"] == 8156
    and contract["sample_seed"] == 8157
)
for path, digest in contract["bindings"].items():
    assert sha(path) == digest, path
assert (
    sha("logs/roadmap/repaired-production-imitation-01.preflight.json")
    == contract["preflight_receipt_sha256"]
)
config = read("logs/roadmap/joint-professional-fit-05/configuration.json")
old_paths = {
    Path(s["dataset"]).name: Path(s["dataset"])
    for s in config["sources"]
    if s["role"] == "teaching"
}
new_paths = {
    g: Path("logs/roadmap/pro-demonstrations-production-08") / g
    for g in contract["train"]
}
sources = validate_datasets(
    [old_paths[g] for g in contract["train"]],
    [old_paths[g] for g in contract["held"]],
    missing_fields=True,
)
sources += validate_datasets(list(new_paths.values()), [], missing_fields=True)
assert sources == contract["sources"]
games, new_games = {}, {}
for game in contract["train"] + contract["held"]:
    games[game] = collect(
        [old_paths[game]], contract["vocabulary"], spatial=True, missing_fields=True
    )[0]
for game in contract["train"]:
    new_games[game] = collect(
        [new_paths[game]], contract["vocabulary"], spatial=True, missing_fields=True
    )[0]
    print(json.dumps(dict(stage="source_rebuilt", game=game)), flush=True)
old = [e for g in contract["train"] for e in games[g]]
new = [e for g in contract["train"] for e in new_games[g]]
held = [e for g in contract["held"] for e in games[g]]
old_fit = [(x, y) for x, y, _, _ in old if y is not None]
new_fit = [(x, y) for x, y, _, _ in new if y is not None]
assert len(old) == contract["original_training_rows"] == 3400
assert len(new) == contract["repaired_training_rows"] == 3546
assert (
    len(old_fit) == contract["fitting_rows_per_epoch"] == 3398 and len(new_fit) == 3544
)
assert len(held) == contract["held_rows"] == 1113
indices, offset = [], 0
for game in contract["train"]:
    with gzip.open(old_paths[game] / "examples.jsonl.gz", "rt") as stream:
        old_keys = {
            (r["action_loop"], r["source_sequence"]) for r in map(json.loads, stream)
        }
    with gzip.open(new_paths[game] / "examples.jsonl.gz", "rt") as stream:
        rows = list(map(json.loads, stream))
    indices.extend(
        offset + i
        for i, r in enumerate(rows)
        if (r["action_loop"], r["source_sequence"]) not in old_keys
    )
    offset += len(rows)
assert indices == contract["recovered_indices"] and len(indices) == 146
lookup = {
    raw: i for i, raw in enumerate(j for j, e in enumerate(new) if e[1] is not None)
}
fit_indices = [lookup[i] for i in indices]
assert fit_indices == contract["recovered_fitting_indices"]
recovered = [new[i] for i in indices]
rng = np.random.default_rng(8157)
samples = [rng.choice(3544, 3398, replace=False).tolist() for _ in range(30)]
assert samples == contract["sample_indices"]
assert {
    str(i): sum(i in sample for sample in samples) for i in fit_indices
} == contract["planned_recovered_presentations"]
expected = GoalFirstPolicy(
    contract["dimensions"],
    (0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512),
    hidden=64,
    seed=8156,
)
support = teaching_support(expected, old_fit + new_fit)
expected.clear_unseen_inputs(support)
assert sha(ROOT / "teaching-support.npz") == contract["support_sha256"]
with np.load(ROOT / "teaching-support.npz", allow_pickle=False) as archive:
    for key in support:
        np.testing.assert_array_equal(support[key], archive[key])
for name in contract["arms"]:
    policy, _ = GoalFirstPolicy.load(ROOT / name / "initial.npz")
    assert not policy.type_status
    for key, value in expected.state_dict().items():
        torch.testing.assert_close(value, policy.state_dict()[key], rtol=0, atol=0)
macro = set(contract["macro_ids"])
static = read(old_paths[contract["train"][0]] / "static.json")["game_data"]
assert macro == {
    a["ability_id"]
    for a in static["abilities"]
    if any(
        k in a.get("friendly_name", "").upper()
        for k in ("BUILD ", "TRAIN ", "RESEARCH ")
    )
}


def ability_metrics(examples, predictions):
    counts = Counter()
    for (_, _, gold, _), pred in zip(examples, predictions, strict=True):
        counts["rows"] += 1
        ismacro = gold.ability in macro
        counts["macro_rows"] += ismacro
        correct = gold.ability == pred["ability"]
        counts["ability_correct"] += correct
        counts["macro_correct"] += ismacro and correct
        counts["macro_false_positives"] += not ismacro and pred["ability"] in macro
    result = {
        k: counts[k]
        for k in (
            "rows",
            "macro_rows",
            "ability_correct",
            "macro_correct",
            "macro_false_positives",
        )
    }
    result["macro_recall"] = result["macro_correct"] / result["macro_rows"]
    result["macro_false_positive_rate"] = result["macro_false_positives"] / (
        result["rows"] - result["macro_rows"]
    )
    return result


reports, fits = {}, {}
ordinary_count = own_count = 0
for name in contract["arms"]:
    arm = ROOT / name
    for file, digest in comparison["arm_bindings"][name].items():
        assert sha(arm / file) == digest
    report, fit = read(arm / "report.json"), read(arm / "fit.json")
    policy, meta = GoalFirstPolicy.load(arm / "policy.npz")
    assert (
        meta["contract_sha256"] == sha(ROOT / "contract.json")
        and meta["fit_status"] == fit["status"]
    )
    assert (
        report["checkpoint_sha256"] == sha(arm / "policy.npz")
        and not policy.type_status
    )
    assert fit["optimizer_seconds"] <= 610 and fit["epochs_completed"] <= 30
    assert sum(e["presentations"] for e in fit["history"]) == fit["presentations"]
    assert (
        sum(int(np.ceil(e["presentations"] / 16)) for e in fit["history"])
        == fit["updates"]
    )
    if fit["status"] == "completed":
        assert fit["epochs_completed"] == len(fit["history"]) == 30
        assert fit["updates"] == 6390 and fit["presentations"] == 101940
    exposure = Counter()
    rng = np.random.default_rng(8156)
    for entry in fit["history"]:
        shuffled = rng.permutation(3398)
        if name == "repaired":
            for position in shuffled[: entry["presentations"]]:
                index = samples[entry["epoch"] - 1][position]
                if index in fit_indices:
                    exposure[index] += 1
    assert {str(i): exposure[i] for i in fit_indices} == fit[
        "actual_recovered_presentations"
    ]
    assert (
        audit_commands(policy, old if name == "original" else new) == report["teaching"]
    )
    assert audit_commands(policy, new) == report["common_repaired_teaching"]
    assert audit_commands(policy, recovered) == report["recovered"]
    assert audit_commands(policy, held) == report["held"]
    for ability in sorted({c.ability for _, _, c, _ in recovered}):
        subset = [e for e in recovered if e[2].ability == ability]
        assert report["recovered_families"][str(ability)]["audit"] == audit_commands(
            policy, subset
        )
    eval_games = dict(new_games, **{g: games[g] for g in contract["held"]})
    records = []
    for game, examples in eval_games.items():
        predictions = []
        for index, (inputs, _, gold, reason) in enumerate(examples):
            prediction = policy.predict(inputs)
            predictions.append(prediction)
            records.append(
                dict(
                    game=game,
                    row=index,
                    prediction=prediction,
                    command=gold.as_dict(),
                    exclusion=reason,
                )
            )
        assert ability_metrics(examples, predictions) == report["ability"][game]
    assert normal(records) == report["commands"]
    assert (
        ability_metrics(
            held, [r["prediction"] for r in records if r["game"] in contract["held"]]
        )
        == report["held_ability"]
    )
    ordinary_count += len(records)
    own = []
    for game in contract["held"]:
        rebuilt, rows = prediction_history_examples(
            policy,
            games[game],
            teacher_states(old_paths[game]),
            contract["vocabulary"],
            construction_products(read(old_paths[game] / "static.json")["game_data"]),
        )
        assert normal(rows) == read(arm / f"{game}-own-history.json")
        assert audit_commands(policy, rebuilt) == report["own_history"][game]["audit"]
        predictions = [r["prediction"] for r in rows]
        assert (
            ability_metrics(rebuilt, predictions)
            == report["own_history"][game]["ability"]
        )
        own.extend(predictions)
    assert ability_metrics(held, own) == report["own_held_ability"]
    own_count += len(own)
    reports[name], fits[name] = report, fit
    print(json.dumps(dict(stage="arm_verified", arm=name)), flush=True)
a, b = reports["original"], reports["repaired"]
fa, fb = fits["original"], fits["repaired"]
gates = dict(
    matched_epochs=fa["epochs_completed"] == fb["epochs_completed"] == 30
    and fa["status"] == fb["status"] == "completed"
    and fa["updates"] == fb["updates"] == 6390
    and fa["presentations"] == fb["presentations"] == 101940,
    macro_recall_gain=b["held_ability"]["macro_recall"]
    >= a["held_ability"]["macro_recall"] + 0.10,
    complete_gain=b["held"]["predicted"]["complete"] / 1113
    >= a["held"]["predicted"]["complete"] / 1113 + 0.05,
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
    gates == comparison["gates"]
    and all(gates.values()) == comparison["all_gates_passed"]
)
telemetry = read(ROOT.with_suffix(".telemetry.json"))
assert (
    telemetry["status"] == "completed"
    and telemetry["returncode"] == 0
    and telemetry["stop_reason"] is None
)
assert (
    not comparison["promoted"]
    and comparison["native_games"] == comparison["rl_updates"] == 0
)
for path, digest in contract["bindings"].items():
    assert sha(path) == digest
result = dict(
    status="verified_source_version_development_result",
    gates=gates,
    all_gates_passed=all(gates.values()),
    ordinary_predictions_verified=ordinary_count,
    own_history_predictions_verified=own_count,
    comparison_sha256=sha(ROOT / "comparison.json"),
    contract_sha256=sha(ROOT / "contract.json"),
    telemetry_sha256=sha(ROOT.with_suffix(".telemetry.json")),
    verifier_sha256=sha(__file__),
    refit=False,
    native_competence=False,
)
(ROOT / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result), flush=True)
