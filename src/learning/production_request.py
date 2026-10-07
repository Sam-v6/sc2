"""Observe effects and delayed failures of one accepted production command."""

import math

from src.learning.production_execution import canonical


class ProductionRequest:
    def __init__(self, command, state, data):
        self.command = command
        self.loop = state["game_loop"]
        self.catalog = {row["ability_id"]: row for row in data["abilities"]}
        self.wanted = canonical(command.ability, self.catalog)
        self.initial_train_orders = (
            {
                unit["tag"]: sum(
                    canonical(order["ability_id"], self.catalog) == self.wanted
                    for order in unit.get("orders", [])
                )
                for unit in state["units"]
                if unit["tag"] in command.units
            }
            if self.catalog[command.ability]
            .get("friendly_name", "")
            .startswith("Train ")
            else {}
        )
        self.previous_progress = {
            unit["tag"]: unit["orders"][0].get("progress", 0)
            for unit in state["units"]
            if command.queue
            and unit["tag"] in self.initial_train_orders
            and len(unit.get("orders", [])) == 1
            and self.initial_train_orders[unit["tag"]] == 1
        }
        self.building = (
            self.catalog[command.ability].get("friendly_name", "").startswith("Build ")
        )
        self.products = {
            row["unit_id"]
            for row in data["units"]
            if row.get("ability_id") is not None
            and canonical(row["ability_id"], self.catalog) == self.wanted
        }
        self.products.update(
            row["unit_id"]
            for row in data["units"]
            if set(row.get("tech_alias", [])) & self.products
            or row.get("unit_alias") in self.products
        )
        self.existing = {
            unit["tag"] for unit in state["units"] if unit["alliance"] == 1
        }
        target = next(
            (unit for unit in state["units"] if unit["tag"] == command.target_unit),
            None,
        )
        self.point = command.target_point or (
            tuple(target["position"][:2]) if target else None
        )
        if self.point is None and self.catalog[command.ability].get(
            "friendly_name", ""
        ).startswith(("Build TechLab", "Build Reactor")):
            actor = next(
                (unit for unit in state["units"] if unit["tag"] in command.units), None
            )
            if actor and "position" in actor:
                self.point = (actor["position"][0] + 2.5, actor["position"][1] - 0.5)

    def status(self, state):
        if state["game_loop"] <= self.loop:
            return "pending"
        if any(
            error["unit_tag"] in self.command.units
            and canonical(error["ability_id"], self.catalog) == self.wanted
            for error in state.get("action_errors", [])
        ):
            return "failed"
        own = [unit for unit in state["units"] if unit["alliance"] == 1]
        if self.building:
            if any(
                unit["tag"] not in self.existing
                and unit["unit_type"] in self.products
                and (
                    math.dist(unit["position"][:2], self.point) < 1
                    if self.point is not None
                    else any(
                        actor["tag"] in self.command.units
                        and actor.get("add_on_tag") == unit["tag"]
                        for actor in own
                    )
                )
                for unit in own
            ):
                return "started"
        elif any(
            unit["tag"] in self.command.units
            and sum(
                canonical(order["ability_id"], self.catalog) == self.wanted
                for order in unit.get("orders", [])
            )
            > self.initial_train_orders.get(unit["tag"], 0)
            or (
                unit["tag"] in self.command.units
                and unit["tag"] in self.previous_progress
                and len(unit.get("orders", [])) == 1
                and canonical(unit["orders"][0]["ability_id"], self.catalog)
                == self.wanted
                and unit["orders"][0].get("progress", 0)
                < self.previous_progress[unit["tag"]]
            )
            for unit in own
        ):
            return "started"
        if not set(self.command.units) & {unit["tag"] for unit in own}:
            return "actor_missing"
        return "pending"
