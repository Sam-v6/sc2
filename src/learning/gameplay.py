"""Raw gameplay commands and player-visible entities, shared by replays and play."""

import base64
from dataclasses import dataclass
import math
from google.protobuf.json_format import MessageToDict
from google.protobuf.descriptor import FieldDescriptor
from s2clientprotocol import sc2api_pb2 as pb, raw_pb2 as raw


def protocol_dict(message):
    row = MessageToDict(
        message, preserving_proto_field_name=True, use_integers_for_enums=True
    )
    for field, value in message.ListFields():
        if field.type == FieldDescriptor.TYPE_MESSAGE:
            row[field.name] = (
                [protocol_dict(item) for item in value]
                if field.label == FieldDescriptor.LABEL_REPEATED
                else protocol_dict(value)
            )
        elif field.type in (
            FieldDescriptor.TYPE_UINT64,
            FieldDescriptor.TYPE_INT64,
            FieldDescriptor.TYPE_FIXED64,
            FieldDescriptor.TYPE_SFIXED64,
            FieldDescriptor.TYPE_SINT64,
        ):
            row[field.name] = (
                list(value) if field.label == FieldDescriptor.LABEL_REPEATED else value
            )
    return row


@dataclass(frozen=True)
class Command:
    ability: int
    units: tuple[int, ...]
    target_unit: int | None = None
    target_point: tuple[float, float] | None = None
    queue: bool = False
    autocast: bool = False

    def to_proto(self):
        if (
            self.ability <= 0
            or not self.units
            or any(tag <= 0 for tag in self.units)
            or (self.target_unit is not None and self.target_point is not None)
        ):
            raise ValueError("A command needs an ability, units and at most one target")
        if self.target_unit is not None and self.target_unit <= 0:
            raise ValueError("Target unit tags must be positive")
        if self.target_point is not None and (
            len(self.target_point) != 2
            or not all(math.isfinite(x) for x in self.target_point)
        ):
            raise ValueError("Target positions must be finite coordinates")
        if self.autocast:
            if (
                self.target_unit is not None
                or self.target_point is not None
                or self.queue
            ):
                raise ValueError("Autocast toggles do not take targets or queues")
            action = raw.ActionRaw(
                toggle_autocast=raw.ActionRawToggleAutocast(
                    ability_id=self.ability, unit_tags=self.units
                )
            )
        else:
            command = raw.ActionRawUnitCommand(
                ability_id=self.ability, unit_tags=self.units, queue_command=self.queue
            )
            if self.target_unit is not None:
                command.target_unit_tag = self.target_unit
            if self.target_point is not None:
                command.target_world_space_pos.x, command.target_world_space_pos.y = (
                    self.target_point
                )
            action = raw.ActionRaw(unit_command=command)
        return pb.Action(action_raw=action)

    @classmethod
    def from_proto(cls, action):
        if action.action_raw.HasField("unit_command"):
            c = action.action_raw.unit_command
            result = cls(
                c.ability_id,
                tuple(c.unit_tags),
                c.target_unit_tag if c.HasField("target_unit_tag") else None,
                (c.target_world_space_pos.x, c.target_world_space_pos.y)
                if c.HasField("target_world_space_pos")
                else None,
                c.queue_command,
            )
        elif action.action_raw.HasField("toggle_autocast"):
            c = action.action_raw.toggle_autocast
            result = cls(c.ability_id, tuple(c.unit_tags), autocast=True)
        else:
            raise ValueError("Action is not a raw gameplay command")
        result.to_proto()
        return result

    def as_dict(self):
        return {
            "ability": self.ability,
            "units": list(self.units),
            "target_unit": self.target_unit,
            "target_point": list(self.target_point)
            if self.target_point is not None
            else None,
            "queue": self.queue,
            "autocast": self.autocast,
        }


def image_dict(image):
    return {
        "width": image.size.x,
        "height": image.size.y,
        "bits_per_pixel": image.bits_per_pixel,
        "data": base64.b64encode(image.data).decode("ascii"),
    }


class PlayerView:
    """No camera crop; enemy memory contains previously known identity and position."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.known = {}
        self.owned = {}
        self.recent_commands = []

    def record_commands(self, commands, loop):
        self.recent_commands.extend(
            {"game_loop": loop, **command.as_dict()} for command in commands
        )
        self.recent_commands = self.recent_commands[-32:]

    def observe(self, packet):
        observation = packet.observation
        loop = observation.game_loop
        units, visible_enemies, radar_contacts = [], set(), []
        for action in packet.actions:
            if action.action_raw.HasField("unit_command") or action.action_raw.HasField(
                "toggle_autocast"
            ):
                self.record_commands([Command.from_proto(action)], action.game_loop)
        for unit in observation.raw_data.units:
            if unit.is_blip:
                radar_contacts.append(
                    {"position": [unit.pos.x, unit.pos.y, unit.pos.z]}
                )
                continue
            if unit.display_type == raw.Hidden:
                continue
            if unit.alliance == raw.Enemy:
                if unit.display_type == raw.Visible:
                    self.known[unit.tag] = {
                        "tag": unit.tag,
                        "unit_type": unit.unit_type,
                        "position": [unit.pos.x, unit.pos.y, unit.pos.z],
                        "last_seen_loop": loop,
                    }
                    visible_enemies.add(unit.tag)
                elif unit.tag not in self.known:
                    self.known[unit.tag] = {
                        "tag": unit.tag,
                        "unit_type": unit.unit_type,
                        "position": [unit.pos.x, unit.pos.y, unit.pos.z],
                        "last_seen_loop": None,
                    }
            if unit.display_type != raw.Visible:
                continue
            if unit.alliance == raw.Self:
                self.owned[unit.tag] = {
                    "tag": unit.tag,
                    "unit_type": unit.unit_type,
                    "alliance": raw.Self,
                    "position": [unit.pos.x, unit.pos.y, unit.pos.z],
                    "last_seen_loop": loop,
                    "observed": False,
                }
            row = protocol_dict(unit)
            row["tag"] = unit.tag
            row["position"] = [unit.pos.x, unit.pos.y, unit.pos.z]
            # UI selection and camera position are neither sensory limits nor inputs.
            for name in ("pos", "is_selected", "is_on_screen"):
                row.pop(name, None)
            units.append(row)
        for tag in observation.raw_data.event.dead_units:
            self.known.pop(tag, None)
            self.owned.pop(tag, None)
        current_tags = {unit["tag"] for unit in units}
        return {
            "schema": 1,
            "game_loop": loop,
            "player": protocol_dict(observation.player_common),
            "units": sorted(units, key=lambda u: u["tag"]),
            "owned_memory": [
                dict(row)
                for tag, row in sorted(self.owned.items())
                if tag not in current_tags
            ],
            "radar_contacts": radar_contacts,
            "recent_commands": list(self.recent_commands),
            "memory": [
                dict(row)
                for tag, row in sorted(self.known.items())
                if tag not in visible_enemies
            ],
            "upgrades": list(observation.raw_data.player.upgrade_ids),
            "effects": [
                protocol_dict(effect) for effect in observation.raw_data.effects
            ],
            "map": {
                name: image_dict(getattr(observation.raw_data.map_state, name))
                for name in ("visibility", "creep")
            },
            "action_errors": [protocol_dict(error) for error in packet.action_errors],
        }
