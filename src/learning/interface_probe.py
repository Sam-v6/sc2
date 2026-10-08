"""Bounded engineering fixture for broad gameplay commands; never a training win."""

import argparse
import gzip
import json
from pathlib import Path
import sys

from src.runner import validate_map, positive
from src.runtime import supervise
from src.learning.gameplay import Command, PlayerView
from src.learning.live import ability_catalog, ability_query, issue
from sc2.bot_ai import BotAI
from sc2.data import Race, Difficulty
from sc2.ids.ability_id import AbilityId as A
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.main import run_game
from sc2.player import Bot, Computer
from s2clientprotocol import sc2api_pb2 as pb


class InterfaceProbe(BotAI):
    def __init__(self, output, stream, extended=False):
        super().__init__()
        self.output, self.stream = output, stream
        self.view = PlayerView()
        self.frames = 0
        self.error = None
        self.checks = {}
        self.results = []
        self.inventory = {}
        self.extended = extended

    async def on_start(self):
        self.client.game_step = 4
        await self.client.debug_all_resources()
        center = self.start_location.offset((8, 0))
        await self.client.debug_create_unit(
            [
                [U.MARINE, 2, center, 1],
                [U.MEDIVAC, 1, center.offset((1, 0)), 1],
                [U.SIEGETANK, 1, center.offset((4, 0)), 1],
                [U.SUPPLYDEPOT, 1, self.start_location.offset((-8, 0)), 1],
            ]
        )
        if self.extended:
            self.barracks_position = await self.find_placement(
                U.BARRACKS, near=self.start_location.offset((10, 8)), addon_place=True
            )
            bay_position = await self.find_placement(
                U.ENGINEERINGBAY, near=self.start_location.offset((-10, 8))
            )
            orbital_position = await self.find_placement(
                U.COMMANDCENTER, near=self.start_location.offset((12, -8))
            )
            await self.client.debug_create_unit(
                [
                    [U.BARRACKS, 1, self.barracks_position, 1],
                    [U.ENGINEERINGBAY, 1, bay_position, 1],
                    [U.ORBITALCOMMAND, 1, orbital_position, 1],
                    [U.MEDIVAC, 1, center.offset((8, 0)), 1],
                    [U.MARINE, 1, center.offset((8, 0)), 1],
                ]
            )
        self.marine_start = center
        self.depot_position = await self.find_placement(
            U.SUPPLYDEPOT, near=self.start_location.offset((0, 8))
        )
        data = (
            await self.client._execute(
                data=pb.RequestData(ability_id=True, unit_type_id=True)
            )
        ).data
        (self.output / "catalog.json").write_text(
            json.dumps(ability_catalog(data)) + "\n"
        )

    async def on_step(self, iteration):
        try:
            state = self.view.observe(self.state.response_observation)
            tags = [u["tag"] for u in state["units"] if u["alliance"] == 1]
            response = (await self.client._execute(query=ability_query(tags))).query
            for entry in response.abilities:
                self.inventory.setdefault(str(entry.unit_type_id), set()).update(
                    a.ability_id for a in entry.abilities
                )
            commands = []
            if iteration == 1:
                if self.extended:
                    self.depot_position = await self.find_placement(
                        U.SUPPLYDEPOT, near=self.start_location.offset((0, 8))
                    )
                marines = sorted(self.units(U.MARINE), key=lambda u: u.tag)[:2]
                self.marine_tags = [u.tag for u in marines]
                self.worker_tag = self.workers.first.tag
                self.tank_tag = self.units(U.SIEGETANK).first.tag
                await self.client.debug_set_unit_value([marines[0].tag], 2, 10)
                commands = [
                    Command(A.SIEGEMODE_SIEGEMODE.value, (self.tank_tag,)),
                    Command(
                        A.COMMANDCENTERTRAIN_SCV.value, (self.townhalls.first.tag,)
                    ),
                    Command(
                        A.TERRANBUILD_SUPPLYDEPOT.value,
                        (self.worker_tag,),
                        target_point=tuple(self.depot_position),
                    ),
                ]
            if iteration == 2:
                self.checks["damage_setup"] = (
                    self.units.find_by_tag(self.marine_tags[0]).health == 10
                )
                commands = [
                    Command(
                        A.MEDIVACHEAL_HEAL.value,
                        (min(self.units(U.MEDIVAC), key=lambda u: u.tag).tag,),
                        target_unit=self.marine_tags[0],
                    )
                ]
            if iteration == 8:
                self.checks["siege_transformed"] = bool(self.units(U.SIEGETANKSIEGED))
                self.checks["production_order"] = any(
                    o.ability.id == A.COMMANDCENTERTRAIN_SCV
                    for u in self.townhalls
                    for o in u.orders
                )
                self.checks["healing_observed"] = (
                    self.units.find_by_tag(self.marine_tags[0]).health > 10
                )
                commands = [
                    Command(
                        A.MOVE_MOVE.value,
                        (self.marine_tags[0],),
                        target_point=tuple(self.marine_start.offset((0, 4))),
                    ),
                    Command(
                        A.MOVE_MOVE.value,
                        (self.marine_tags[1],),
                        target_point=tuple(self.marine_start.offset((0, -4))),
                    ),
                    Command(A.UNSIEGE_UNSIEGE.value, (self.tank_tag,)),
                ]
            if iteration == 32:
                self.checks["construction_started"] = any(
                    u.build_progress < 1 for u in self.structures(U.SUPPLYDEPOT)
                )
                self.checks["unsiege_transformed"] = bool(self.units(U.SIEGETANK))
                positions = [
                    self.units.find_by_tag(tag).position.y for tag in self.marine_tags
                ]
                self.checks["independent_movement"] = (
                    positions[0] > self.marine_start.y + 1
                    and positions[1] < self.marine_start.y - 1
                )
                # Two queued moves for one unit must remain two real orders.
                commands = [
                    Command(
                        A.MOVE_MOVE.value,
                        (self.marine_tags[0],),
                        target_point=tuple(self.marine_start.offset((0, 6))),
                    ),
                    Command(
                        A.MOVE_MOVE.value,
                        (self.marine_tags[0],),
                        target_point=tuple(self.marine_start.offset((6, 6))),
                        queue=True,
                    ),
                ]
            if iteration == 33:
                self.checks["queue_preserved"] = (
                    len(self.units.find_by_tag(self.marine_tags[0]).orders) >= 2
                )
            if iteration == 95:
                self.checks["scv_produced"] = self.workers.amount >= 13
            if self.extended:
                commands.extend(await self.extended_commands(iteration, state))
            result = (
                await issue(self.client, commands) if commands else pb.ResponseAction()
            )
            self.results.extend(result.result)
            self.stream.write(
                json.dumps(
                    {
                        "observation": state,
                        "commands": [c.as_dict() for c in commands],
                        "results": list(result.result),
                    }
                )
                + "\n"
            )
            self.frames += 1
        except Exception as error:
            self.error = repr(error)
            raise

    async def extended_commands(self, iteration, state):
        """Debug setups isolate mechanics; no results count as training strength."""
        commands = []
        if iteration == 1:
            self.barracks_tag = self.structures(U.BARRACKS).first.tag
            self.bay_tag = self.structures(U.ENGINEERINGBAY).first.tag
            self.depot_tag = self.structures(U.SUPPLYDEPOT).first.tag
            self.transport_tag = max(self.units(U.MEDIVAC), key=lambda u: u.tag).tag
            self.passenger_tag = max(self.units(U.MARINE), key=lambda u: u.tag).tag
            self.orbital_tag = self.structures(U.ORBITALCOMMAND).first.tag
            await self.client.debug_set_unit_value([self.depot_tag], 2, 100)
            await self.client.debug_set_unit_value([self.orbital_tag], 1, 200)
            commands = [
                Command(
                    A.ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL1.value,
                    (self.bay_tag,),
                ),
                Command(A.BUILD_TECHLAB_BARRACKS.value, (self.barracks_tag,)),
                Command(A.MORPH_SUPPLYDEPOT_LOWER.value, (self.depot_tag,)),
                Command(
                    A.LOAD_MEDIVAC.value,
                    (self.transport_tag,),
                    target_unit=self.passenger_tag,
                ),
                Command(
                    A.SCANNERSWEEP_SCAN.value,
                    (self.orbital_tag,),
                    target_point=tuple(self.marine_start),
                ),
            ]
        if iteration == 16:
            self.checks["research_order"] = any(
                u.tag == self.bay_tag and u.orders for u in self.structures
            )
            self.checks["addon_started"] = bool(self.structures(U.BARRACKSTECHLAB))
            self.checks["depot_lowered"] = bool(self.structures(U.SUPPLYDEPOTLOWERED))
            self.checks["transport_loaded"] = any(
                p.tag == self.passenger_tag
                for p in self.units.find_by_tag(self.transport_tag).passengers
            )
            unload_position = await self.find_placement(
                U.SUPPLYDEPOT, near=self.start_location.offset((0, -8))
            )
            commands = [
                Command(A.CANCEL_BARRACKSADDON.value, (self.barracks_tag,)),
                Command(A.MORPH_SUPPLYDEPOT_RAISE.value, (self.depot_tag,)),
                Command(
                    A.UNLOADALLAT_MEDIVAC.value,
                    (self.transport_tag,),
                    target_point=tuple(unload_position),
                ),
            ]
        if iteration == 32:
            self.checks["addon_cancelled"] = not self.structures(U.BARRACKSTECHLAB)
            self.checks["depot_raised"] = (
                self.structures.find_by_tag(self.depot_tag).type_id == U.SUPPLYDEPOT
            )
            self.checks["transport_unloaded"] = (
                self.units.find_by_tag(self.passenger_tag) is not None
            )
            commands = [Command(A.LIFT_BARRACKS.value, (self.barracks_tag,))]
        if iteration == 64:
            self.checks["barracks_lifted"] = bool(self.structures(U.BARRACKSFLYING))
            commands = [
                Command(
                    A.LAND_BARRACKS.value,
                    (self.barracks_tag,),
                    target_point=tuple(self.barracks_position),
                )
            ]
        if iteration == 96:
            self.checks["repair_observed"] = (
                self.structures.find_by_tag(self.depot_tag).health > 100
            )
            self.checks["transport_unloaded"] = (
                self.units.find_by_tag(self.passenger_tag) is not None
            )
            self.checks["barracks_landed"] = bool(self.structures(U.BARRACKS))
        if iteration == 2:
            commands.append(
                Command(
                    A.EFFECT_REPAIR_SCV.value,
                    (self.workers[1].tag,),
                    target_unit=self.depot_tag,
                )
            )
            self.checks["scan_effect"] = any(
                e.id.value == 6 for e in self.state.effects
            )
        return commands


def probe_job(job):
    from loguru import logger

    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    output = Path(job["output"])
    output.mkdir(parents=True, exist_ok=False)
    with gzip.open(output / "trace.jsonl.gz", "xt") as stream:
        bot = InterfaceProbe(output, stream, job.get("extended", False))
        result = run_game(
            validate_map("Simple64"),
            [Bot(Race.Terran, bot), Computer(Race.Zerg, Difficulty.VeryEasy)],
            realtime=False,
            random_seed=1100,
            game_time_limit=25 if job.get("extended") else 20,
            save_replay_as=str(output / "game.SC2Replay"),
        )
    if bot.error or not bot.frames:
        raise RuntimeError(bot.error or "No probe frames")
    receipt = {
        "status": "completed"
        if all(bot.checks.values())
        and len(bot.checks) == (20 if job.get("extended") else 9)
        and all(x == 1 for x in bot.results)
        else "failed",
        "engineering_only": True,
        "game_result": result.name,
        "frames": bot.frames,
        "checks": bot.checks,
        "action_results": bot.results,
        "available_by_type": {k: sorted(v) for k, v in bot.inventory.items()},
    }
    (output / "probe.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wall-seconds", type=positive, default=90)
    parser.add_argument(
        "--extended",
        action="store_true",
        help="Also check research, repair, transformations, transport, addons, scan and lift/land",
    )
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; choose a new probe directory")
    receipt = supervise(
        probe_job,
        ({"output": str(args.output.resolve()), "extended": args.extended},),
        args.wall_seconds,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".supervision.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    print(json.dumps(receipt), flush=True)
    if receipt["status"] != "completed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
