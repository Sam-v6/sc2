"""Fixed source instructions with physical primitives; no learned policy or RL."""

import gzip
import json
import math
from pathlib import Path
from sc2.bot_ai import BotAI
from sc2.data import Race, Difficulty, AIBuild
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.position import Point2
from s2clientprotocol import sc2api_pb2 as pb, query_pb2 as query, common_pb2 as common
from src.runner import validate_map
from src.learning.gameplay import Command, PlayerView, protocol_dict
from src.learning.live import ability_query, issue
from src.learning.tournament_record import decode_record
from src.learning.producer_bindings import ProducerBindings
from src.learning.production_execution import (
    queried_command_ability,
    queued_supply,
    command_cost,
    worker_constructing,
)
from src.learning.production_primitives import (
    primitive_assistance,
    scripted_army_destination,
)


class FixedHumanPlanBot(BotAI):
    def __init__(self, job, stream):
        super().__init__()
        self.job = job
        self.stream = stream
        self.plan = json.loads(Path(job["plan"]).read_text())
        self.tickets = self.plan["tickets"]
        self.view = PlayerView()
        self.bindings = ProducerBindings()
        self.index = 0
        self.done = set()
        self.last_attempt = -1
        self.last_blocks = {}
        self.builder_tags = {}
        self.prepositioned = set()
        self.pending = []
        self.history = []
        self.divergence = None
        self.error = None
        self.frames = 0
        self.attacking = False
        self.search = 0
        self.next_mining = 0
        self.block = None
        record = decode_record(Path(job["record"]).read_bytes())
        f = record["units"]["fields"]
        self.entities = {}
        self.neutrals = {}
        self.source_frames = {}
        for i, step in enumerate(record["units"]["step"]):
            tag = int(f["id"][i])
            loop = int(record["steps"]["game_loop"][step])
            if f["alliance"][i] == 1:
                self.source_frames.setdefault(loop, {})[tag] = dict(
                    kind=int(f["unitType"][i]), point=list(map(float, f["pos"][i][:2]))
                )
            if f["alliance"][i] == 1 and tag not in self.entities:
                self.entities[tag] = dict(
                    loop=int(record["steps"]["game_loop"][step]),
                    kind=int(f["unitType"][i]),
                    point=list(map(float, f["pos"][i][:2])),
                )
        n = (
            record["neutral_units"]["fields"]
            if "neutral_units" in record
            else record["neutral"]["fields"]
        )
        for i, tag in enumerate(n["id"]):
            self.neutrals.setdefault(int(tag), list(map(float, n["pos"][i][:2])))

    async def on_start(self):
        self.client.game_step = 8
        self.data = protocol_dict(
            (
                await self.client._execute(
                    data=pb.RequestData(
                        ability_id=True, unit_type_id=True, upgrade_id=True
                    )
                )
            ).data
        )
        self.catalog = {a["ability_id"]: a for a in self.data["abilities"]}
        self.types = {u["unit_id"]: u for u in self.data["units"]}
        self.products = {}
        self.food = {}
        self.costs = {
            t["command"]["ability"]: command_cost(t["command"]["ability"], self.data)
            for t in self.tickets
        }
        for u in self.data["units"]:
            if u.get("ability_id"):
                self.food[u["ability_id"]] = max(
                    self.food.get(u["ability_id"], 0), u.get("food_required", 0)
                )
            if 8 in u.get("attributes", []) and u.get("ability_id"):
                self.products.setdefault(u["ability_id"], []).append(u["unit_id"])
        source = self.entities[4347920385]["point"]
        if math.dist(source, tuple(self.start_location)) > 0.1:
            raise ValueError(
                "Source spawn mismatch: " + str(tuple(self.start_location))
            )

    def source_product(self, ticket, point):
        kinds = self.products.get(ticket["command"]["ability"], [])
        existing = [
            tag
            for tag, e in self.source_frames[ticket["loop"]].items()
            if e["kind"] in kinds and math.dist(e["point"], point) < 0.1
        ]
        if len(existing) == 1:
            return existing[0]
        matches = [
            tag
            for tag, e in self.entities.items()
            if e["loop"] >= ticket["loop"]
            and e["kind"] in kinds
            and math.dist(e["point"], point) < 0.1
        ]
        return matches[0] if len(matches) == 1 else None

    def choose_worker(self, source, state, point, explicit_move):
        own = [
            u
            for u in state["units"]
            if u["alliance"] == 1 and u["unit_type"] == 45 and u.get("health", 1) > 0
        ]
        actor = next((u for u in own if u["tag"] == self.builder_tags.get(source)), None)
        if actor is None:
            free = [
                u
                for u in own
                if u["tag"] not in self.builder_tags.values()
                and not worker_constructing(u, state, self.catalog)
            ]
            if not free:
                return None
            actor = min(
                free,
                key=lambda u: math.dist(
                    u["position"][:2], point or tuple(self.start_location)
                ),
            )
            self.builder_tags[source] = actor["tag"]
        if worker_constructing(actor, state, self.catalog) and not explicit_move:
            return None
        return actor

    def pending_heads(self, loop):
        heads, seen = [], set()
        for index, ticket in enumerate(self.tickets):
            if index in self.done:
                continue
            actor = tuple(ticket["command"]["units"])
            if actor not in seen:
                seen.add(actor)
                if ticket["loop"] <= loop:
                    heads.append(index)
        return heads

    def retire_unsubmitted_cancellations(self, loop):
        for index, ticket in enumerate(self.tickets):
            if (
                index in self.done
                or ticket["loop"] > loop
                or ticket["command"]["ability"] != 3671
            ):
                continue
            previous = next(
                (
                    i
                    for i in range(index - 1, -1, -1)
                    if self.tickets[i]["command"]["units"] == ticket["command"]["units"]
                ),
                None,
            )
            if (
                previous is not None
                and previous not in self.done
                and self.tickets[previous]["name"].startswith("Train ")
            ):
                self.done.update((previous, index))
                self.history.append(
                    dict(
                        event="cancel_unsubmitted_request",
                        loop=loop,
                        ticket=index,
                        cancelled_ticket=previous,
                    )
                )

    def retire_superseded_worker_builds(self, loop):
        for index, ticket in enumerate(self.tickets):
            if (index in self.done or ticket['loop'] > loop
                    or ticket['actor_types'] != [45]
                    or not ticket['name'].startswith('Build ')
                    or not ticket['command'].get('target_point')):
                continue
            replacement = next((i for i in range(index+1, len(self.tickets))
                                if self.tickets[i]['command']['units'] == ticket['command']['units']), None)
            if replacement is None:
                continue
            later = self.tickets[replacement]
            if (later['loop'] <= loop and later['name'] == 'Move builder'
                    and not later['command']['queue']
                    and self.source_product(ticket, ticket['command']['target_point']) is None):
                self.done.add(index)
                self.history.append(dict(event='superseded_unsubmitted_build', loop=loop,
                                         ticket=index, replacement_ticket=replacement,
                                         source_loop=ticket['loop']))

    async def on_step(self, iteration):
        try:
            state = self.view.observe(self.state.response_observation)
            loop = state["game_loop"]
            own = [u for u in state["units"] if u["alliance"] == 1]
            self.frames += 1
            if not self.bindings.tags:
                bases = [u for u in own if u["unit_type"] == 18]
                assert len(bases) == 1
                self.bindings.bind(4347920385, bases[0]["tag"])
            for pending in list(self.pending):
                candidates = [
                    u
                    for u in own
                    if u["tag"] not in pending["before"]
                    and u["unit_type"] in pending["kinds"]
                    and math.dist(u["position"][:2], pending["point"]) < 0.1
                ]
                if len(candidates) == 1:
                    self.bindings.bind(pending["source"], candidates[0]["tag"])
                    self.pending.remove(pending)
                    self.history.append(
                        dict(
                            event="foundation_bound",
                            loop=loop,
                            source=pending["source"],
                            native=candidates[0]["tag"],
                        )
                    )
                elif len(candidates) > 1:
                    raise ValueError("Ambiguous native foundation")
            commands = []
            sent = None
            self.block = None
            available = None
            for error in state["action_errors"]:
                submitted = next(
                    (
                        h
                        for h in reversed(self.history)
                        if h.get("command", {}).get("ability") == error["ability_id"]
                        and error["unit_tag"] in h.get("command", {}).get("units", [])
                    ),
                    None,
                )
                if submitted:
                    self.divergence = dict(
                        loop=loop,
                        reason="delayed_production_error",
                        error=error,
                        submitted=submitted,
                    )
            self.retire_unsubmitted_cancellations(loop)
            self.retire_superseded_worker_builds(loop)
            expired = next(
                (
                    i
                    for i, ticket in enumerate(self.tickets)
                    if i not in self.done and loop - ticket["loop"] > 672
                ),
                None,
            )
            if expired is not None and self.divergence is None:
                self.divergence = dict(
                    loop=loop,
                    ticket=expired,
                    source_loop=self.tickets[expired]["loop"],
                    name=self.tickets[expired]["name"],
                    reason=self.last_blocks.get(expired, "instruction_deadline"),
                    player=state["player"],
                )
            if self.divergence:
                self.stream.write(
                    json.dumps(
                        dict(
                            loop=loop,
                            observation=state,
                            index=self.index,
                            bindings=self.bindings.tags,
                            divergence=self.divergence,
                        )
                    )
                    + "\n"
                )
                await self.client.leave()
                return
            heads = self.pending_heads(loop)
            self.index = next(
                (i for i in heads if i > self.last_attempt),
                heads[0] if heads else len(self.tickets),
            )
            if self.index < len(self.tickets):
                ticket = self.tickets[self.index]
                source = ticket["command"]
                ability = source["ability"]
                point = source.get("target_point")
                target = None
                if loop >= ticket["loop"]:
                    actor = None
                    if ticket["actor_types"] == [45]:
                        location = point or self.neutrals.get(source.get("target_unit"))
                        actor = self.choose_worker(
                            source["units"][0],
                            state,
                            location,
                            ticket["name"] == "Move builder",
                        )
                    elif len(source["units"]) == 1:
                        actor = self.bindings.resolve(source["units"][0], state)
                    if actor is None:
                        self.block = "source_actor_unbound_or_lost"
                    elif source.get("target_unit"):
                        location = self.neutrals.get(source["target_unit"])
                        candidates = [
                            u
                            for u in state["units"]
                            if u["alliance"] == 3
                            and location
                            and math.dist(u["position"][:2], location) < 0.1
                            and u.get("display_type", 1) == 1
                        ]
                        if len(candidates) == 1:
                            target = candidates[0]["tag"]
                        else:
                            self.block = "unobserved_or_ambiguous_target"
                    if actor and self.block is None:
                        packet = (
                            await self.client._execute(
                                query=ability_query([actor["tag"]])
                            )
                        ).query
                        available = {
                            a.ability_id
                            for entry in packet.abilities
                            for a in entry.abilities
                        }
                        resolved = queried_command_ability(
                            ability, available, self.catalog
                        )
                        if resolved is None:
                            if ability == 3671 and not actor.get("orders"):
                                self.history.append(
                                    dict(
                                        event="cancel_empty_queue",
                                        loop=loop,
                                        ticket=self.index,
                                        source_loop=ticket["loop"],
                                        native=actor["tag"],
                                    )
                                )
                                self.done.add(self.index)
                            else:
                                self.block = "native_ability_unavailable"
                        else:
                            ability = resolved
                        if self.catalog[ability].get("friendly_name", "").startswith(
                            ("Lift", "Land", "Build TechLab", "Build Reactor")
                        ) and actor.get("orders"):
                            self.block = "producer_busy"
                    if actor and self.block is None and self.index not in self.done:
                        if self.food.get(ability, 0) > state["player"].get(
                            "food_cap", 0
                        ) - state["player"].get("food_used", 0) - queued_supply(
                            state, self.data
                        ):
                            self.block = "supply"
                    if actor and self.block is None and self.index not in self.done:
                        command = Command(
                            ability,
                            (actor["tag"],),
                            target_unit=target,
                            target_point=tuple(point) if point else None,
                            queue=source.get("queue", False),
                        )
                        expected = None
                        product_point = point
                        if ticket["name"].startswith("Build "):
                            if target:
                                product_point = next(
                                    u["position"][:2]
                                    for u in state["units"]
                                    if u["tag"] == target
                                )
                            elif ticket["name"].startswith(
                                ("Build TechLab", "Build Reactor")
                            ):
                                product_point = (
                                    [
                                        actor["position"][0] + 2.5,
                                        actor["position"][1] - 0.5,
                                    ]
                                    if not point
                                    else [point[0] + 2.5, point[1] - 0.5]
                                )
                            expected = (
                                self.source_product(ticket, product_point)
                                if product_point
                                else None
                            )
                            if expected is None:
                                self.block = "source_foundation_identity_unresolved"
                            elif expected in self.bindings.tags:
                                foundation = self.bindings.resolve(expected, state)
                                allowed = self.products[ability] + (
                                    [47] if ability == 319 else []
                                )
                                if foundation is None:
                                    self.block = "bound_foundation_lost"
                                elif (
                                    foundation["unit_type"] not in allowed
                                    or math.dist(
                                        foundation["position"][:2], product_point
                                    )
                                    >= 0.1
                                ):
                                    self.block = "bound_foundation_mismatch"
                                elif foundation.get("build_progress", 1) >= 1:
                                    self.history.append(
                                        dict(
                                            event="existing_completed_foundation",
                                            loop=loop,
                                            ticket=self.index,
                                            source=expected,
                                            native=foundation["tag"],
                                        )
                                    )
                                    self.done.add(self.index)
                                    command = None
                                    expected = None
                                else:
                                    command = Command(
                                        1,
                                        (actor["tag"],),
                                        target_unit=foundation["tag"],
                                    )
                                    expected = None
                        if command is not None and self.block is None:
                            older = next(
                                (
                                    i
                                    for i in range(self.index)
                                    if i not in self.done
                                    and self.tickets[i]["loop"] <= loop
                                ),
                                None,
                            )
                            reserved = (
                                self.costs[self.tickets[older]["command"]["ability"]]
                                if older is not None
                                else (0, 0)
                            )
                            price = self.costs.get(command.ability, (0, 0))
                            if price != (0, 0) and any(
                                state["player"].get(resource, 0) - cost < hold
                                for resource, cost, hold in zip(
                                    ("minerals", "vespene"), price, reserved
                                )
                            ):
                                self.block = "earlier_resource_commitment"
                        if (
                            command is not None
                            and command.ability == ability
                            and self.block is None
                            and (point or target)
                            and (ticket["name"].startswith(("Build ", "Land")))
                        ):
                            check_point = point if point else product_point
                            response = (
                                await self.client._execute(
                                    query=query.RequestQuery(
                                        placements=[
                                            query.RequestQueryBuildingPlacement(
                                                ability_id=ability,
                                                placing_unit_tag=actor["tag"],
                                                target_pos=common.Point2D(
                                                    x=check_point[0], y=check_point[1]
                                                ),
                                            )
                                        ]
                                    )
                                )
                            ).query
                            if response.placements[0].result != 1:
                                self.block = "native_exact_placement:" + str(
                                    response.placements[0].result
                                )
                        if self.block is None and command is not None:
                            commands = [command]
                            sent = dict(
                                ticket=self.index,
                                loop=loop,
                                source_loop=ticket["loop"],
                                sequence=ticket["sequence"],
                                name=ticket["name"],
                                command=command.as_dict(),
                            )
                            if expected is not None:
                                self.pending.append(
                                    dict(
                                        source=expected,
                                        point=product_point,
                                        kinds=self.products[ability],
                                        before=[u["tag"] for u in own],
                                    )
                                )
            selected = {tag for c in commands for tag in c.units}
            selected.update(
                self.builder_tags[tag] for tag in self.prepositioned if tag in self.builder_tags
            )
            selected.update(
                u["tag"]
                for u in own
                if u.get("orders")
                and any(
                    self.catalog.get(o["ability_id"], {})
                    .get("friendly_name", "")
                    .startswith("Build ")
                    for o in u["orders"]
                )
            )
            destination, self.attacking, self.search = scripted_army_destination(
                state,
                self.types,
                tuple(self.start_location),
                tuple(self.enemy_start_locations[0]),
                tuple(self.game_info.map_center),
                [tuple(p) for p in self.expansion_locations_list],
                self.attacking,
                self.search,
            )
            mining = loop >= self.next_mining
            if mining:
                self.next_mining = loop + 24
            landing_points = [
                (order['target_world_space_pos']['x'], order['target_world_space_pos']['y'])
                for unit in own for order in unit.get('orders', [])
                if self.catalog.get(order['ability_id'], {}).get('friendly_name', '').startswith('Land')
                and order.get('target_world_space_pos')
            ]
            if self.index < len(self.tickets) and ticket['name'].startswith('Land'):
                landing_points.append(tuple(source['target_point']))
            assists = primitive_assistance(
                state,
                selected,
                self.types,
                self.catalog,
                destination,
                lambda p: self.in_map_bounds(Point2(p))
                and self.in_pathing_grid(Point2(p)),
                mining,
                landing_points,
            )
            batch = commands + assists
            result = await issue(self.client, batch) if batch else pb.ResponseAction()
            if sent:
                sent["result"] = result.result[0]
                self.history.append(sent)
                if result.result[0] == 1:
                    self.done.add(self.index)
                    if ticket["name"] == "Move builder":
                        self.prepositioned.add(source["units"][0])
                else:
                    self.divergence = dict(
                        loop=loop,
                        ticket=self.index,
                        reason="rejected_command",
                        detail=sent,
                    )
            if (
                self.index in self.done
                and ticket["actor_types"] == [45]
                and ticket["name"].startswith("Build ")
            ):
                self.prepositioned.discard(source["units"][0])
            self.last_blocks[self.index] = self.block
            self.last_attempt = -1 if self.index in self.done else self.index
            self.stream.write(
                json.dumps(
                    dict(
                        loop=loop,
                        observation=state,
                        index=self.index,
                        completed=sorted(self.done),
                        block=self.block,
                        bindings=self.bindings.tags,
                        worker_bindings=self.builder_tags,
                        prepositioned=sorted(self.prepositioned),
                        pending=self.pending,
                        available=sorted(available) if available is not None else None,
                        execution=sent,
                        commands=[c.as_dict() for c in batch],
                        results=list(result.result),
                        divergence=self.divergence,
                    )
                )
                + "\n"
            )
            if self.divergence:
                await self.client.leave()
        except Exception as e:
            self.error = repr(e)
            raise


def play_fixed_human_plan(job):
    out = Path(job["output"])
    out.mkdir(exist_ok=False)
    with gzip.open(out / "trace.jsonl.gz", "xt") as stream:
        bot = FixedHumanPlanBot(job, stream)
        result = run_game(
            validate_map("AcropolisLE"),
            [
                Bot(Race.Terran, bot),
                Computer(Race.Zerg, Difficulty.VeryEasy, AIBuild.Rush),
            ],
            realtime=False,
            random_seed=job["seed"],
            game_time_limit=600,
            save_replay_as=str(out / "game.SC2Replay"),
        )
    if bot.error or not bot.frames:
        raise RuntimeError(bot.error or "No native fixed-plan frames")
    report = dict(
        status="diverged" if bot.divergence else "finished",
        result=result.name,
        frames=bot.frames,
        instructions_resolved=len(bot.done),
        total=len(bot.tickets),
        divergence=bot.divergence,
        history=bot.history,
        training=False,
        rl=False,
        fixed_human_plan=True,
        job=job,
    )
    (out / "episode.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
