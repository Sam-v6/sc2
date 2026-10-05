import unittest
from src.learning.gameplay import Command

try:
    from src.learning.sandbox import attack_commands, micro_score
except ImportError:
    attack_commands = micro_score = None


class SandboxTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(attack_commands, "Micro sandbox control is missing")

    def test_each_unit_can_target_a_different_visible_fight(self):
        state = {
            "units": [
                {"tag": 1, "alliance": 1, "position": [0.0, 0.0, 0.0]},
                {"tag": 2, "alliance": 1, "position": [100.0, 100.0, 0.0]},
                {"tag": 3, "alliance": 4, "position": [1.0, 0.0, 0.0]},
                {"tag": 4, "alliance": 4, "position": [99.0, 100.0, 0.0]},
            ],
            "memory": [{"tag": 5, "position": [0.01, 0.0, 0.0]}],
        }
        commands = attack_commands(state)
        self.assertEqual(
            commands,
            [Command(23, (1,), target_unit=3), Command(23, (2,), target_unit=4)],
        )
        state["units"] = state["units"][:2]
        self.assertEqual(attack_commands(state), [])

    def test_damage_reward_uses_observed_score_not_hidden_enemy_health(self):
        from s2clientprotocol import sc2api_pb2 as pb

        packet = pb.ResponseObservation()
        packet.observation.score.score_details.total_damage_dealt.life = 30
        packet.observation.score.score_details.total_damage_taken.life = 10
        packet.observation.score.score_details.killed_value_units = 50
        self.assertEqual(
            micro_score(packet),
            {
                "damage_dealt": 30.0,
                "damage_taken": 10.0,
                "killed_value": 50.0,
                "score": 0,
            },
        )
