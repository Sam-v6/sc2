"""Write partial professional human demonstrations from reconciled source files."""

import argparse
import base64
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import struct

import mpyq

from src.learning.gameplay import Command, PlayerView
from src.learning.replay_extract import load_protocol, replay_metadata
from src.learning.tournament_history import history_rows
from src.learning.tournament_observation import partial_observation
from src.learning.tournament_record import decode_record
from src.learning.tournament_targets import normalized_resource_target
from src.learning.tournament_tracker import CausalTracker


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_bindings(receipt):
    for path, expected in receipt["bindings"].items():
        if digest(path) != expected:
            raise ValueError("Changed source binding: " + path)


def replay_user_id(details, init, player):
    """Resolve gameplay user IDs through player working slots, past observers."""
    if not 1 <= player <= len(details["m_playerList"]):
        raise ValueError("Invalid replay player")
    working_slot = details["m_playerList"][player - 1]["m_workingSetSlotId"]
    slots = init["m_syncLobbyState"]["m_lobbyState"]["m_slots"]
    matches = [s for s in slots if s["m_workingSetSlotId"] == working_slot]
    if len(matches) != 1 or matches[0]["m_userId"] is None:
        raise ValueError("Require a unique assigned gameplay user identity")
    return matches[0]["m_userId"]


def verify_owned_identity(tracker, tag, loop, boundary_owners):
    """Reject positively foreign Self tags; unknown ownership stays unknown."""
    owners = set(boundary_owners.get((loop, tag), set()))
    owner = tracker.owners.get(tag)
    if owner is not None:
        owners.add(owner)
    if owners and tracker.player not in owners:
        raise ValueError("Source Self unit has a known foreign tracker owner")


def import_game(job):
    paths = {
        name: Path(job[name])
        for name in ("record", "replay", "map", "catalog", "reconciliation", "phase")
    }
    reconciled = json.loads(paths["reconciliation"].read_text())
    check_bindings(reconciled)
    game = next(g for g in reconciled["games"] if g["idx"] == job["record_index"])
    check_bindings(game)
    action_path = next(
        Path(p)
        for p in game["bindings"]
        if Path(p).name == f"fall-actions-{job['record_index']}.json"
    )
    if json.loads(action_path.read_text())["record_sha256"] != digest(paths["record"]):
        raise ValueError("Record differs from the reconciled converted action source")
    for name in ("replay", "catalog"):
        if digest(paths[name]) not in game["bindings"].values():
            raise ValueError("Input differs from the reconciled " + name)
    phase = json.loads(paths["phase"].read_text())
    check_bindings(phase)
    if phase["status"] != "verified_native_phase_and_converter_buffer_contract":
        raise ValueError("Require verified issue-loop pre-effect contract")
    record = decode_record(paths["record"].read_bytes())
    metadata, details = replay_metadata(paths["replay"])
    protocol = load_protocol(int(metadata["BaseBuild"].removeprefix("Base")))
    archive = mpyq.MPQArchive(str(paths["replay"]))
    map_hash = details["m_cacheHandles"][-1][-32:].hex()
    if digest(paths["map"]) != map_hash:
        raise ValueError("Require the exact original replay map")
    map_info = mpyq.MPQArchive(str(paths["map"])).read_file("MapInfo")
    size = list(struct.unpack_from("<II", map_info, 16))
    player = record["header"]["player"]
    init = protocol.decode_replay_initdata(archive.read_file("replay.initData"))
    user_id = replay_user_id(details, init, player)
    if (
        record["header"]["race"] != 0
        or game.get("source_player_id", 1) != player
        or game.get("source_user_id", 0) != user_id
    ):
        raise ValueError("Require the reconciled human Terran player/user identity")
    static = json.loads(paths["catalog"].read_text())
    catalog = static["game_data"]
    tracker_events = list(
        protocol.decode_replay_tracker_events(
            archive.read_file("replay.tracker.events")
        )
    )
    tracker = CausalTracker(tracker_events, player, catalog)
    boundary_owners = defaultdict(set)
    for event in tracker_events:
        if event["_event"].rsplit(".", 1)[-1] in (
            "SUnitBornEvent",
            "SUnitInitEvent",
            "SUnitOwnerChangeEvent",
        ):
            tag = (event["m_unitTagIndex"] << 18) | event["m_unitTagRecycle"]
            boundary_owners[(event["_gameloop"], tag)].add(event["m_upkeepPlayerId"])
    native_names = {u["name"]: u["unit_id"] for u in catalog["units"]}
    boundary_types = {
        (
            e["_gameloop"],
            (e["m_unitTagIndex"] << 18) | e["m_unitTagRecycle"],
        ): native_names.get(e["m_unitTypeName"].decode())
        for e in tracker_events
        if e["_event"].endswith(".SUnitTypeChangeEvent")
    }
    resource_types = {
        u["unit_id"]
        for u in catalog["units"]
        if u.get("has_minerals") or u.get("has_vespene")
    }
    events = list(
        protocol.decode_replay_game_events(archive.read_file("replay.game.events"))
    )
    events = [
        e
        for e in events
        if e["_event"].endswith(".SCmdEvent") and e["_userid"]["m_userId"] == user_id
    ]
    event_by_key = {(e["_gameloop"], e["m_sequence"]): e for e in events}
    accepted = []
    for item in game["accepted"]:
        raw = item["command"]
        accepted.append(
            dict(
                item,
                command=Command(
                    **dict(
                        raw,
                        units=tuple(raw["units"]),
                        target_point=tuple(raw["target_point"])
                        if raw.get("target_point") is not None
                        else None,
                    )
                ),
            )
        )
    translations = {
        (t['loop'], t['sequence']): t['proof']
        for t in game.get('label_translations', [])
    }
    rows = defaultdict(list)
    for row in history_rows(events, accepted):
        rows[row["loop"]].append(row)
    output = Path(job["output"])
    output.mkdir(parents=True, exist_ok=False)
    # Terrain height lacks independent original-map validation; mask it explicitly.
    static = dict(
        game_data=catalog,
        game_info=dict(start_raw=dict(map_size=dict(x=size[0], y=size[1]))),
        terrain={"terrain_height": {"known": False}},
    )
    (output / "static.json").write_text(json.dumps(static) + "\n")
    view = PlayerView()
    mappings = []
    mapping_cache = {}
    written = 0
    type_checks = 0
    with gzip.open(output / "examples.jsonl.gz", "xt") as stream:
        for step, loop in enumerate(record["steps"]["game_loop"]):
            loop = int(loop)
            dead = tracker.advance(loop)
            own_deaths = [tag for tag in view.owned if tag & 0xFFFFFFFF in dead]
            state = partial_observation(
                record, step, size, view, sorted(tracker.upgrades), own_deaths
            )
            if tracker.unmapped_upgrades:
                state["unknown_fields"]["world"].append("upgrade_absence")
                state["unmapped_own_upgrades"] = sorted(tracker.unmapped_upgrades)
            for unit in state["units"]:
                if unit["alliance"] == 1:
                    verify_owned_identity(
                        tracker, unit["tag"] & 0xFFFFFFFF, loop, boundary_owners
                    )
                expected = tracker.own_types.get(unit["tag"] & 0xFFFFFFFF)
                if unit["alliance"] == 1 and expected is not None:
                    # A tracker change at L may precede or follow the source's
                    # observation phase. Use it only to verify the ID vocabulary;
                    # learned features always retain the observed source type.
                    boundary = boundary_types.get((loop, unit["tag"] & 0xFFFFFFFF))
                    if unit["unit_type"] not in (expected, boundary):
                        raise ValueError(
                            f"Own tracker/native unit type disagreement: loop {loop}, "
                            f"tag {unit['tag']}, observed {unit['unit_type']}, tracker {expected}"
                        )
                    type_checks += 1
            for source, target in (
                ("pathable", "pathing_grid"),
                ("buildable", "placement_grid"),
            ):
                grid = record["images"][source][step]
                state["map"][target] = dict(
                    width=grid.shape[1],
                    height=grid.shape[0],
                    bits_per_pixel=8,
                    data=base64.b64encode(grid.astype("uint8").tobytes()).decode(),
                    coordinate_system="feature_minimap",
                    world_size=size,
                    transform="world_y_flip_then_uniform_max_dimension_scale",
                )
            for row in rows.get(loop, []):
                command = row["command"]
                event = event_by_key[(loop, row["sequence"])]
                original_type = tracker.neutral_types.get(
                    (command.target_unit or 0) & 0xFFFFFFFF
                )
                translated, mapping = normalized_resource_target(
                    command, event, state, original_type, resource_types
                )
                history = [
                    dict(
                        c,
                        target_unit=mapping_cache.get(
                            c.get("target_unit"), c.get("target_unit")
                        ),
                    )
                    if not c.get("unknown")
                    else dict(c)
                    for c in row["recent_commands"]
                ]
                if mapping:
                    mapping_cache[mapping["original_tag"]] = mapping["source_tag"]
                    mappings.append(dict(mapping, loop=loop, sequence=row["sequence"]))
                candidate = dict(
                    state, history_quality="event_slots", recent_commands=history
                )
                example = dict(
                    action_loop=loop,
                    source_sequence=row["sequence"],
                    observation=candidate,
                    commands=[translated.as_dict()],
                    original_command=command.as_dict(),
                    next_action_delay=row["next_action_delay"],
                )
                translation = translations.get((loop, row['sequence']))
                if translation is not None:
                    example['label_translation'] = translation
                stream.write(json.dumps(example) + "\n")
                written += 1
    if written != len(accepted):
        raise ValueError("Missing verified original issue-loop observations")
    receipt = dict(
        status="completed",
        sha256=digest(paths["replay"]),
        disable_fog=False,
        alignment="state_at_issue_loop_before_effect",
        teacher_kind="human_professional_partial",
        player={"player_info": {"race_actual": 1, "player_id": player}},
        source_user_id=user_id,
        requires_missing_fields=True,
        training_eligible=True,
        source_phase_proof=str(paths["phase"]),
        source_replay=str(paths["replay"]),
        professional_engine_reconstruction=False,
        issued_command_audit=game["audit"],
        source_resource_mappings=mappings,
        own_type_checks=type_checks,
        unmapped_tracker_upgrades=sorted(tracker.unmapped_upgrades),
        source_bindings={str(p): digest(p) for p in paths.values()},
        code_bindings={
            str(p): digest(p)
            for p in (
                Path(__file__),
                *[
                    Path(__file__).with_name(name + ".py")
                    for name in (
                        "tournament_record",
                        "tournament_observation",
                        "tournament_tracker",
                        "tournament_targets",
                        "tournament_history",
                        "tournament_commands",
                        "gameplay",
                    )
                ],
            )
        },
        corpus_bindings={
            name: digest(output / name) for name in ("static.json", "examples.jsonl.gz")
        },
    )
    if translations:
        receipt['label_translations'] = game['label_translations']
    (output / "dataset.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path)
    job = json.loads(parser.parse_args().job.read_text())
    print(json.dumps(import_game(job), indent=2))


if __name__ == "__main__":
    main()
