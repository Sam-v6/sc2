"""Lossless gameplay labels aligned to observations strictly before command time."""

from collections import Counter
from src.learning.gameplay import Command, PlayerView


class ReplayExamples:
    def __init__(self):
        self.view = PlayerView()
        self.history = {}
        self.counts = Counter()
        self.last_loop = None

    def push(self, packet):
        loop = packet.observation.game_loop
        if self.last_loop is not None and loop != self.last_loop + 1:
            raise ValueError(
                "Replay extraction requires consecutive single-loop observations"
            )
        groups = {}
        for action in packet.actions:
            if [field.name for field, _ in action.ListFields()] == ["game_loop"]:
                self.counts["empty"] += 1
                continue
            if (
                action.action_raw.HasField("camera_move")
                or action.action_feature_layer.HasField("camera_move")
                or action.HasField("action_ui")
            ):
                self.counts["ui"] += 1
                continue
            command = Command.from_proto(action)
            if (
                not action.HasField("game_loop")
                or action.game_loop - 1 not in self.history
            ):
                raise ValueError(
                    "No observation strictly before the recorded command loop"
                )
            groups.setdefault(action.game_loop, []).append(command.as_dict())
            self.counts["gameplay"] += 1
        rows = [
            {
                "observation": self.history[issued - 1],
                "action_loop": issued,
                "received_loop": loop,
                "commands": commands,
            }
            for issued, commands in sorted(groups.items())
        ]
        self.history[loop] = self.view.observe(packet)
        self.history = {t: state for t, state in self.history.items() if t >= loop - 3}
        self.last_loop = loop
        self.counts["observations"] += 1
        return rows


def label_timing(rows):
    """Merge same-loop bursts and label the delay to the next issued command."""
    pending = None
    for row in rows:
        row = dict(row, commands=list(row["commands"]))
        if pending is not None:
            gap = row["action_loop"] - pending["action_loop"]
            if gap < 0:
                raise ValueError("Replay command times moved backwards")
            if gap == 0:
                pending["commands"].extend(row["commands"])
                continue
            yield dict(pending, next_action_delay=gap)
        pending = row
    if pending is not None:
        yield dict(pending, next_action_delay=None)
