"""Contracts that protect command fidelity and the player's information boundary."""

import unittest
from s2clientprotocol import sc2api_pb2 as pb, raw_pb2 as raw, common_pb2 as common

try:
    from src.learning.gameplay import Command, PlayerView
except ImportError:
    Command = PlayerView = None


class GameplayTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(Command, "The shared raw gameplay interface is missing")

    def test_legacy_visible_flag_cannot_override_visibility_grid_or_refresh_memory(self):
        packet = pb.ResponseObservation()
        packet.observation.game_loop = 10
        packet.observation.raw_data.map_state.visibility.CopyFrom(
            common.ImageData(bits_per_pixel=8, size={"x": 2, "y": 1}, data=b"\x02\x00")
        )
        enemy = packet.observation.raw_data.units.add(
            tag=2, alliance=raw.Enemy, display_type=raw.Visible, unit_type=21,
            health=100, pos={"x": 0, "y": 0})
        view = PlayerView()
        self.assertEqual([u['tag'] for u in view.observe(packet)['units']], [2])
        packet.observation.game_loop = 20
        enemy.pos.x = 1
        enemy.health = 999
        packet.observation.raw_data.units.add(
            tag=3, alliance=raw.Enemy, display_type=raw.Visible, unit_type=21,
            health=999, pos={"x": 1, "y": 0})
        state = view.observe(packet)
        self.assertEqual(state['units'], [])
        self.assertEqual([u['tag'] for u in state['memory']], [2])
        self.assertEqual(state['memory'][0]['position'], [0.0, 0.0, 0.0])
        self.assertEqual(state['memory'][0]['last_seen_loop'], 10)
        self.assertNotIn('health', state['memory'][0])

    def test_commands_preserve_multiple_units_target_queue_and_autocast(self):
        command = Command(ability=23, units=(101, 102), target_unit=201, queue=True)
        action = command.to_proto()
        self.assertEqual(list(action.action_raw.unit_command.unit_tags), [101, 102])
        self.assertEqual(action.action_raw.unit_command.target_unit_tag, 201)
        self.assertTrue(action.action_raw.unit_command.queue_command)
        self.assertEqual(Command.from_proto(action), command)
        point = Command(ability=16, units=(101,), target_point=(23.5, 44.25))
        self.assertEqual(Command.from_proto(point.to_proto()), point)
        toggle = Command(ability=316, units=(101,), autocast=True)
        self.assertEqual(Command.from_proto(toggle.to_proto()), toggle)

    def test_ambiguous_targets_and_camera_commands_are_not_training_waits(self):
        with self.assertRaises(ValueError):
            Command(23, (1,), target_unit=2, target_point=(1.0, 2.0)).to_proto()
        with self.assertRaises(ValueError):
            Command(16, (), target_point=(1.0, 2.0)).to_proto()
        with self.assertRaises(ValueError):
            Command(16, (1,), target_point=(float("nan"), 2.0)).to_proto()
        with self.assertRaises(ValueError):
            Command.from_proto(
                pb.Action(
                    action_raw=raw.ActionRaw(camera_move=raw.ActionRawCameraMove())
                )
            )

    def test_hidden_units_and_snapshot_health_cannot_enter_actor_view(self):
        packet = pb.ResponseObservation()
        packet.observation.game_loop = 10
        units = packet.observation.raw_data.units
        units.add(
            tag=1, alliance=raw.Self, display_type=raw.Visible, unit_type=48, health=45
        )
        units.add(
            tag=2,
            alliance=raw.Enemy,
            display_type=raw.Visible,
            unit_type=105,
            health=35,
            pos={"x": 20, "y": 30},
        )
        units.add(
            tag=3,
            alliance=raw.Enemy,
            display_type=raw.Hidden,
            unit_type=105,
            health=999,
        )
        units.add(
            tag=4,
            alliance=raw.Enemy,
            display_type=raw.Snapshot,
            unit_type=21,
            health=999,
            pos={"x": 40, "y": 50},
        )
        view = PlayerView()
        state = view.observe(packet)
        self.assertEqual([u["tag"] for u in state["units"]], [1, 2])
        self.assertEqual([u["tag"] for u in state["memory"]], [4])
        self.assertNotIn("health", state["memory"][0])
        self.assertIsNone(state["memory"][0]["last_seen_loop"])
        del units[:]
        packet.observation.game_loop = 20
        units.add(
            tag=2,
            alliance=raw.Enemy,
            display_type=raw.Snapshot,
            unit_type=105,
            health=1000,
            pos={"x": 99, "y": 99},
        )
        state = view.observe(packet)
        remembered = next(u for u in state["memory"] if u["tag"] == 2)
        self.assertEqual(remembered["last_seen_loop"], 10)
        self.assertEqual(remembered["position"], [20.0, 30.0, 0.0])
        self.assertNotIn("health", remembered)
        view.reset()
        self.assertEqual(view.observe(pb.ResponseObservation())["memory"], [])

    def test_full_map_entities_orders_and_resources_do_not_depend_on_camera(self):
        packet = pb.ResponseObservation()
        packet.observation.player_common.minerals = 125
        for tag, x in [(1, 2.0), (2, 190.0)]:
            u = packet.observation.raw_data.units.add(
                tag=tag,
                alliance=raw.Self,
                display_type=raw.Visible,
                unit_type=48,
                health=45,
                pos={"x": x, "y": 10},
                weapon_cooldown=7,
            )
            u.orders.add(ability_id=23, target_unit_tag=9, progress=0.5)
        packet.observation.raw_data.map_state.visibility.CopyFrom(
            common.ImageData(bits_per_pixel=8, size={"x": 2, "y": 1}, data=b"\x01\x02")
        )
        state = PlayerView().observe(packet)
        self.assertEqual(state["player"]["minerals"], 125)
        self.assertEqual([u["position"][0] for u in state["units"]], [2.0, 190.0])
        self.assertEqual(state["units"][1]["orders"][0]["target_unit_tag"], 9)
        self.assertEqual(state["units"][0]["weapon_cooldown"], 7)
        self.assertEqual(state["map"]["visibility"]["data"], "AQI=")

    def test_recent_commands_and_radar_do_not_reveal_unit_identity(self):
        view = PlayerView()
        self.assertTrue(hasattr(view, "record_commands"))
        view.record_commands([Command(16, (1,), target_point=(5.0, 6.0))], 9)
        packet = pb.ResponseObservation()
        packet.observation.game_loop = 10
        packet.observation.raw_data.units.add(
            tag=55,
            alliance=raw.Enemy,
            display_type=raw.Visible,
            is_blip=True,
            unit_type=105,
            health=999,
            pos={"x": 40.0, "y": 50.0},
        )
        state = view.observe(packet)
        self.assertEqual(state["recent_commands"][0]["game_loop"], 9)
        self.assertEqual(state["radar_contacts"], [{"position": [40.0, 50.0, 0.0]}])
        self.assertEqual(state["units"], [])
        self.assertEqual(state["memory"], [])
        view.reset()
        self.assertEqual(view.observe(pb.ResponseObservation())["recent_commands"], [])

    def test_own_units_missing_from_raw_view_remain_known_without_current_health(self):
        packet = pb.ResponseObservation()
        packet.observation.game_loop = 10
        packet.observation.raw_data.units.add(
            tag=1,
            alliance=raw.Self,
            display_type=raw.Visible,
            unit_type=45,
            health=45,
            pos={"x": 4.0, "y": 5.0},
        )
        view = PlayerView()
        view.observe(packet)
        del packet.observation.raw_data.units[:]
        packet.observation.game_loop = 20
        memory = view.observe(packet).get("owned_memory")
        self.assertIsNotNone(memory)
        self.assertEqual(memory[0]["tag"], 1)
        self.assertEqual(memory[0]["last_seen_loop"], 10)
        self.assertNotIn("health", memory[0])
        packet.observation.raw_data.event.dead_units.append(1)
        self.assertEqual(view.observe(packet)["owned_memory"], [])
