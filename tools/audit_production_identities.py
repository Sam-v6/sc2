"""Audit missing human production identities without modifying the corpus."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import sc2reader

from src.learning.production_identity import producer_ability
from src.learning.tournament_commands import reconcile_commands


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(bindings):
    for path, expected in bindings.items():
        if digest(path) != expected:
            raise ValueError("Changed binding: " + path)


def serialized(rows):
    return json.loads(
        json.dumps([dict(r, command=r["command"].as_dict()) for r in rows])
    )


def audit_game(game):
    root = Path("logs/roadmap/pro-demonstrations-07") / game
    receipt_path = root / "dataset.json"
    receipt = json.loads(receipt_path.read_text())
    reconciliation = next(
        p for p in receipt["source_bindings"] if "command-reconciliation" in p
    )
    verify({reconciliation: receipt["source_bindings"][reconciliation]})
    old = next(
        g
        for g in json.loads(Path(reconciliation).read_text())["games"]
        if str(g["idx"]) == game
    )
    verify(old["bindings"])
    paths = old["bindings"]
    events = json.loads(
        Path(
            next(p for p in paths if Path(p).name == f"raw-commands-{game}.json")
        ).read_text()
    )
    observations = json.loads(
        Path(
            next(p for p in paths if Path(p).name == f"fall-actions-{game}.json")
        ).read_text()
    )["actions"]
    catalog_path = next(p for p in paths if Path(p).name == "static.json")
    catalog = json.loads(Path(catalog_path).read_text())["game_data"]
    abilities = {a["ability_id"]: a for a in catalog["abilities"]}
    names = {(r["link"], r["index"]): r["name"] for r in old["replay_names"]}
    selections = {(r["loop"], r["sequence"]): r["tags"] for r in old["selections"]}
    baseline, baseline_audit = reconcile_commands(
        events, observations, selections, abilities, names
    )
    assert serialized(baseline) == old["accepted"], (
        "Original reconciliation no longer reproduces"
    )
    assert baseline_audit == old["audit"]
    reader = sc2reader.load_replay(
        receipt["source_replay"], load_level=2, load_map=False
    )
    event_keys = {(e["_gameloop"], e["m_sequence"]): e for e in events}
    old_keys = {(r["loop"], r["sequence"]): r["command"].ability for r in baseline}
    mappings, rejects = {}, Counter()
    for event in events:
        raw = event["m_abil"]
        if raw is None:
            continue
        key = (raw["m_abilLink"], raw["m_abilCmdIndex"])
        metadata = reader.datapack.abilities.get((key[0] << 5) | key[1])
        if metadata is None or metadata.build_unit is None:
            rejects["missing_producer_metadata"] += 1
            continue
        candidate = producer_ability(metadata.build_unit.name, key[1], catalog)
        if candidate is None:
            rejects["nonunique_name_missing_ability_or_index_conflict"] += 1
            continue
        mappings[key] = dict(
            link=key[0],
            index=key[1],
            replay_name=metadata.name,
            producer_unit=metadata.build_unit.name,
            raw_ability=candidate,
            native_name=abilities[candidate]["friendly_name"],
        )
    # Reject a whole mapping if it contradicts any independently retained command.
    conflicts = set()
    for key, raw_ability in old_keys.items():
        raw = event_keys[key]["m_abil"]
        ability_key = (raw["m_abilLink"], raw["m_abilCmdIndex"]) if raw else None
        if (
            ability_key in mappings
            and mappings[ability_key]["raw_ability"] != raw_ability
        ):
            conflicts.add(ability_key)
    revised_names = dict(names)
    for key, mapping in mappings.items():
        if key not in conflicts:
            revised_names[key] = mapping["native_name"]
    accepted, audit = reconcile_commands(
        events, observations, selections, abilities, revised_names
    )
    new_keys = {(r["loop"], r["sequence"]) for r in accepted}
    assert set(old_keys) <= new_keys, "Metadata test lost previously retained commands"
    assert (
        serialized([r for r in accepted if (r["loop"], r["sequence"]) in old_keys])
        == old["accepted"]
    ), "Metadata test changed retained commands"
    fresh = [r for r in accepted if (r["loop"], r["sequence"]) not in old_keys]
    samples = {}
    for row in fresh:
        event = event_keys[row["loop"], row["sequence"]]
        raw = event["m_abil"]
        mapping = mappings[raw["m_abilLink"], raw["m_abilCmdIndex"]]
        i, j = row["converted_position"]
        action = observations[i]["actions"][j]
        selected = selections[row["loop"], row["sequence"]]
        # Separate source-level checks for one inspectable example per family.
        assert observations[i]["loop"] == event["_gameloop"]
        assert action["ability"] == mapping["raw_ability"]
        assert {tag & 0xFFFFFFFF for tag in action["tags"]} <= set(selected)
        assert event["m_cmdFlags"] & 0x100 and not event["m_cmdFlags"] & ~(
            0x100 | 2 | 8 | 0x10000 | 0x20000
        )
        samples.setdefault(
            str(action["ability"]),
            dict(
                mapping=mapping,
                event=event,
                selection=selected,
                converted_action=action,
                accepted_command=row["command"].as_dict(),
            ),
        )
    bindings = dict(
        paths,
        **{
            str(receipt_path): digest(receipt_path),
            reconciliation: digest(reconciliation),
        },
    )
    verify(bindings)
    return dict(
        game=game,
        idx=int(game),
        source_player_id=old.get("source_player_id", 1),
        source_user_id=old.get("source_user_id", 0),
        reader_datapack=reader.datapack.id,
        bindings=bindings,
        baseline_commands=len(baseline),
        candidate_commands=len(accepted),
        recovered_commands=len(fresh),
        conflicts=[list(k) for k in sorted(conflicts)],
        metadata_rejections=dict(rejects),
        mappings=list(mappings.values()),
        recovered_by_ability=dict(
            Counter(abilities[r["command"].ability]["friendly_name"] for r in fresh)
        ),
        samples=samples,
        unresolved_reasons=dict(
            Counter(r["reason"] for r in audit["unresolved_events"])
        ),
        accepted=serialized(accepted),
        audit=audit,
        selections=old["selections"],
        replay_names=old["replay_names"],
        verified_candidate_names=[
            dict(link=k[0], index=k[1], name=v) for k, v in revised_names.items()
        ],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    code = [
        Path(__file__),
        Path("src/learning/production_identity.py"),
        Path("src/learning/tournament_commands.py"),
        Path("docs/superpowers/plans/2026-10-06-production-identity-audit.md"),
    ]
    reader_root = Path(sc2reader.__file__).parent
    code.extend(
        p
        for p in reader_root.rglob("*")
        if p.is_file() and p.suffix in (".py", ".csv", ".json")
    )
    bindings = {str(p): digest(p) for p in code}
    games = [audit_game(g) for g in ("294", "870", "955", "839", "991", "523")]
    verify(bindings)
    report = dict(
        kind="human_production_identity_audit",
        bindings=bindings,
        games=games,
        training_eligible=False,
        corpus_modified=False,
        training=False,
        rl=False,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            [
                dict(
                    game=g["game"],
                    baseline=g["baseline_commands"],
                    recovered=g["recovered_commands"],
                    conflicts=g["conflicts"],
                    families=g["recovered_by_ability"],
                )
                for g in games
            ]
        )
    )


if __name__ == "__main__":
    main()
