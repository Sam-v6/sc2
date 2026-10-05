"""Execute the factorized imitation model through broad raw gameplay controls."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from sc2.bot_ai import BotAI
from sc2.data import Race, Difficulty, AIBuild
from sc2.main import run_game
from sc2.player import Bot, Computer
from s2clientprotocol import sc2api_pb2 as pb
from src.learning.gameplay import Command, PlayerView
from src.learning.imitation import FactorPolicy, unit_features, DELAYS
from src.learning.global_imitation import (
    global_features,
    select_group,
    coordinate_signs,
)
from src.learning.live import ability_query, issue
from src.learning.sandbox import micro_score
from src.runner import positive, validate_map
from src.runtime import supervise


def decode_commands(state, actors, output, available, catalog, unit_types, map_size):
    lookup = {kind: index + 1 for index, kind in enumerate(unit_types)}
    commands = []
    rows = []
    for index, actor in enumerate(actors):
        legal = [
            0,
            *sorted(
                a
                for a in available.get(actor["tag"], set())
                if 0 < a < output["ability"].shape[1]
            ),
        ]
        ability = legal[int(np.argmax(output["ability"][index, legal]))]
        row = {
            "unit": actor["tag"],
            "raw_ability": int(output["ability"][index].argmax()),
            "ability": ability,
            "delay": int(DELAYS[output["delay"][index].argmax()]),
        }
        rows.append(row)
        if not ability:
            continue
        descriptor = catalog[ability]
        target_rule = descriptor.get("target", 1)
        modes = (
            [0]
            if target_rule in (0, 1)
            else [1]
            if target_rule == 2
            else [2]
            if target_rule == 3
            else [1, 2]
            if target_rule == 4
            else [0, 1]
        )
        if descriptor.get("allow_autocast"):
            modes.append(3)
        mode = modes[int(np.argmax(output["mode"][index, modes]))]
        queue = bool(output["queue"][index].argmax()) if mode != 3 else False
        desired = np.asarray(actor["position"][:2]) + 128 * output["point"][index]
        point = (
            tuple(np.clip(desired, [0.0, 0.0], np.asarray(map_size) - 0.01))
            if mode == 1
            else None
        )
        target = None
        if mode == 2:
            if not state["units"]:
                row["rejected"] = "no_current_target"
                continue

            def score(unit):
                type_index = lookup.get(unit["unit_type"], 0)
                distance = (
                    np.linalg.norm(np.asarray(unit["position"][:2]) - desired) / 128
                )
                return (
                    output["target_type"][index, type_index]
                    + output["alliance"][index, unit["alliance"]]
                    - 5 * distance
                )

            target = max(state["units"], key=score)["tag"]
        command = Command(
            ability,
            (actor["tag"],),
            target_unit=target,
            target_point=point,
            queue=queue,
            autocast=mode == 3,
        )
        commands.append(command)
        row["command"] = command.as_dict()
    return commands, rows


def idle_worker_harvest(state, selected):
    minerals = [
        u
        for u in state["units"]
        if u["alliance"] == 3 and u.get("mineral_contents", 0) > 0
    ]
    commands = []
    if not minerals:
        return commands
    for unit in state["units"]:
        if (
            unit["alliance"] != 1
            or unit["unit_type"] != 45
            or unit["tag"] in selected
            or unit.get("orders")
        ):
            continue
        target = min(
            minerals,
            key=lambda m: np.linalg.norm(
                np.asarray(m["position"][:2]) - unit["position"][:2]
            ),
        )
        commands.append(Command(295, (unit["tag"],), target_unit=target["tag"]))
    return commands


class ImitationBot(BotAI):
    def __init__(self, job, stream):
        super().__init__()
        self.job = job
        self.stream = stream
        self.policy = FactorPolicy.load(job["policy"])
        self.view = PlayerView()
        self.next_action = {}
        self.next_global = 0
        self.worker_assistance_commands = 0
        self.frames = self.commands = 0
        self.results = {}
        self.callback_error = None
        self.final_score = None

    async def on_start(self):
        self.client.game_step = self.job["step"]
        data = (await self.client._execute(data=pb.RequestData(ability_id=True))).data
        self.catalog = {
            a.ability_id: {"target": a.target, "allow_autocast": a.allow_autocast}
            for a in data.abilities
        }
        if max(self.catalog) + 1 != self.policy.sizes["ability"]:
            raise ValueError("Model/engine ability schema mismatch")
        # Explicit execution assistance; no build order.
        if self.job["initial_harvest"]:
            for worker in self.workers:
                worker.gather(self.mineral_field.closest_to(worker))

    async def on_step(self, iteration):
        try:
            packet = self.state.response_observation
            state = self.view.observe(packet)
            state["map_size"] = [self.game_info.map_size.x, self.game_info.map_size.y]
            actors = [
                u
                for u in state["units"] + state["owned_memory"]
                if u["alliance"] == 1
                and state["game_loop"] >= self.next_action.get(u["tag"], 0)
            ]
            global_decision = "actor_type" in self.policy.sizes
            if global_decision and state["game_loop"] < self.next_global:
                actors = []
            commands = []
            decisions = []
            if actors:
                available = (
                    await self.client._execute(
                        query=ability_query([u["tag"] for u in actors])
                    )
                ).query
                abilities = {
                    entry.unit_tag: {a.ability_id for a in entry.abilities}
                    for entry in available.abilities
                }
                if global_decision:
                    canonical = (
                        self.policy.evidence.get("coordinate_frame")
                        == "base_toward_map_center"
                    )
                    x, origin = global_features(
                        state,
                        self.policy.unit_types,
                        self.policy.sizes["ability"],
                        canonical=canonical,
                    )
                    output = self.policy.predict(x[None, :])
                    allowed = [0, *sorted(set().union(*abilities.values()))]
                    ability = allowed[int(np.argmax(output["ability"][0, allowed]))]
                    output = self.policy.predict(x[None, :], abilities=[ability])
                    if canonical:
                        signs = coordinate_signs(state, origin)
                        output["point"][:, :2] *= signs
                        output["point"][:, 2:4] *= signs
                    group = (
                        select_group(
                            state,
                            output,
                            abilities,
                            ability,
                            self.policy.unit_types,
                            origin,
                        )
                        if ability
                        else []
                    )
                    if group:
                        proxy = dict(group[0], position=[*origin, 0.0])
                        output["point"] = output["point"][:, :2]
                        commands, decisions = decode_commands(
                            state,
                            [proxy],
                            output,
                            {proxy["tag"]: {ability}},
                            self.catalog,
                            self.policy.unit_types,
                            (self.game_info.map_size.x, self.game_info.map_size.y),
                        )
                        commands = [
                            Command(
                                c.ability,
                                tuple(u["tag"] for u in group),
                                c.target_unit,
                                c.target_point,
                                c.queue,
                                c.autocast,
                            )
                            for c in commands
                        ]
                        for row, command in zip(decisions, commands):
                            row["command"] = command.as_dict()
                        self.next_global = state["game_loop"] + int(
                            DELAYS[output["delay"][0].argmax()]
                        )
                else:
                    x = np.stack(
                        [
                            unit_features(state, u, self.policy.unit_types)
                            for u in actors
                        ]
                    )
                    output = self.policy.predict(x)
                    commands, decisions = decode_commands(
                        state,
                        actors,
                        output,
                        abilities,
                        self.catalog,
                        self.policy.unit_types,
                        (self.game_info.map_size.x, self.game_info.map_size.y),
                    )
                result = (
                    await issue(self.client, commands)
                    if commands
                    else pb.ResponseAction()
                )
                for code in result.result:
                    self.results[str(code)] = self.results.get(str(code), 0) + 1
                self.view.record_commands(commands, state["game_loop"])
                if not global_decision:
                    for row in decisions:
                        if "command" in row:
                            self.next_action[row["unit"]] = (
                                state["game_loop"] + row["delay"]
                            )
            if self.job.get("idle_worker_harvest"):
                selected = {tag for command in commands for tag in command.units}
                assistance = idle_worker_harvest(state, selected)
                if assistance:
                    response = await issue(self.client, assistance)
                    for code in response.result:
                        self.results[str(code)] = self.results.get(str(code), 0) + 1
                    self.worker_assistance_commands += len(assistance)
                    self.view.record_commands(assistance, state["game_loop"])
                    decisions.extend(
                        {"source": "idle_worker_harvest", "command": c.as_dict()}
                        for c in assistance
                    )
            self.final_score = micro_score(packet)
            self.frames += 1
            self.commands += len(commands)
            self.stream.write(
                json.dumps(
                    {
                        "observation": state,
                        "decisions": decisions,
                        "score": self.final_score,
                    },
                    separators=(",", ":"),
                )
                + "\n"
            )
        except Exception as error:
            self.callback_error = repr(error)
            raise


def play_job(job):
    from loguru import logger

    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    output = Path(job["output"])
    output.mkdir(parents=True, exist_ok=False)
    with gzip.open(output / "trace.jsonl.gz", "xt") as stream:
        bot = ImitationBot(job, stream)
        result = run_game(
            validate_map(job["map"]),
            [
                Bot(Race.Terran, bot),
                Computer(
                    Race[job["race"]],
                    Difficulty[job["difficulty"]],
                    AIBuild[job["build"]],
                ),
            ],
            realtime=False,
            random_seed=job["seed"],
            game_time_limit=job["seconds"],
            save_replay_as=str(output / "game.SC2Replay"),
        )
    if bot.callback_error or not bot.frames:
        raise RuntimeError(bot.callback_error or "No model frames")
    receipt = {
        "status": "truncated" if result.name == "Tie" else "completed",
        "result": result.name,
        "policy": job["policy"],
        "policy_sha256": hashlib.sha256(Path(job["policy"]).read_bytes()).hexdigest(),
        "race": job["race"],
        "difficulty": job["difficulty"],
        "map": job["map"],
        "seed": job["seed"],
        "frames": bot.frames,
        "commands": bot.commands,
        "action_results": bot.results,
        "score": bot.final_score,
        "game_seconds": bot.time,
        "workers": bot.workers.amount,
        "army_supply": bot.supply_army,
        "supply_cap": bot.supply_cap,
        "structures": {
            kind.name: bot.structures(kind).amount
            for kind in {u.type_id for u in bot.structures}
        },
        "worker_assistance_commands": bot.worker_assistance_commands,
        "idle_worker_harvest": job.get("idle_worker_harvest", False),
        "scripted_assistance": "initial worker harvesting"
        if job["initial_harvest"]
        else "none",
        "macro_decisions": "factorized entity imitation",
        "micro_decisions": "same imitation model; not roach controller",
    }
    (output / "episode.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--race", choices=["Terran", "Protoss", "Zerg"], default="Zerg")
    parser.add_argument(
        "--difficulty",
        choices=["VeryEasy", "Easy", "Medium", "Hard", "Harder", "VeryHard", "Elite"],
        default="VeryEasy",
    )
    parser.add_argument(
        "--build",
        choices=["RandomBuild", "Rush", "Timing", "Power", "Macro", "Air"],
        default="RandomBuild",
    )
    parser.add_argument("--map", default="Simple64")
    parser.add_argument("--seed", type=int, default=40000)
    parser.add_argument("--seconds", type=positive, default=600)
    parser.add_argument("--step", type=positive, default=16)
    parser.add_argument("--wall-seconds", type=positive, default=180)
    parser.add_argument("--initial-harvest", action="store_true")
    parser.add_argument(
        "--idle-worker-harvest",
        action="store_true",
        help="Assign idle SCVs to visible minerals, preserving ongoing and current model orders",
    )
    args = parser.parse_args()
    FactorPolicy.load(args.policy)
    validate_map(args.map)
    if args.output.exists():
        parser.error("Output exists; choose a new episode directory")
    job = {
        key: getattr(args, key)
        for key in (
            "race",
            "difficulty",
            "build",
            "map",
            "seed",
            "seconds",
            "step",
            "initial_harvest",
            "idle_worker_harvest",
        )
    }
    job.update(policy=str(args.policy.resolve()), output=str(args.output.resolve()))
    receipt = supervise(play_job, (job,), args.wall_seconds)
    args.output.with_suffix(".supervision.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    print(json.dumps(receipt), flush=True)
    if receipt["status"] not in ("completed", "truncated"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
