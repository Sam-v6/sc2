"""Read-only coverage audit of next human production labels in fitted replays."""

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
from statistics import median

from src.learning.production_targets import production_targets


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_game(directory):
    paths = [
        directory / name
        for name in ("static.json", "dataset.json", "examples.jsonl.gz")
    ]
    hashes = {str(path): sha(path) for path in paths}
    catalog = json.loads(paths[0].read_text())["game_data"]["abilities"]
    names = {a["ability_id"]: a.get("friendly_name", "") for a in catalog}
    abilities = {
        a
        for a, name in names.items()
        if name.startswith(("Build ", "Train ", "Research "))
    }
    receipt = json.loads(paths[1].read_text())
    for path in (paths[0], paths[2]):
        if hashes[str(path)] != receipt["corpus_bindings"][path.name]:
            raise ValueError("Changed corpus binding: " + str(path))
    unknowns = sorted(
        {
            (r["event"]["_gameloop"], r["event"]["m_sequence"])
            for r in receipt["issued_command_audit"]["unresolved_events"]
        }
    )
    with gzip.open(paths[2], "rt") as stream:
        rows = [json.loads(line) for line in stream]
    before = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    labels = production_targets(rows, abilities, unknowns)
    # Deliberately use a direct forward scan, independent of the labeler's bisect.
    end = intervening = 0
    for index, (row, actual) in enumerate(zip(rows, labels)):
        key = (row["action_loop"], row["source_sequence"])
        next_row = next(
            (r for r in rows[index:] if r["commands"][0]["ability"] in abilities), None
        )
        expected = None
        if next_row is None:
            end += 1
        else:
            target = (next_row["action_loop"], next_row["source_sequence"])
            if any(key < unknown < target for unknown in unknowns):
                intervening += 1
            else:
                expected = dict(
                    ability=next_row["commands"][0]["ability"],
                    delay_loops=target[0] - key[0],
                    target_key=list(target),
                )
        assert actual == expected, (directory.name, key, actual, expected)
    assert (
        before == hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    )
    assert hashes == {str(path): sha(path) for path in paths}
    immediate = Counter(
        r["commands"][0]["ability"]
        for r in rows
        if r["commands"][0]["ability"] in abilities
    )
    valid = [label for label in labels if label is not None]
    forecast = Counter(label["ability"] for label in valid)
    unique = {
        ability: len(
            {
                tuple(label["target_key"])
                for label in valid
                if label["ability"] == ability
            }
        )
        for ability in forecast
    }
    delays = sorted(label["delay_loops"] for label in valid)
    return dict(
        game=directory.name,
        source_sha256=hashes,
        rows=len(rows),
        unresolved_events=len(unknowns),
        immediate_production=sum(immediate.values()),
        forecast_labels=len(valid),
        censored_unknown=intervening,
        censored_end=end,
        verified_labels=len(labels),
        observations_unchanged=True,
        delay_seconds=dict(
            median=median(delays) / 22.4,
            p90=delays[int((len(delays) - 1) * 0.9)] / 22.4,
            maximum=delays[-1] / 22.4,
        ),
        classes={
            str(a): dict(
                name=names[a],
                immediate=immediate[a],
                forecast=forecast[a],
                unique_targets=unique[a],
                within_seconds={
                    str(s): sum(
                        label["ability"] == a and label["delay_loops"] <= s * 22.4
                        for label in valid
                    )
                    for s in (1, 5, 15, 30)
                },
            )
            for a in sorted(forecast)
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources = [
        Path(__file__),
        Path("src/learning/production_targets.py"),
        Path("docs/superpowers/plans/2026-10-06-production-forecast-coverage.md"),
    ]
    report = dict(
        kind="human_production_forecast_coverage",
        fitted_games_only=True,
        future_information_is_target_only=True,
        training=False,
        rl=False,
        taxonomy="friendly_name starts Build, Train or Research; incomplete macro taxonomy",
        source_sha256={str(p): sha(p) for p in sources},
        games=[
            audit_game(Path("logs/roadmap/pro-demonstrations-07") / game)
            for game in ("294", "870", "955", "839", "991", "523")
        ],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: sum(game[k] for game in report["games"])
                for k in (
                    "rows",
                    "immediate_production",
                    "forecast_labels",
                    "censored_unknown",
                    "censored_end",
                    "verified_labels",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
