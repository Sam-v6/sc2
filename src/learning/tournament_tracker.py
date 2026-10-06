"""Causal own-unit deaths/upgrades and neutral identities from replay trackers."""


class CausalTracker:
    def __init__(self, events, player, catalog):
        self.events = iter(events)
        self.pending = next(self.events, None)
        self.player = player
        self.loop = -1
        self.owners = {}
        self.own_types = {}
        self.neutral_types = {}
        self.upgrades = set()
        self.unmapped_upgrades = set()
        self.units = {u["name"]: u["unit_id"] for u in catalog["units"]}
        self.upgrade_ids = {u["name"]: u["upgrade_id"] for u in catalog["upgrades"]}

    def advance(self, loop):
        """Expose tracker effects strictly before the pre-effect decision loop."""
        if loop < self.loop:
            raise ValueError("Tracker cannot move backward")
        deaths = set()
        while self.pending is not None and self.pending["_gameloop"] < loop:
            event = self.pending
            if event["_gameloop"] < self.loop:
                raise ValueError("Tracker events must be chronological")
            self.loop = event["_gameloop"]
            kind = event["_event"].rsplit(".", 1)[-1]
            if kind == "SUpgradeEvent" and event["m_playerId"] == self.player:
                name = event["m_upgradeTypeName"].decode()
                if name in self.upgrade_ids and event["m_count"] > 0:
                    self.upgrades.add(self.upgrade_ids[name])
                elif name not in self.upgrade_ids:
                    self.unmapped_upgrades.add(name)
            if "m_unitTagIndex" in event:
                tag = (event["m_unitTagIndex"] << 18) | event["m_unitTagRecycle"]
                if kind in (
                    "SUnitBornEvent",
                    "SUnitInitEvent",
                    "SUnitOwnerChangeEvent",
                ):
                    self.owners[tag] = event["m_upkeepPlayerId"]
                    if self.owners[tag] != self.player:
                        self.own_types.pop(tag, None)
                if kind in ("SUnitBornEvent", "SUnitInitEvent", "SUnitTypeChangeEvent"):
                    name = event["m_unitTypeName"].decode()
                    unit_type = self.units.get(name)
                    if self.owners.get(tag) == self.player:
                        self.own_types[tag] = unit_type
                    elif self.owners.get(tag) == 0:
                        self.neutral_types[tag] = unit_type
                if kind == "SUnitDiedEvent":
                    if self.owners.get(tag) == self.player:
                        deaths.add(tag)
                    self.owners.pop(tag, None)
                    self.own_types.pop(tag, None)
                    self.neutral_types.pop(tag, None)
            self.pending = next(self.events, None)
        self.loop = loop
        return deaths
