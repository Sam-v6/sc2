"""Bounded headless episodes driven entirely by a joint imitation checkpoint."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

from sc2.bot_ai import BotAI
from sc2.data import AIBuild, Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer
from s2clientprotocol import sc2api_pb2 as pb

from src.learning.actor_selection import construction_products
from src.learning.entity_execution import (
    JointCommandAgent,
    command_available,
    command_candidates,
    validate_order_aliases,
)
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import digest
from src.learning.gameplay import PlayerView, image_dict, protocol_dict
from src.learning.live import ability_query, issue
from src.learning.placement import resolve_placements
from src.learning.sandbox import micro_score
from src.runner import positive, validate_map
from src.runtime import supervise


def decision_step(current_loop, next_loop, maximum):
    return min(maximum, max(1, next_loop - current_loop))


def load_policy(path, controller="joint"):
    if controller == "joint":
        return JointEntityPolicy.load(path)
    if controller == "goal-first":
        from src.learning.goal_first_policy import GoalFirstPolicy

        return GoalFirstPolicy.load(path)
    raise ValueError("Unknown imitation controller: " + controller)


def validate_engine(policy, data):
    vocabulary = tuple(
        max((getattr(row, key) for row in rows), default=-1) + 1
        for rows, key in (
            (data.units, "unit_id"),
            (data.abilities, "ability_id"),
            (data.upgrades, "upgrade_id"),
        )
    )
    expected = getattr(policy, "engine_vocabulary", None)
    if expected is None:
        expected = (
            len(policy.encoder.parameters["types"]),
            len(policy.encoder.parameters["abilities"]),
            policy.encoder.parameters["scene"].shape[0]
            // (2 if policy.missing_fields else 1)
            - 13,
        )
    if vocabulary != expected:
        raise ValueError("Joint checkpoint and engine vocabularies differ")
    return vocabulary


class JointImitationBot(BotAI):
    def __init__(self, job, stream):
        super().__init__()
        self.job, self.stream = job, stream
        self.policy, self.metadata = load_policy(
            job["policy"], job.get("controller", "joint")
        )
        if (
            job.get("condition_available") or job.get("ability_seed") is not None
        ) and job.get("controller") != "goal-first":
            raise ValueError(
                "Conditioned/sampled decoding requires the goal-first controller"
            )
        self.observation_profile = None
        self.observation_profile_sha256 = None
        if job.get("observation_profile"):
            if not self.policy.missing_fields:
                raise ValueError(
                    "Partial observation profiles require a missing-field model"
                )
            content = Path(job["observation_profile"]).read_bytes()
            self.observation_profile = json.loads(content)
            self.observation_profile_sha256 = hashlib.sha256(content).hexdigest()
        self.view = PlayerView()
        self.frames = self.commands = self.last_loop = 0
        self.decisions = self.availability_blocks = 0
        self.placement_blocks = self.placement_adjustments = 0
        self.final_player = None
        self.final_units = []
        self.action_results = {}
        self.callback_error = None
        self.last_score = None
        self.scheduled_step_counts = {}

    async def on_start(self):
        self.client.game_step = 1
        data = (
            await self.client._execute(
                data=pb.RequestData(ability_id=True, unit_type_id=True, upgrade_id=True)
            )
        ).data
        vocabulary = validate_engine(self.policy, data)
        terrain = {
            name: image_dict(getattr(self.game_info._proto.start_raw, name))
            for name in ("terrain_height", "pathing_grid", "placement_grid")
        }
        static = dict(
            game_info=protocol_dict(self.game_info._proto),
            game_data=protocol_dict(data),
            terrain=terrain,
        )
        (Path(self.job["output"]) / "static.json").write_text(json.dumps(static) + "\n")
        self.catalog = {a["ability_id"]: a for a in static["game_data"]["abilities"]}
        if self.observation_profile is not None:
            validate_order_aliases(self.observation_profile, self.catalog)
        self.agent = JointCommandAgent(
            self.policy,
            vocabulary,
            construction_products(static["game_data"]),
            terrain,
            self.observation_profile,
            self.job.get("ability_seed"),
        )

    def schedule_step(self):
        step = decision_step(
            self.last_loop, self.agent.next_loop, self.job.get("max_game_step", 1)
        )
        self.client.game_step = step
        self.scheduled_step_counts[str(step)] = (
            self.scheduled_step_counts.get(str(step), 0) + 1
        )

    async def on_step(self, iteration):
        try:
            packet = self.state.response_observation
            state = self.view.observe(packet)
            state["map_size"] = [self.game_info.map_size.x, self.game_info.map_size.y]
            self.frames += 1
            self.last_loop = state["game_loop"]
            self.last_score = micro_score(packet)
            feature_state = dict(state, recent_commands=list(self.agent.history))
            candidates = None
            candidate_queries = None
            if (
                self.job.get("condition_available")
                and self.last_loop >= self.agent.next_loop
            ):
                tags = [u["tag"] for u in state["units"] if u["alliance"] == 1]
                normal = (await self.client._execute(query=ability_query(tags))).query
                toggles = (
                    await self.client._execute(
                        query=ability_query(tags, ignore_resources=True)
                    )
                ).query
                candidates = command_candidates(normal, toggles, self.catalog)
                candidate_queries = dict(
                    normal=protocol_dict(normal), autocast=protocol_dict(toggles)
                )
            command, delay = self.agent.decide(feature_state, candidates)
            if command is None:
                self.schedule_step()
                return
            available = (
                await self.client._execute(query=ability_query(command.units))
            ).query
            self.decisions += 1
            issued = not self.job.get("wait_unavailable") or command_available(
                command, available, self.catalog
            )
            placement_queries, placement_trace = [], []
            dispatched = command if issued else None
            if not issued:
                self.availability_blocks += 1
            elif self.job.get("engine_placement"):

                async def placement_execute(**kwargs):
                    response = await self.client._execute(**kwargs)
                    placement_queries.append(
                        dict(
                            request=protocol_dict(kwargs["query"]),
                            response=protocol_dict(response.query),
                        )
                    )
                    return response

                commands, placement_trace = await resolve_placements(
                    SimpleNamespace(_execute=placement_execute),
                    [command],
                    self.catalog,
                    state,
                )
                dispatched = commands[0] if commands else None
                if dispatched is None:
                    self.placement_blocks += 1
                elif dispatched != command:
                    self.placement_adjustments += 1
            issued = dispatched is not None
            if issued:
                result = await issue(self.client, [dispatched])
                self.agent.record_issued(dispatched, state, delay)
                self.commands += 1
            else:
                # Unissued intentions never enter dispatched command history.
                result = pb.ResponseAction()
            self.schedule_step()
            for code in result.result:
                self.action_results[str(code)] = (
                    self.action_results.get(str(code), 0) + 1
                )
            self.stream.write(
                json.dumps(
                    dict(
                        observation=feature_state,
                        candidate_queries=candidate_queries,
                        command=command.as_dict(),
                        issued_command=dispatched.as_dict() if dispatched else None,
                        placement_queries=placement_queries,
                        placement_trace=placement_trace,
                        delay=delay,
                        issued=issued,
                        available=[protocol_dict(row) for row in available.abilities],
                        results=list(result.result),
                        score=self.last_score,
                    ),
                    separators=(",", ":"),
                )
                + "\n"
            )
        except Exception as error:
            self.callback_error = repr(error)
            raise

    async def on_end(self, result):
        packet = (await self.client.observation()).observation
        self.last_loop = packet.observation.game_loop
        self.last_score = micro_score(packet)
        state = self.view.observe(packet)
        self.final_player = state["player"]
        self.final_units = [
            dict(
                tag=u["tag"],
                unit_type=u["unit_type"],
                build_progress=u.get("build_progress", 1),
                position=u["position"],
            )
            for u in state["units"]
            if u["alliance"] == 1
        ]


def play_joint_job(job):
    from loguru import logger

    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    output = Path(job["output"])
    output.mkdir(parents=True, exist_ok=False)
    policy_path = Path(job["policy"])
    checksum = digest(policy_path)
    with gzip.open(output / "trace.jsonl.gz", "xt", encoding="utf-8") as stream:
        bot = JointImitationBot(job, stream)
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
        raise RuntimeError(bot.callback_error or "Joint model produced no frames")
    if digest(policy_path) != checksum:
        raise ValueError("Checkpoint changed during the episode")
    receipt = dict(
        status="truncated" if result.name == "Tie" else "completed",
        result=result.name,
        policy=str(policy_path),
        policy_sha256=checksum,
        map=job["map"],
        race=job["race"],
        difficulty=job["difficulty"],
        build=job["build"],
        seed=job["seed"],
        frames=bot.frames,
        commands=bot.commands,
        decisions=bot.decisions,
        availability_blocks=bot.availability_blocks,
        placement_blocks=bot.placement_blocks,
        placement_adjustments=bot.placement_adjustments,
        engine_placement=bool(job.get("engine_placement")),
        wait_unavailable=bool(job.get("wait_unavailable")),
        condition_available=bool(job.get("condition_available")),
        ability_seed=job.get("ability_seed"),
        final_player=bot.final_player,
        final_observed_own_units=bot.final_units,
        action_results=bot.action_results,
        game_seconds=bot.last_loop / 22.4,
        score=bot.last_score,
        controller="goal_first_imitation"
        if job.get("controller") == "goal-first"
        else "joint_imitation",
        step=1 if job.get("max_game_step", 1) == 1 else "adaptive",
        max_game_step=job.get("max_game_step", 1),
        scheduled_step_counts=bot.scheduled_step_counts,
        observation_profile=bot.observation_profile,
        observation_profile_sha256=bot.observation_profile_sha256,
        training=False,
        scope="Single frozen checkpoint episode; no acceptance or RL claim",
    )
    (output / "episode.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--controller", choices=("joint", "goal-first"), default="joint"
    )
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument(
        "--observation-profile",
        type=Path,
        help="Explicit partial-source input projection; raw native traces stay complete",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--map", default="AcropolisLE")
    parser.add_argument("--race", choices=("Terran", "Zerg", "Protoss"), default="Zerg")
    parser.add_argument(
        "--difficulty", choices=[d.name for d in Difficulty], default="VeryEasy"
    )
    parser.add_argument(
        "--build", choices=[b.name for b in AIBuild], default="RandomBuild"
    )
    parser.add_argument(
        "--engine-placement",
        action="store_true",
        help="Resolve learned construction points through local engine placement queries",
    )
    parser.add_argument(
        "--condition-available",
        action="store_true",
        help="Condition goal-first choices and casters on current engine abilities",
    )
    parser.add_argument(
        "--wait-unavailable",
        action="store_true",
        help="Retry model decisions next loop while selected unit commands are unavailable",
    )
    parser.add_argument(
        "--max-game-step",
        type=positive,
        default=1,
        help="Cap observation steps during model-chosen waits; default observes every loop",
    )
    parser.add_argument(
        "--ability-seed",
        type=int,
        help="Sample learned goal-first ability probabilities with this local seed",
    )
    parser.add_argument("--seed", type=int, default=120001)
    parser.add_argument("--seconds", type=positive, default=600)
    parser.add_argument("--wall-seconds", type=positive, default=120)
    args = parser.parse_args()
    validate_map(args.map)
    load_policy(args.policy, args.controller)
    if args.output.exists():
        parser.error("Use a fresh episode directory")
    job = dict(
        controller=args.controller,
        observation_profile=str(args.observation_profile.resolve())
        if args.observation_profile
        else None,
        max_game_step=args.max_game_step,
        policy=str(args.policy.resolve()),
        output=str(args.output.resolve()),
        map=args.map,
        race=args.race,
        difficulty=args.difficulty,
        build=args.build,
        seed=args.seed,
        wait_unavailable=args.wait_unavailable,
        condition_available=args.condition_available,
        engine_placement=args.engine_placement,
        ability_seed=args.ability_seed,
        seconds=args.seconds,
    )
    receipt = supervise(play_joint_job, (job,), args.wall_seconds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".supervision.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    print(json.dumps(receipt), flush=True)
    if receipt["status"] not in ("completed", "truncated"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
