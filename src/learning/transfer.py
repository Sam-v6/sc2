"""Isolate learned Marine combat changes while holding the old macro model fixed."""

import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import sys
from sc2.data import Race, Difficulty, AIBuild
from sc2.main import run_game
from sc2.player import Bot, Computer
from src.learning.gameplay import PlayerView
from src.learning.live import issue
from src.learning.micro_policy import MicroPolicy, combat_view
from src.rl.policy import load_policy
from src.rl.terran import TerranLearner, FEATURES, ACTIONS
from src.runner import positive, validate_map
from src.runtime import supervise


class MicroTransfer(TerranLearner):
    def __init__(self, *args, micro_policy, **kwargs):
        super().__init__(*args, **kwargs)
        self.micro_policy = micro_policy
        self.micro_view = PlayerView()
        self.owned_tags = set()
        self.micro_frames = self.micro_commands = 0
        self.micro_results = {}

    def army_units(self):
        # Exclusion exists only while the inherited combat executor runs.
        return super().army_units().filter(lambda unit: unit.tag not in self.owned_tags)

    async def micro(self):
        state = combat_view(self.micro_view.observe(self.state.response_observation))
        self.owned_tags = {
            unit["tag"] for unit in state["units"] if unit["alliance"] == 1
        }
        try:
            await super().micro()
        finally:
            self.owned_tags = set()
        commands = self.micro_policy.commands(state)
        if commands:
            result = await issue(self.client, commands)
            self.micro_view.record_commands(commands, state["game_loop"])
            self.micro_frames += 1
            self.micro_commands += len(commands)
            for code in result.result:
                self.micro_results[str(code)] = self.micro_results.get(str(code), 0) + 1


def transfer_job(job):
    from loguru import logger

    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    output = Path(job["output"])
    output.mkdir(parents=True, exist_ok=False)
    policy = load_policy(job["macro"], FEATURES, ACTIONS)
    kwargs = {
        "training": False,
        "action_log": output / "macro.jsonl",
        "macro_seconds": policy.macro_seconds,
        "game_seconds": job["seconds"],
    }
    if job["micro"]:
        bot = MicroTransfer(
            policy, micro_policy=MicroPolicy.load(job["micro"]), **kwargs
        )
    else:
        bot = TerranLearner(policy, **kwargs)
    result = run_game(
        validate_map(job["map"]),
        [
            Bot(Race.Terran, bot),
            Computer(
                Race[job["race"]], Difficulty[job["difficulty"]], AIBuild[job["build"]]
            ),
        ],
        realtime=False,
        random_seed=job["seed"],
        game_time_limit=job["seconds"],
        save_replay_as=str(output / "game.SC2Replay"),
    )
    if bot.callback_error or not bot.started:
        raise RuntimeError(bot.callback_error or "Bot did not start")
    receipt = {
        "status": "truncated" if result.name == "Tie" else "completed",
        "result": result.name,
        "seed": job["seed"],
        "race": job["race"],
        "difficulty": job["difficulty"],
        "build": job["build"],
        "map": job["map"],
        "macro": job["macro"],
        "micro": job["micro"],
        "game_seconds": bot.time,
        "combat": bot.combat_score(),
        "micro_frames": getattr(bot, "micro_frames", 0),
        "micro_commands": getattr(bot, "micro_commands", 0),
        "micro_results": getattr(bot, "micro_results", {}),
        "attribution": "frozen narrow learned macro; Marine-only learned combat if supplied; remaining execution scripted",
    }
    (output / "episode.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def evaluate(job):
    return supervise(transfer_job, (job,), job.pop("wall_seconds"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--macro", type=Path, required=True)
    parser.add_argument("--micro", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--map", default="Simple64")
    parser.add_argument(
        "--difficulty",
        choices=["Easy", "Medium", "Hard", "Harder", "VeryHard", "Elite"],
        default="Hard",
    )
    parser.add_argument(
        "--build",
        choices=["RandomBuild", "Rush", "Timing", "Power", "Macro", "Air"],
        default="RandomBuild",
    )
    parser.add_argument("--seed", type=int, default=99000)
    parser.add_argument("--seconds", type=positive, default=1200)
    parser.add_argument("--wall-seconds", type=positive, default=300)
    parser.add_argument("--workers", type=positive, default=3)
    args = parser.parse_args()
    validate_map(args.map)
    MicroPolicy.load(args.micro)
    args.output.mkdir(parents=True, exist_ok=False)
    hashes = {
        str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (args.macro, args.micro)
    }
    jobs = []
    for index, race in enumerate(("Terran", "Protoss", "Zerg")):
        for label, micro in [
            ("baseline", None),
            ("learned", str(args.micro.resolve())),
        ]:
            jobs.append(
                {
                    "macro": str(args.macro.resolve()),
                    "micro": micro,
                    "race": race,
                    "difficulty": args.difficulty,
                    "build": args.build,
                    "map": args.map,
                    "seed": args.seed + index,
                    "seconds": args.seconds,
                    "wall_seconds": args.wall_seconds,
                    "output": str((args.output / f"{race}-{label}").resolve()),
                }
            )
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        receipts = list(pool.map(evaluate, jobs))
    if any(
        hashlib.sha256(Path(path).read_bytes()).hexdigest() != before
        for path, before in hashes.items()
    ):
        raise RuntimeError("Frozen checkpoint changed during evaluation")
    panel = {
        "schema": 1,
        "status": "completed",
        "frozen_checkpoints": hashes,
        "episodes": receipts,
        "purpose": "bounded three-race micro-transfer development probe; not Hard acceptance",
    }
    (args.output / "panel.json").write_text(json.dumps(panel, indent=2) + "\n")
    print(json.dumps(panel), flush=True)
    if any(r["status"] not in ("completed", "truncated") for r in receipts):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
