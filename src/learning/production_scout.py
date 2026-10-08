"""Protected worker scout transferred from the verified scripted baseline."""

import math
from src.bots.terran_primitives import changes_order
from src.learning.gameplay import Command


class WorkerScout:
    def __init__(self):
        self.tag = None
        self.sent = False
        self.deadline = None
        self.protected = set()
        self.events = []

    def update(self, state, claimed, enemy_start, home):
        loop = state["game_loop"]
        own = [u for u in state["units"] if u["alliance"] == 1]
        self.events = []
        self.protected = set()
        if not self.sent and 75 * 22.4 < loop < 135 * 22.4:
            ready = any(
                u["unit_type"] == 21 and u.get("build_progress", 1) == 1 for u in own
            )
            workers = [
                u
                for u in own
                if u["unit_type"] == 45
                and u["tag"] not in claimed
                and (
                    not u.get("orders")
                    or all(o["ability_id"] in (295, 3666) for o in u["orders"])
                )
            ]
            if ready and workers:
                worker = min(
                    workers,
                    key=lambda u: (math.dist(u["position"][:2], home), u["tag"]),
                )
                self.tag, self.sent = worker["tag"], True
                self.deadline = loop + 1344
                self.events.append(dict(event="selected", tag=self.tag, loop=loop))
        if self.tag is None:
            return []
        worker = next((u for u in own if u["tag"] == self.tag), None)
        remembered = any(u["tag"] == self.tag for u in state.get("owned_memory", []))
        if self.tag in claimed or (worker is None and not remembered):
            self.events.append(
                dict(
                    event="claimed" if self.tag in claimed else "lost",
                    tag=self.tag,
                    loop=loop,
                )
            )
            self.tag = None
            return []
        self.protected.add(self.tag)
        if worker is None:
            if loop >= self.deadline:
                self.events.append(
                    dict(event="deadline_unobserved", tag=self.tag, loop=loop)
                )
                self.tag = None
            return []
        if (
            worker.get("health", 0) > 0.6 * worker.get("health_max", 45)
            and loop < self.deadline
        ):
            command = Command(16, (self.tag,), target_point=enemy_start)
        else:
            bases = [
                u
                for u in own
                if u["unit_type"] in (18, 132, 130)
                and u.get("build_progress", 1) == 1
                and not u.get("is_flying")
            ]
            patches = [
                u
                for u in state["units"]
                if u["alliance"] == 3
                and u.get("mineral_contents", 0) > 0
                and any(
                    math.dist(u["position"][:2], b["position"][:2]) < 10 for b in bases
                )
            ]
            target = (
                min(
                    patches,
                    key=lambda u: math.dist(u["position"][:2], worker["position"][:2]),
                )
                if patches
                else None
            )
            command = (
                Command(295, (self.tag,), target_unit=target["tag"])
                if target
                else Command(16, (self.tag,), target_point=home)
            )
            self.events.append(
                dict(
                    event="return",
                    tag=self.tag,
                    loop=loop,
                    reason="deadline" if loop >= self.deadline else "damaged",
                )
            )
            self.tag = None
        return [command] if changes_order(worker, command) else []
