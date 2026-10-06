"""Execute the factorized imitation model through broad raw gameplay controls."""

from src.learning.teacher_states import remember_command
from src.learning.broad_rl import ResidualPPO, episode_arrays

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
from src.learning.gameplay import Command, PlayerView, image_dict
from src.learning.imitation import FactorPolicy, unit_features, DELAYS, softmax
from src.learning.global_imitation import (
    global_features,
    select_group,
    coordinate_signs,
)
from src.learning.live import ability_query, issue
from src.learning.placement import resolve_placements
from src.learning.actor_selection import actor_features, select_actors, group_features
from src.learning.spatial_construction import (
    decode_terrain,
    spatial_candidates,
    candidate_features,
    rank_points,
)
from src.learning.sandbox import micro_score
from src.runner import positive, validate_map
from src.runtime import supervise


def replace_arguments(macro, arguments, signs):
    output = dict(macro, **{k: v for k, v in arguments.items() if k != "ability"})
    output["point"] = arguments["point"] * np.asarray(signs)
    return output


def choose_ability(logits, allowed, rng, sample, wait_unavailable=False):
    if wait_unavailable and not sample and int(logits.argmax()) not in allowed:
        return 0
    scores = logits[allowed]
    return (
        allowed[int(rng.choice(len(allowed), p=softmax(scores[None, :])[0]))]
        if sample
        else allowed[int(scores.argmax())]
    )


def command_delay(job, residual, predicted, results):
    if job.get("learned_cadence"):
        return max(job["step"], predicted) if 1 in results else job["step"]
    return job["step"] if job.get("fixed_cadence") or residual else predicted


def decode_commands(
    state,
    actors,
    output,
    available,
    catalog,
    unit_types,
    map_size,
    chosen_abilities=None,
):
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
        ability = (
            legal[int(np.argmax(output["ability"][index, legal]))]
            if chosen_abilities is None
            else chosen_abilities[index]
        )
        if ability not in legal:
            raise ValueError("Selected ability is not engine-legal for this actor")
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
        self.actor_policy = (
            FactorPolicy.load(job["actor_policy"]) if job.get("actor_policy") else None
        )
        self.argument_policy = (
            FactorPolicy.load(job["argument_policy"])
            if job.get("argument_policy")
            else None
        )
        self.spatial_policy = (
            FactorPolicy.load(job["spatial_policy"])
            if job.get("spatial_policy")
            else None
        )
        if self.spatial_policy and (
            self.spatial_policy.evidence.get("role") != "spatial_construction"
            or self.spatial_policy.evidence["macro_sha256"]
            != hashlib.sha256(Path(job["policy"]).read_bytes()).hexdigest()
        ):
            raise ValueError("Spatial scorer is incompatible with macro checkpoint")
        if self.argument_policy and (
            self.argument_policy.evidence.get("role") != "argument_prediction"
            or self.argument_policy.evidence["macro_sha256"]
            != hashlib.sha256(Path(job["policy"]).read_bytes()).hexdigest()
        ):
            raise ValueError("Argument predictor is incompatible with macro checkpoint")
        if self.actor_policy and (
            self.actor_policy.evidence.get("role") != "actor_selection"
            or self.actor_policy.evidence["macro_sha256"]
            != hashlib.sha256(Path(job["policy"]).read_bytes()).hexdigest()
        ):
            raise ValueError("Actor pointer is incompatible with macro checkpoint")
        self.residual = (
            ResidualPPO.load(
                job["residual_policy"],
                hashlib.sha256(Path(job["policy"]).read_bytes()).hexdigest(),
            )
            if job.get("residual_policy")
            else None
        )
        self.rl_records = []
        self.view = PlayerView()
        self.next_action = {}
        self.next_global = 0
        self.policy_history = []
        self.rng = np.random.default_rng(job["seed"])
        self.worker_assistance_commands = 0
        self.frames = self.commands = 0
        self.results = {}
        self.callback_error = None
        self.final_score = None

    async def on_start(self):
        self.client.game_step = self.job["step"]
        data = (await self.client._execute(data=pb.RequestData(ability_id=True))).data
        self.catalog = {
            a.ability_id: {
                "target": a.target,
                "allow_autocast": a.allow_autocast,
                "is_building": a.is_building,
                "footprint_radius": a.footprint_radius,
            }
            for a in data.abilities
        }
        images = {
            name: image_dict(getattr(self.game_info._proto.start_raw, name))
            for name in ("pathing_grid", "placement_grid", "terrain_height")
        }
        self.terrain = decode_terrain(images)
        (Path(self.job["output"]) / "terrain.json").write_text(
            json.dumps(images) + "\n"
        )
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
            feature_state = dict(state, recent_commands=self.policy_history[-32:])
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
            model_results = []
            rl_decision = None
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
                        feature_state,
                        self.policy.unit_types,
                        self.policy.sizes["ability"],
                        canonical=canonical,
                        summarize=self.policy.evidence.get("entity_encoder")
                        == "per_type_spatial_orders",
                        semantics=self.policy.evidence.get("action_history_encoder")
                        == "roles_targets_age",
                        upgrade_count=self.policy.evidence.get("upgrade_count", 0),
                    )
                    output = self.policy.predict(x[None, :])
                    allowed = [0, *sorted(set().union(*abilities.values()))]
                    if self.residual:
                        context = self.policy.command_context(x, 0)
                        prior = output["ability"][0].copy()
                        mask = np.zeros(len(prior), dtype=bool)
                        mask[allowed] = True
                        q, _, values = self.residual.distribution(
                            context[None, :], prior[None, :], mask[None, :]
                        )
                        ability = (
                            int(self.rng.choice(len(prior), p=q[0]))
                            if self.job.get("sample")
                            else int(q[0].argmax())
                        )
                        self.rl_records.append(
                            dict(
                                state=context,
                                prior=prior,
                                mask=mask,
                                action=ability,
                                log_prob=float(np.log(q[0, ability]))
                                if self.job.get("sample")
                                else 0.0,
                                value=float(values[0]),
                                loop=state["game_loop"],
                                killed=micro_score(packet)["killed_value"],
                            )
                        )
                        rl_decision = {
                            "ability": ability,
                            "probability": float(q[0, ability])
                            if self.job.get("sample")
                            else 1.0,
                            "policy_probability": float(q[0, ability]),
                            "value": float(values[0]),
                            "allowed": allowed,
                        }
                    else:
                        ability = choose_ability(
                            output["ability"][0],
                            allowed,
                            self.rng,
                            self.job.get("sample", False),
                            self.job.get("wait_unavailable", False),
                        )
                    if (
                        not self.residual
                        and not ability
                        and int(output["ability"][0].argmax()) not in allowed
                    ):
                        decisions.append(
                            {
                                "source": "unavailable_intent",
                                "raw_ability": int(output["ability"][0].argmax()),
                                "ability": 0,
                                "rejected": "engine_availability",
                                "retry_loops": self.job["step"],
                            }
                        )
                    # predict already conditioned arguments on its raw argmax.
                    # Only an alternate legal fallback needs another forward pass.
                    if ability and ability != int(output["ability"][0].argmax()):
                        output = self.policy.predict(x[None, :], abilities=[ability])
                    if canonical:
                        signs = coordinate_signs(state, origin)
                        output["point"][:, :2] *= signs
                        output["point"][:, 2:4] *= signs
                    group = []
                    if ability and self.actor_policy:
                        actors = sorted(actors, key=lambda u: u["tag"])
                        context = self.policy.command_context(x, ability)
                        actor_x = np.stack(
                            [
                                actor_features(
                                    feature_state,
                                    u,
                                    index,
                                    self.policy.unit_types,
                                    self.policy.sizes["ability"],
                                    origin,
                                    context,
                                )
                                for index, u in enumerate(actors)
                            ]
                        )
                        actor_logits = self.actor_policy.predict(actor_x)["ability"]
                        group = select_actors(actors, actor_logits, abilities, ability)
                    elif ability:
                        group = select_group(
                            state,
                            output,
                            abilities,
                            ability,
                            self.policy.unit_types,
                            origin,
                        )
                    if group:
                        if self.argument_policy:
                            argument_x = group_features(
                                feature_state,
                                group,
                                self.policy.unit_types,
                                self.policy.sizes["ability"],
                                origin,
                                self.policy.command_context(x, ability),
                            )
                            output = replace_arguments(
                                output,
                                self.argument_policy.predict(argument_x[None, :]),
                                coordinate_signs(state, origin)
                                if canonical
                                else [1.0, 1.0],
                            )
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
                            chosen_abilities=[ability],
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
                else:
                    x = np.stack(
                        [
                            unit_features(feature_state, u, self.policy.unit_types)
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
                rankings = {}
                if self.spatial_policy:
                    own = {
                        u["tag"]: u
                        for u in state["units"] + state["owned_memory"]
                        if u["alliance"] == 1
                    }
                    for command in commands:
                        descriptor = self.catalog[command.ability]
                        if (
                            not descriptor.get("is_building")
                            or command.target_point is None
                        ):
                            continue
                        points = spatial_candidates(
                            state["map_size"],
                            descriptor["footprint_radius"],
                            self.spatial_policy.evidence["grid_spacing"],
                        )
                        features = candidate_features(
                            feature_state,
                            [own[tag] for tag in command.units],
                            origin,
                            self.policy.command_context(x, command.ability),
                            points,
                            self.terrain,
                            descriptor["footprint_radius"],
                            self.spatial_policy.evidence["structure_types"],
                        )
                        rankings[(command.ability, command.units)] = rank_points(
                            self.spatial_policy, features, points
                        )
                commands, placement_trace = await resolve_placements(
                    self.client, commands, self.catalog, state, ranked_points=rankings
                )
                if placement_trace:
                    decisions.append(
                        {"source": "engine_placement", "placements": placement_trace}
                    )
                result = (
                    await issue(self.client, commands)
                    if commands
                    else pb.ResponseAction()
                )
                model_results = list(result.result)
                if global_decision and group:
                    self.next_global = state["game_loop"] + command_delay(
                        self.job,
                        self.residual,
                        int(DELAYS[output["delay"][0].argmax()]),
                        model_results,
                    )
                for code in result.result:
                    self.results[str(code)] = self.results.get(str(code), 0) + 1
                self.view.record_commands(commands, state["game_loop"])
                self.policy_history.extend(
                    remember_command(c.as_dict(), feature_state, state["game_loop"])
                    for c in commands
                )
                self.policy_history = self.policy_history[-32:]
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
                        "model_recent_commands": feature_state["recent_commands"],
                        "issued_model_commands": [c.as_dict() for c in commands],
                        "score": self.final_score,
                        "model_action_results": model_results,
                        "rl_decision": rl_decision,
                    },
                    separators=(",", ":"),
                )
                + "\n"
            )
        except Exception as error:
            self.callback_error = repr(error)
            raise

    async def on_end(self, result):
        if self.residual:
            packet = (await self.client.observation()).observation
            self.final_score = micro_score(packet)
            self.rl_final_loop = packet.observation.game_loop


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
    if bot.residual:
        arrays = episode_arrays(
            bot.rl_records,
            result.name,
            bot.final_score["killed_value"],
            bot.rl_final_loop,
        )
        metadata = {
            "base_sha256": bot.residual.base_sha256,
            "residual_sha256": hashlib.sha256(
                Path(job["residual_policy"]).read_bytes()
            ).hexdigest(),
            "reward": "incremental killed-resource value /100 +100 victory -100 defeat; finite-horizon timeout 0",
            "finite_horizon": True,
            "epsilon": bot.residual.epsilon,
            "feature_encoder": "frozen_macro_wait_context",
            "sampling": "mixture" if job.get("sample") else "greedy",
            "result": result.name,
        }
        np.savez_compressed(
            output / "rollout.npz", metadata=np.array(json.dumps(metadata)), **arrays
        )
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
        "scripted_assistance": "; ".join(
            name
            for enabled, name in (
                (job["initial_harvest"], "initial worker harvesting"),
                (
                    job.get("idle_worker_harvest", False),
                    "idle worker harvesting, preserving ongoing/current model orders",
                ),
            )
            if enabled
        )
        or "none",
        "construction_placement": "learned uniform-grid candidate score, filtered by engine legality"
        if job.get("spatial_policy")
        else "closest engine-valid half-tile point around requested location; visible gas candidates",
        "total_commands": bot.commands + bot.worker_assistance_commands,
        "history_contract": "model-issued decisions only; assistance is traced separately and observable through unit orders",
        "actor_pointer": job.get("actor_policy"),
        "argument_predictor": job.get("argument_policy"),
        "spatial_scorer": job.get("spatial_policy"),
        "spatial_scorer_sha256": hashlib.sha256(
            Path(job["spatial_policy"]).read_bytes()
        ).hexdigest()
        if job.get("spatial_policy")
        else None,
        "argument_predictor_sha256": hashlib.sha256(
            Path(job["argument_policy"]).read_bytes()
        ).hexdigest()
        if job.get("argument_policy")
        else None,
        "actor_pointer_sha256": hashlib.sha256(
            Path(job["actor_policy"]).read_bytes()
        ).hexdigest()
        if job.get("actor_policy")
        else None,
        "sampled_commands": job.get("sample", False),
        "wait_unavailable": job.get("wait_unavailable", False),
        "fixed_cadence": (job.get("fixed_cadence", False) or bool(bot.residual))
        and not job.get("learned_cadence", False),
        "learned_cadence": job.get("learned_cadence", False),
        "residual_policy": job.get("residual_policy"),
        "rl_decisions": len(bot.rl_records),
        "macro_decisions": "PPO raw-ability residual with frozen human encoder"
        if bot.residual
        else "factorized entity imitation",
        "micro_decisions": "same imitation model; not roach controller",
    }
    (output / "episode.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--actor-policy", type=Path, help="Compatible learned per-entity actor pointer"
    )
    parser.add_argument(
        "--argument-policy",
        type=Path,
        help="Compatible learned selected-group argument predictor",
    )
    parser.add_argument(
        "--spatial-policy",
        type=Path,
        help="Compatible learned construction candidate scorer",
    )
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
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Sample engine-legal global commands from the learned distribution",
    )
    parser.add_argument("--initial-harvest", action="store_true")
    parser.add_argument(
        "--residual-policy",
        type=Path,
        help="Compatible CPU-only raw ability PPO residual; frozen human unit and target models",
    )
    parser.add_argument(
        "--fixed-cadence",
        action="store_true",
        help="Reevaluate every engine step instead of sleeping for a predicted delay",
    )
    parser.add_argument(
        "--learned-cadence",
        action="store_true",
        help="Residual controller uses predicted delays after accepted commands; retries failures next step",
    )
    parser.add_argument(
        "--wait-unavailable",
        action="store_true",
        help="Reevaluate unavailable intended commands instead of selecting an unrelated legal fallback",
    )
    parser.add_argument(
        "--idle-worker-harvest",
        action="store_true",
        help="Assign idle SCVs to visible minerals, preserving ongoing and current model orders",
    )
    args = parser.parse_args()
    policy = FactorPolicy.load(args.policy)
    if args.learned_cadence and (not args.residual_policy or args.fixed_cadence):
        parser.error("Learned cadence requires a residual policy without fixed cadence")
    if args.fixed_cadence and "actor_type" not in policy.sizes:
        parser.error("Fixed cadence requires global decisions")
    if args.sample and "actor_type" not in policy.sizes:
        parser.error("Command sampling currently requires a global decision checkpoint")
    if args.wait_unavailable and (args.sample or "actor_type" not in policy.sizes):
        parser.error(
            "Waiting for unavailable intent currently requires deterministic global decisions"
        )
    if args.actor_policy:
        actor = FactorPolicy.load(args.actor_policy)
        if (
            actor.evidence.get("role") != "actor_selection"
            or actor.evidence["macro_sha256"]
            != hashlib.sha256(args.policy.read_bytes()).hexdigest()
        ):
            parser.error("Actor pointer is incompatible with macro checkpoint")
    if args.argument_policy:
        argument = FactorPolicy.load(args.argument_policy)
        if "actor_type" not in policy.sizes or (
            argument.evidence.get("role") != "argument_prediction"
            or argument.evidence["macro_sha256"]
            != hashlib.sha256(args.policy.read_bytes()).hexdigest()
        ):
            parser.error("Argument predictor is incompatible with macro checkpoint")
    if args.spatial_policy:
        spatial = FactorPolicy.load(args.spatial_policy)
        if "actor_type" not in policy.sizes or (
            spatial.evidence.get("role") != "spatial_construction"
            or spatial.evidence["macro_sha256"]
            != hashlib.sha256(args.policy.read_bytes()).hexdigest()
        ):
            parser.error("Spatial scorer is incompatible with macro checkpoint")
    if args.residual_policy:
        if "actor_type" not in policy.sizes or args.wait_unavailable:
            parser.error(
                "Residual learning requires global native-masked choices without an unavailable-intent guard"
            )
        residual = ResidualPPO.load(
            args.residual_policy, hashlib.sha256(args.policy.read_bytes()).hexdigest()
        )
        if residual.parameters["actor"].shape != (32, policy.sizes["ability"]):
            parser.error("Residual dimensions do not match frozen macro")
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
            "sample",
            "wait_unavailable",
            "fixed_cadence",
            "learned_cadence",
        )
    }
    job.update(policy=str(args.policy.resolve()), output=str(args.output.resolve()))
    if args.residual_policy:
        job["residual_policy"] = str(args.residual_policy.resolve())
    if args.actor_policy:
        job["actor_policy"] = str(args.actor_policy.resolve())
    if args.argument_policy:
        job["argument_policy"] = str(args.argument_policy.resolve())
    if args.spatial_policy:
        job["spatial_policy"] = str(args.spatial_policy.resolve())
    receipt = supervise(play_job, (job,), args.wall_seconds)
    args.output.with_suffix(".supervision.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    print(json.dumps(receipt), flush=True)
    if receipt["status"] not in ("completed", "truncated"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
