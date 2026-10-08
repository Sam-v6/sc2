"""Unfitted Attack destination persistence; run from the worktree root."""
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics

ROOT = Path("logs/roadmap")
GAMES = ["51574", "51573", "51958", "51890", "51891", "51957-p1",
         "50925", "51960-p1", "51959-held-01"]
OUTPUT = ROOT / "attack-history-persistence-01.json"
COMPARISON = ROOT / "attack-listwise-corpus-01/report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    files = [Path(__file__), COMPARISON]
    for game in GAMES:
        files.extend(ROOT / ("issued-" + game) / name
                     for name in ("dataset.json", "examples.jsonl.gz"))
    before = {str(p.resolve()): sha(p) for p in files}
    comparison = json.loads(COMPARISON.read_text())
    games = []
    for game in GAMES:
        directory = ROOT / ("issued-" + game)
        receipt = json.loads((directory / "dataset.json").read_text())
        assert receipt["status"] == "completed" and not receipt["disable_fog"]
        with gzip.open(directory / "examples.jsonl.gz", "rt") as stream:
            rows = list(map(json.loads, stream))
        loops = [r["action_loop"] for r in rows]
        assert loops == sorted(loops)
        history, predictions = [], []
        # Every command sharing the current loop is excluded, regardless of row
        # order. No assumption about ordering within a simultaneous burst.
        for loop, items in itertools.groupby(enumerate(rows), lambda item: item[1]["action_loop"]):
            current = []
            for row_index, row in items:
                assert row["observation"]["game_loop"] < loop
                for command_index, command in enumerate(row["commands"]):
                    if command["ability"] != 23 or command["target_point"] is None:
                        continue
                    record = dict(loop=loop, row_index=row_index,
                                  command_index=command_index, units=command["units"],
                                  teacher_point=command["target_point"])
                    tags = set(command["units"])
                    previous = next((h for h in reversed(history)
                                     if tags.intersection(h["units"])), None)
                    if previous is None:
                        prediction = dict(record, category="first", previous=None,
                                          error_tiles=None, age_seconds=None)
                    else:
                        assert previous["loop"] < loop
                        error = math.dist(command["target_point"], previous["teacher_point"])
                        prediction = dict(record, category="same" if error <= 2 else "changed",
                                          previous=previous.copy(), error_tiles=error,
                                          age_seconds=(loop - previous["loop"]) / 22.4)
                    predictions.append(prediction)
                    current.append(record)
            history.extend(current)
        errors = [p["error_tiles"] for p in predictions if p["previous"] is not None]
        ages = [p["age_seconds"] for p in predictions if p["previous"] is not None]
        counts = {k: sum(p["category"] == k for p in predictions)
                  for k in ("same", "changed", "first")}
        assert sum(counts.values()) == len(predictions)
        held = next((d for d in comparison["diagnostics"]
                     if Path(d["dataset"]).name == directory.name), None)
        games.append(dict(
            dataset=str(directory), replay_sha256=receipt["sha256"],
            split="teaching" if game in GAMES[:6] else "reused_diagnostic",
            commands=len(predictions), counts=counts, covered=len(errors),
            within_2_tiles=counts["same"],
            within_2_all_commands=counts["same"] / len(predictions),
            mean_error_covered=statistics.mean(errors) if errors else None,
            median_age_seconds=statistics.median(ages) if ages else None,
            listwise_comparison=held["new"] if held else None,
            predictions=predictions))
    after = {str(p.resolve()): sha(p) for p in files}
    assert before == after
    report = dict(
        status="completed", algorithm="unfitted_previous_overlapping_group_attack_destination",
        history="Latest earlier-loop Attack point command sharing at least one actor tag; unbounded past within the same replay. Within a prior-loop burst, final recorded command wins ties.",
        ordering="Strict previous action_loop < current action_loop; same-loop commands excluded across all rows; observations strictly precede commands.",
        categories="same: previous target within 2 tiles inclusive; changed: farther than 2 tiles; first: no earlier overlapping-group Attack point. First commands have no prediction and count as misses in all-command accuracy.",
        limitations="Oracle human ability, point mode and selected actors. Teacher-forced past human commands, not autonomous history. Diagnostic games reused; no fitting, live skill, RL or professional claim. Earlier exploratory calculation appended commands within each row; this artifact uses stricter prior-loop history.",
        files_before=before, files_after=after, games=games)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps([dict(game=g["dataset"], commands=g["commands"], **g["counts"],
                           mean_error_covered=g["mean_error_covered"],
                           median_age_seconds=g["median_age_seconds"])
                      for g in games], indent=2))


if __name__ == "__main__":
    main()
