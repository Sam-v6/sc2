"""Decode the published May 2024 Windows sc2-serializer Action record.

This is a wire decoder, not a native demonstration importer. Queue flags,
autocast distinction and precise point coordinates are absent from this format.
Header map dimensions may be stale; reconcile with the original replay map.
"""

import struct

import numpy as np


ORDER = np.dtype(
    [
        ("ability", "<i4"),
        ("progress", "<f4"),
        ("target_unit", "<u8"),
        ("x", "<i4"),
        ("y", "<i4"),
    ]
)
UNIT_FIELDS = (
    [("id", "<u8"), ("unitType", "<i4"), ("observation", "u1"), ("alliance", "u1")]
    + [
        (k, "<f4")
        for k in (
            "health",
            "health_max",
            "shield",
            "shield_max",
            "energy",
            "energy_max",
        )
    ]
    + [
        (k, "i1")
        for k in ("cargo", "cargo_max", "assigned_harvesters", "ideal_harvesters")
    ]
    + [("weapon_cooldown", "<f4"), ("tgtId", "<u8"), ("cloak_state", "u1")]
    + [
        (k, "i1")
        for k in ("is_blip", "is_flying", "is_burrowed", "is_powered", "in_cargo")
    ]
    + [("pos", ("<f4", 3))]
    + [(f"order{i}", ORDER) for i in range(4)]
    + [("buff0", "<i4"), ("buff1", "<i4")]
    + [(k, "<f4") for k in ("heading", "radius", "build_progress")]
    + [("add_on_tag", "u1")]
)
NEUTRAL_FIELDS = [
    ("id", "<u8"),
    ("unitType", "<i4"),
    ("observation", "u1"),
    ("health", "<f4"),
    ("health_max", "<f4"),
    ("pos", ("<f4", 3)),
    ("heading", "<f4"),
    ("radius", "<f4"),
    ("contents", "<u2"),
]


class Reader:
    def __init__(self, data):
        self.data = memoryview(data)
        self.offset = 0

    def read(self, size):
        if size < 0 or size > len(self.data) - self.offset:
            raise ValueError("Truncated tournament record")
        result = self.data[self.offset : self.offset + size]
        self.offset += size
        return result

    def unpack(self, fmt):
        return struct.unpack(fmt, self.read(struct.calcsize(fmt)))

    def count(self, minimum_bytes):
        count = self.unpack("<Q")[0]
        if count > (len(self.data) - self.offset) // minimum_bytes:
            raise ValueError("Tournament vector exceeds remaining record")
        return count

    def vector(self, dtype):
        dtype = np.dtype(dtype)
        count = self.count(dtype.itemsize)
        return np.frombuffer(self.read(count * dtype.itemsize), dtype=dtype)

    def string(self):
        return self.vector("u1").tobytes().decode("utf-8")

    def image(self, packed=False):
        height, width = self.unpack("<ii")
        if (height, width) != (128, 128):
            raise ValueError("Unsupported tournament minimap dimensions")
        pixels = self.vector("u1")
        expected = height * width // (8 if packed else 1)
        if len(pixels) != expected:
            raise ValueError("Tournament minimap byte count mismatch")
        if packed:
            pixels = np.unpackbits(pixels, bitorder="big")
        return pixels.reshape(height, width)

    def units(self, fields, nsteps):
        values = {name: self.vector(dtype) for name, dtype in fields}
        count = len(values["id"])
        if any(len(v) != count for v in values.values()):
            raise ValueError("Tournament unit field lengths disagree")
        ranges = self.vector(("<u4", 2))
        maxstep = self.unpack("<I")[0]
        if (
            maxstep != nsteps
            or np.any(ranges[:, 1] == 0)
            or int(ranges[:, 1].sum()) != count
            or np.any(ranges.astype(np.uint64).sum(axis=1) > nsteps)
        ):
            raise ValueError("Tournament unit observation ranges are invalid")
        steps = (
            np.concatenate(
                [
                    np.arange(start, int(start) + int(length), dtype=np.uint32)
                    for start, length in ranges
                ]
            )
            if len(ranges)
            else np.empty(0, dtype=np.uint32)
        )
        return {"fields": values, "step": steps}

    def actions(self):
        commands = []
        for _ in range(self.count(24)):
            units = tuple(map(int, self.vector("<u8")))
            ability, target_type = self.unpack("<ii")
            target = self.read(8)
            command = {"ability": ability, "units": units, "target_type": target_type}
            if target_type == 1:
                command["target_unit"] = struct.unpack("<Q", target)[0]
            elif target_type == 2:
                command["target_point"] = struct.unpack("<ii", target)
            elif target_type != 0:
                raise ValueError("Unknown tournament command target type")
            commands.append(command)
        return commands


def decode_record(data):
    """Decode one already-decompressed record; retain unknowns for reconciliation."""
    if len(data) > 256 * 1024 * 1024:
        raise ValueError("Tournament record exceeds decoded size limit")
    reader = Reader(data)
    header = {"hash": reader.string(), "version": reader.string()}
    header.update(zip(("player", "duration"), reader.unpack("<II")))
    header.update(
        zip(
            ("race", "result", "mmr", "apm", "width", "height"),
            reader.unpack("<bbiiii"),
        )
    )
    header["height_map"] = reader.image()
    steps = {"game_loop": reader.vector("<u4")}
    nsteps = len(steps["game_loop"])
    if not nsteps or np.any(steps["game_loop"][1:] < steps["game_loop"][:-1]):
        raise ValueError("Tournament observation loops must be ordered and nonempty")
    for name in ("minerals", "gas", "cap", "army", "workers"):
        steps[name] = reader.vector("<u2")
    steps["score"] = reader.vector(("<f4", 22))
    if any(len(v) != nsteps for v in steps.values()):
        raise ValueError("Tournament scalar observation lengths disagree")
    images = {}
    for name, packed in [
        ("visibility", False),
        ("creep", True),
        ("relative", False),
        ("alerts", False),
        ("buildable", True),
        ("pathable", True),
    ]:
        if reader.count(16) != nsteps:
            raise ValueError("Tournament image observation count mismatch")
        images[name] = np.stack([reader.image(packed) for _ in range(nsteps)])
    if reader.count(8) != nsteps:
        raise ValueError("Tournament action observation count mismatch")
    actions = [reader.actions() for _ in range(nsteps)]
    units = reader.units(UNIT_FIELDS, nsteps)
    neutral = reader.units(NEUTRAL_FIELDS, nsteps)
    if reader.offset != len(data):
        raise ValueError("Trailing bytes in tournament record")
    return {
        "header": header,
        "steps": steps,
        "images": images,
        "actions": actions,
        "units": units,
        "neutral": neutral,
    }
