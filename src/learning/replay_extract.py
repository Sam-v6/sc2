"""Extract fog-safe Terran demonstrations with the matching installed engine."""

import argparse
import asyncio
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import mpyq
import s2protocol
from s2clientprotocol import sc2api_pb2 as pb, common_pb2 as common
from src.path import SC2_GAME_PATH
from src.runtime import supervise
from src.runner import positive
from src.learning.gameplay import protocol_dict, image_dict
from src.learning.demonstrations import ReplayExamples, label_timing


def load_protocol(build):
    # The upstream versions loader imports imp, removed in Python 3.12.
    # Load its unmodified, packaged build table through modern importlib instead.
    path = Path(s2protocol.__file__).parent / "versions" / f"protocol{int(build)}.py"
    if not path.is_file():
        raise FileNotFoundError(f"No official replay protocol for build {build}")
    spec = importlib.util.spec_from_file_location(f"sc2_replay_protocol_{build}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require_engine(game, base):
    executable = game / "Versions" / base / "SC2_x64"
    if not executable.is_file():
        raise FileNotFoundError(f"Replay requires unavailable engine {base}")
    return executable


def replay_metadata(path):
    archive = mpyq.MPQArchive(str(path))
    metadata = json.loads(archive.read_file("replay.gamemetadata.json"))
    base = int(metadata["BaseBuild"].removeprefix("Base"))
    protocol = load_protocol(base)
    header = protocol.decode_replay_header(
        archive.header["user_data_header"]["content"]
    )
    if header["m_version"]["m_baseBuild"] != base:
        raise ValueError("Replay metadata/header build mismatch")
    details_data = archive.read_file("replay.details") or archive.read_file(
        "replay.details.backup"
    )
    details = protocol.decode_replay_details(details_data)
    return metadata, details


def validate_replay_info(info, player):
    entries = [
        entry for entry in info.player_info if entry.player_info.player_id == player
    ]
    if len(entries) != 1:
        raise ValueError("Observed player is not in this replay")
    entry = entries[0]
    if (
        entry.player_info.type != pb.Participant
        or entry.player_info.race_actual != common.Terran
    ):
        raise ValueError("Teacher must be a human Terran participant")
    return {"teacher_kind": "human_unverified", "player": protocol_dict(entry)}


async def extract(job):
    from loguru import logger
    from sc2.sc2process import SC2Process

    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    replay = Path(job["replay"])
    metadata, details = replay_metadata(replay)
    require_engine(Path(SC2_GAME_PATH), metadata["BaseBuild"])
    output = Path(job["output"])
    output.mkdir(parents=True, exist_ok=False)
    raw_path = output / "raw-examples.jsonl.gz"
    rows_path = output / "examples.jsonl.gz"
    examples = ReplayExamples()
    rows = 0
    ended = False
    async with SC2Process(
        base_build=metadata["BaseBuild"], data_hash=metadata["DataVersion"]
    ) as server:
        response = await server._execute(
            replay_info=pb.RequestReplayInfo(replay_data=replay.read_bytes())
        )
        teacher = validate_replay_info(response.replay_info, job["player"])
        if response.replay_info.base_build != int(metadata["BaseBuild"][4:]):
            raise ValueError("Engine and metadata replay builds disagree")
        options = pb.InterfaceOptions(
            raw=True,
            score=True,
            raw_affects_selection=False,
            raw_crop_to_playable_area=False,
        )
        request = pb.RequestStartReplay(
            replay_data=replay.read_bytes(),
            observed_player_id=job["player"],
            options=options,
            disable_fog=False,
            realtime=False,
        )
        if job.get("map"):
            request.map_data = Path(job["map"]).read_bytes()
        start = await server._execute(start_replay=request)
        if start.start_replay.HasField("error"):
            raise RuntimeError(
                f"{pb.ResponseStartReplay.Error.Name(start.start_replay.error)}: "
                f"{start.start_replay.error_details}"
            )
        info = (await server._execute(game_info=pb.RequestGameInfo())).game_info
        data = (
            await server._execute(
                data=pb.RequestData(
                    ability_id=True,
                    unit_type_id=True,
                    upgrade_id=True,
                    buff_id=True,
                    effect_id=True,
                )
            )
        ).data
        static = {"game_info": protocol_dict(info), "game_data": protocol_dict(data)}
        # Preserve full-resolution terrain/pathing grids along with the protocol data.
        static["terrain"] = {
            name: image_dict(getattr(info.start_raw, name))
            for name in ("pathing_grid", "terrain_height", "placement_grid")
        }
        (output / "static.json").write_text(json.dumps(static) + "\n")
        with gzip.open(raw_path, "xt", encoding="utf-8") as stream:
            for _ in range(job["max_loops"] + 1):
                packet = (
                    await server._execute(observation=pb.RequestObservation())
                ).observation
                for row in examples.push(packet):
                    stream.write(json.dumps(row, separators=(",", ":")) + "\n")
                    rows += 1
                if packet.player_result:
                    ended = True
                    break
                if packet.observation.game_loop >= job["max_loops"]:
                    break
                await server._execute(step=pb.RequestStep(count=1))
        await server.quit()
    if not rows:
        raise ValueError("Replay extraction produced no gameplay examples")
    raw_rows, rows = rows, 0
    with gzip.open(raw_path, "rt") as source, gzip.open(rows_path, "xt") as target:
        for row in label_timing(json.loads(line) for line in source):
            target.write(json.dumps(row, separators=(",", ":")) + "\n")
            rows += 1
    receipt = {
        "status": "completed" if ended else "truncated",
        "schema": 2,
        "replay": str(replay),
        "sha256": hashlib.sha256(replay.read_bytes()).hexdigest(),
        "source": job["source"],
        "metadata": metadata,
        **teacher,
        "rows": rows,
        "raw_rows": raw_rows,
        "counts": dict(examples.counts),
        "last_loop": examples.last_loop,
        "alignment": "state_at_action_loop_minus_one",
        "disable_fog": False,
        "untranslated_gameplay": 0,
        "examples": str(rows_path),
        "cache_handles": [handle.hex() for handle in details["m_cacheHandles"]],
    }
    (output / "dataset.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def extract_job(job):
    return asyncio.run(extract(job))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--player", type=positive, default=1)
    parser.add_argument("--map-file", type=Path)
    parser.add_argument("--max-loops", type=positive, default=50000)
    parser.add_argument("--wall-seconds", type=positive, default=300)
    parser.add_argument(
        "--source", required=True, help="Source URL or provenance description"
    )
    args = parser.parse_args()
    metadata, _ = replay_metadata(args.replay)
    require_engine(Path(SC2_GAME_PATH), metadata["BaseBuild"])
    if args.output.exists():
        parser.error("Output already exists; choose a new dataset directory")
    job = {
        "replay": str(args.replay.resolve()),
        "output": str(args.output.resolve()),
        "map": str(args.map_file.resolve()) if args.map_file else None,
        "player": args.player,
        "max_loops": args.max_loops,
        "source": args.source,
    }
    receipt = supervise(extract_job, (job,), args.wall_seconds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".supervision.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    print(json.dumps(receipt), flush=True)
    if receipt["status"] not in ("completed", "truncated"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
