"""Independent wire fixtures for the published 2024 Windows tournament format."""

import struct
import unittest

import numpy as np


def vector(payload, count):
    return struct.pack("<Q", count) + payload


def image(value=0, packed=False):
    size = 2048 if packed else 16384
    return struct.pack("<iiQ", 128, 128, size) + bytes([value]) * size


def block(neutral=False, bad_range=False, bad_field=False, zero_range=False):
    # Wire field order comes from the May 2024 UnitSoA/NeutralUnitSoA schema.
    fields = (
        [
            ("id", "Q"),
            ("unitType", "i"),
            ("observation", "B"),
            ("health", "f"),
            ("health_max", "f"),
            ("pos", "3f"),
            ("heading", "f"),
            ("radius", "f"),
            ("contents", "H"),
        ]
        if neutral
        else [("id", "Q"), ("unitType", "i"), ("observation", "B"), ("alliance", "B")]
        + [
            (k, "f")
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
            (k, "b")
            for k in ("cargo", "cargo_max", "assigned_harvesters", "ideal_harvesters")
        ]
        + [("weapon_cooldown", "f"), ("tgtId", "Q"), ("cloak_state", "B")]
        + [
            (k, "b")
            for k in ("is_blip", "is_flying", "is_burrowed", "is_powered", "in_cargo")
        ]
        + [("pos", "3f")]
        + [(f"order{i}", "ifQii") for i in range(4)]
        + [
            ("buff0", "i"),
            ("buff1", "i"),
            ("heading", "f"),
            ("radius", "f"),
            ("build_progress", "f"),
            ("add_on_tag", "B"),
        ]
    )
    payload = b""
    for name, fmt in fields:
        values = {
            "id": (2**40 + 7,),
            "unitType": (18,),
            "observation": (2,),
            "alliance": (4,),
            "pos": (11.5, 20.25, 8.0),
            "order0": (524, 0.25, 2**40 + 9, 11, 20),
        }
        value = values.get(name)
        if value is None:
            value = (0, 0.0, 0, 0, 0) if fmt == "ifQii" else (0,)
        encoded = struct.pack("<" + fmt, *value)
        payload += vector(
            encoded * (2 if bad_field and name == "id" else 1),
            2 if bad_field and name == "id" else 1,
        )
    return (
        payload
        + (
            vector(struct.pack("<IIII", 0, 0, 0, 1), 2)
            if zero_range
            else vector(struct.pack("<II", 2 if bad_range else 0, 1), 1)
        )
        + struct.pack("<I", 2)
    )


def record(
    bad_range=False, bad_field=False, bad_scalar=False, target_type=2, zero_range=False
):
    header = vector(b"a" * 32, 32) + vector(b"4.10.2.76052", 12)
    header += struct.pack("<IIbbiiii", 1, 100, 0, 0, 0, 412, 200, 184) + image(17)
    payload = header + vector(struct.pack("<II", 12, 18), 2)
    for values in ((50, 55), (0, 0), (15, 15), (0, 0), (12, 12)):
        payload += vector(struct.pack("<HH", *values), 3 if bad_scalar else 2)
    payload += vector(bytes(2 * 88), 2)
    for packed in (False, True, False, False, True, True):
        payload += (
            struct.pack("<Q", 2)
            + image(128 if packed else 2, packed)
            + image(0, packed)
        )
    # Frame0 has point and unit-target commands; frame1 is a terminal observation.
    actions = struct.pack("<Q", 2)
    actions += vector(struct.pack("<Q", 2**40 + 7), 1) + struct.pack(
        "<iiii", 16, target_type, 33, 44
    )
    actions += vector(struct.pack("<Q", 2**40 + 7), 1) + struct.pack(
        "<iiQ", 1, 1, 2**40 + 9
    )
    payload += struct.pack("<Q", 2) + actions + struct.pack("<Q", 0)
    return (
        payload
        + block(bad_range=bad_range, bad_field=bad_field, zero_range=zero_range)
        + block(neutral=True)
    )


class TournamentRecordTests(unittest.TestCase):
    def decode(self, data):
        from src.learning.tournament_record import decode_record

        return decode_record(data)

    def test_preserves_wire_actions_and_visibility_without_inventing_queue(self):
        r = self.decode(record())
        self.assertEqual(r["header"]["width"], 200)
        self.assertEqual(r["steps"]["game_loop"].tolist(), [12, 18])
        self.assertEqual(r["steps"]["minerals"].tolist(), [50, 55])
        command = r["actions"][0][0]
        self.assertEqual(command["units"], (2**40 + 7,))
        self.assertEqual(command["target_point"], (33, 44))
        self.assertEqual(r["actions"][0][1]["target_unit"], 2**40 + 9)
        self.assertNotIn("queue", command)
        self.assertNotIn("autocast", command)
        self.assertEqual(r["units"]["fields"]["observation"].tolist(), [2])
        self.assertEqual(r["units"]["step"].tolist(), [0])
        self.assertEqual(r["units"]["fields"]["order0"]["ability"].tolist(), [524])
        self.assertEqual(r["units"]["fields"]["pos"].tolist(), [[11.5, 20.25, 8.0]])
        self.assertEqual(r["images"]["visibility"].shape, (2, 128, 128))
        np.testing.assert_array_equal(
            r["images"]["creep"][0, 0, :9], [1, 0, 0, 0, 0, 0, 0, 0, 1]
        )

    def test_rejects_truncation_trailing_bytes_and_out_of_range_unit_step(self):
        for data in (record()[:-1], record() + b"x", record(bad_range=True)):
            with self.subTest(length=len(data)), self.assertRaises(ValueError):
                self.decode(data)

    def test_rejects_unbounded_vector_length_before_allocation(self):
        with self.assertRaises(ValueError):
            self.decode(struct.pack("<Q", 2**63))

    def test_rejects_inconsistent_scalar_and_unit_fields_and_unknown_target(self):
        for data in (
            record(bad_scalar=True),
            record(bad_field=True),
            record(target_type=9),
        ):
            with self.subTest(length=len(data)), self.assertRaises(ValueError):
                self.decode(data)

    def test_rejects_zero_length_unit_ranges_before_expanding_them(self):
        with self.assertRaisesRegex(ValueError, "ranges"):
            self.decode(record(zero_range=True))
