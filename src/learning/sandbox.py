"""Supervised combat mini-games using the full-game raw command/entity schema."""

import argparse
import gzip
import json
from pathlib import Path
import sys

from src.runner import positive, validate_map
from src.runtime import supervise
from src.learning.gameplay import Command, PlayerView, protocol_dict
from src.learning.live import ability_catalog, ability_query, issue
from src.learning.micro_policy import MicroPolicy
from sc2.bot_ai import BotAI
from sc2.data import Race
from sc2.main import run_game
from sc2.player import Bot
from s2clientprotocol import sc2api_pb2 as pb


MAPS = ("DefeatRoaches", "DefeatZerglingsAndBanelings", "FindAndDefeatZerglings")


def attack_commands(state):
    enemies = [u for u in state["units"] if u["alliance"] == 4]
    commands = []
    if enemies:
        for unit in (u for u in state["units"] if u["alliance"] == 1):
            enemy = min(
                enemies,
                key=lambda e: sum(
                    (a - b) ** 2
                    for a, b in zip(e["position"][:2], unit["position"][:2])
                ),
            )
            commands.append(Command(23, (unit["tag"],), target_unit=enemy["tag"]))
    return commands


def micro_score(packet):
    score = packet.observation.score
    details = score.score_details
    return {
        "damage_dealt": float(
            details.total_damage_dealt.life + details.total_damage_dealt.shields
        ),
        "damage_taken": float(
            details.total_damage_taken.life + details.total_damage_taken.shields
        ),
        "killed_value": float(
            details.killed_value_units + details.killed_value_structures
        ),
        "score": score.score,
    }


class MicroSandbox(BotAI):
    def __init__(self, job, stream):
        super().__init__()
        self.job, self.stream = job, stream
        self.view = PlayerView()
        self.frames = self.commands = 0
        self.callback_error = None
        self.last_score = None
        self.action_results = {}
        self.policy = MicroPolicy.load(job["policy"]) if job.get("policy") else None

    async def on_start(self):
        self.client.game_step = self.job["step"]
        data = (
            await self.client._execute(
                data=pb.RequestData(ability_id=True, unit_type_id=True)
            )
        ).data
        (Path(self.job["output"]) / "abilities.json").write_text(
            json.dumps(ability_catalog(data)) + "\n"
        )

    async def on_step(self, iteration):
        try:
            packet = self.state.response_observation
            state = self.view.observe(packet)
            commands = (
                self.policy.commands(state) if self.policy else attack_commands(state)
            )
            tags = [u["tag"] for u in state["units"] if u["alliance"] == 1]
            available = (await self.client._execute(query=ability_query(tags))).query
            result = (
                await issue(self.client, commands) if commands else pb.ResponseAction()
            )
            self.view.record_commands(commands, state["game_loop"])
            for code in result.result:
                self.action_results[str(code)] = (
                    self.action_results.get(str(code), 0) + 1
                )
            self.last_score = micro_score(packet)
            self.stream.write(
                json.dumps(
                    {
                        "observation": state,
                        "available": [
                            protocol_dict(entry) for entry in available.abilities
                        ],
                        "commands": [command.as_dict() for command in commands],
                        "results": list(result.result),
                        "score": self.last_score,
                    },
                    separators=(",", ":"),
                )
                + "\n"
            )
            self.frames += 1
            self.commands += len(commands)
        except Exception as error:
            self.callback_error = repr(error)
            raise

    async def on_end(self, result):
        packet = (await self.client.observation()).observation
        self.last_score = micro_score(packet)
        self.final_game_loop = packet.observation.game_loop


def sandbox_job(job):
    from loguru import logger

    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    output = Path(job["output"])
    output.mkdir(parents=True, exist_ok=False)
    with gzip.open(output / "trace.jsonl.gz", "xt", encoding="utf-8") as stream:
        bot = MicroSandbox(job, stream)
        result = run_game(
            validate_map(job["map"]),
            [Bot(Race.Terran, bot)],
            realtime=False,
            random_seed=job["seed"],
            game_time_limit=job["seconds"],
            save_replay_as=str(output / "game.SC2Replay"),
        )
    if bot.callback_error or not bot.frames:
        raise RuntimeError(bot.callback_error or "Sandbox produced no frames")
    receipt = {
        "status": "truncated" if result.name == "Tie" else "completed",
        "sandbox_result": result.name,
        "map": job["map"],
        "seed": job["seed"],
        "controller": "linear_combat_candidates"
        if bot.policy
        else "scripted_nearest_target_baseline",
        "policy": job.get("policy"),
        "learned": bool(bot.policy),
        "frames": bot.frames,
        "commands": bot.commands,
        "action_results": bot.action_results,
        "game_seconds": bot.final_game_loop / 22.4,
        "step": job["step"],
        "score": bot.last_score,
        "ordinary_game_strength": False,
    }
    (output / "episode.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", choices=MAPS, default="DefeatRoaches")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--seed", type=int, default=1000)
    parser.add_argument("--seconds", type=positive, default=120)
    parser.add_argument("--step", type=positive, default=4)
    parser.add_argument("--wall-seconds", type=positive, default=120)
    args = parser.parse_args()
    validate_map(args.map)
    if args.policy:
        MicroPolicy.load(args.policy)
    if args.output.exists():
        parser.error("Output exists; choose a new episode directory")
    job = {
        "map": args.map,
        "output": str(args.output.resolve()),
        "seed": args.seed,
        "seconds": args.seconds,
        "step": args.step,
        "policy": str(args.policy.resolve()) if args.policy else None,
    }
    receipt = supervise(sandbox_job, (job,), args.wall_seconds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".supervision.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    print(json.dumps(receipt), flush=True)
    if receipt["status"] not in ("completed", "truncated"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
