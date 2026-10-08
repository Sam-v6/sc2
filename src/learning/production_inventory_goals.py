"""Source-backed whole human inventories and execution of their stock deficits."""

import hashlib
import json
from pathlib import Path

import numpy as np
from src.learning.production_execution import queued_work
from src.learning.production_intents import ProductionIntents


def opponent_selected_race(info, player_id):
    opponent = next(p for p in info.player_info if p.player_id != player_id)
    return {1: "Terr", 2: "Zerg", 3: "Prot"}.get(opponent.race_requested, "unknown")


class HumanGoalLibrary:
    def __init__(
        self, names, descriptor, targets, scale, refs, races, thresholds, checksum
    ):
        self.names, self.descriptor, self.targets = names, descriptor, targets
        self.scale, self.refs, self.races = scale, refs, races
        self.thresholds, self.checksum = thresholds, checksum
        self.expires, self.target, self.source = -1, None, None

    @classmethod
    def load(cls, directory):
        directory = Path(directory)
        audit = json.loads((directory / "audit.json").read_text())
        verification = json.loads((directory / "verification.json").read_text())
        if verification["status"] != "verified_human_goal_retrieval":
            raise ValueError("Unverified human inventory library")
        for path, checksum in {**audit["bindings"], **verification["bindings"]}.items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != checksum:
                raise ValueError("Human inventory source changed: " + path)
        source = Path("logs/roadmap/human-inventory-targets-03")
        names = json.loads((source / "preparation.json").read_text())["names"]
        races = {
            r["game"]: r["opponent_selected_race"]
            for r in json.loads((source / "opponent-race-audit.json").read_text())[
                "games"
            ]
        }
        with np.load(directory / "library.npz") as library:
            return cls(
                names,
                library["descriptor"],
                library["targets"],
                library["scale"],
                json.loads((directory / "library-rows.json").read_text()),
                races,
                audit["thresholds"],
                hashlib.sha256(
                    (source / "teaching-inventory.npy").read_bytes()
                ).hexdigest(),
            )

    def select(self, loop, stock, race):
        if self.source is None or loop >= self.expires:
            descriptor = [
                loop / 22.4,
                stock.get("unit:SCV", 0),
                stock.get("unit:CommandCenter", 0),
            ]
            indices = np.array(
                [
                    i
                    for i, r in enumerate(self.refs)
                    if race == "unknown" or self.races[r["game"]] == race
                ]
            )
            distances = np.sum(
                (
                    self.descriptor[indices] / self.scale
                    - np.array(descriptor) / self.scale
                )
                ** 2,
                axis=1,
            )
            index = int(indices[np.argmin(distances)])
            distance = float(np.sqrt(distances.min()))
            supported = distance <= self.thresholds[race]
            self.expires = loop + 1008
            self.target = {
                n: int(v)
                for n, v in zip(self.names, self.targets[index], strict=True)
                if v > 0
            }
            self.source = dict(
                **self.refs[index],
                future_loop=self.refs[index]["loop"] + 1008,
                selected_at=loop,
                expires=self.expires,
                descriptor=descriptor,
                selected_race=race,
                distance=distance,
                supported=supported,
                inventory_sha256=self.checksum,
            )
        return dict(self.target) if self.source["supported"] else {}, dict(self.source)


class InventoryIntents(ProductionIntents):
    def plan(self, deficits, queued, loop):
        for ticket, item in list(self.intents.items()):
            if ticket not in self.pending and deficits.get(
                item["goal"], 0
            ) <= queued.get(item["goal"], 0):
                del self.intents[ticket]
                self.events.append(
                    dict(event="retired", ticket=ticket, goal=item["goal"], loop=loop)
                )
        # Absolute stocks already account for produced units. Recent fulfilments
        # are a rate quota and must not suppress still-unsatisfied stock targets.
        self.recent.clear()
        super().plan(deficits, queued, loop)


def inventory_queued(state, goals, catalog, unit_names):
    # Remembered foundations count in own stock, but remembered orders are stale.
    missing = {u["tag"]: dict(u, orders=[]) for u in state.get("owned_memory", [])}
    for u in state["units"]:
        missing.pop(u["tag"], None)
    return queued_work(
        dict(state, units=state["units"] + list(missing.values())),
        goals,
        catalog,
        unit_names,
    )
