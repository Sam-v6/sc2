import unittest
import numpy as np

try:
    from src.learning.micro_policy import (
        candidates,
        MicroPolicy,
        update_distribution,
        episode_return,
    )
except ImportError:
    candidates = MicroPolicy = update_distribution = episode_return = None


class MicroPolicyTests(unittest.TestCase):
    def test_candidates_use_current_visible_entities_and_cooldown(self):
        self.assertIsNotNone(candidates)
        unit = {
            "tag": 1,
            "position": [10.0, 10.0, 0.0],
            "health": 45.0,
            "health_max": 45.0,
            "weapon_cooldown": 0.0,
        }
        enemies = [
            {
                "tag": 2,
                "position": [12.0, 10.0, 0.0],
                "health": 100.0,
                "health_max": 145.0,
            }
        ]
        commands, features = candidates(unit, enemies)
        self.assertEqual(commands[0].target_unit, 2)
        self.assertTrue(all(c.units == (1,) for c in commands))
        self.assertTrue(np.isfinite(features).all())
        _, cooldown = candidates(dict(unit, weapon_cooldown=15.0), enemies)
        self.assertFalse(np.array_equal(features, cooldown))
        self.assertEqual(candidates(unit, [])[0], [])

    def test_policy_weights_control_independent_decisions(self):
        self.assertIsNotNone(MicroPolicy)
        own = {
            "tag": 1,
            "alliance": 1,
            "position": [10.0, 10.0, 0.0],
            "health": 45.0,
            "health_max": 45.0,
        }
        enemy = {
            "tag": 2,
            "alliance": 4,
            "position": [12.0, 10.0, 0.0],
            "health": 100.0,
            "health_max": 145.0,
        }
        weights = np.zeros(MicroPolicy.dimension)
        weights[0] = 5.0
        policy = MicroPolicy(weights)
        self.assertEqual(policy.commands({"units": [own, enemy]})[0].ability, 23)
        weights[0] = -5.0
        weights[6] = 5.0
        self.assertEqual(
            MicroPolicy(weights).commands({"units": [own, enemy]})[0].ability, 16
        )
        self.assertEqual(policy.commands({"units": [own], "memory": [enemy]}), [])

    def test_return_drives_fit_without_command_count_reward(self):
        self.assertIsNotNone(update_distribution)
        mean, scale = update_distribution(
            np.array([[1.0, 0.0], [2.0, 0.0], [-1.0, 0.0]]),
            np.array([2.0, 3.0, -1.0]),
            2,
        )
        np.testing.assert_allclose(mean, [1.5, 0.0])
        self.assertGreater(scale[1], 0.0)
        result = {
            "status": "completed",
            "sandbox_result": "Defeat",
            "score": {
                "damage_dealt": 100.0,
                "damage_taken": 50.0,
                "killed_value": 100.0,
            },
            "game_seconds": 10.0,
            "commands": 1,
        }
        self.assertEqual(
            episode_return(result), episode_return(dict(result, commands=1000))
        )
        self.assertGreater(
            episode_return(
                dict(result, score=dict(result["score"], killed_value=200.0))
            ),
            episode_return(result),
        )
        with self.assertRaises(ValueError):
            episode_return({"status": "wall_timeout"})

    def test_transfer_ownership_is_local_combat_marines_only(self):
        from src.learning.micro_policy import combat_view

        state = {
            "units": [
                {"tag": 1, "alliance": 1, "unit_type": 48, "position": [1.0, 1.0, 0.0]},
                {"tag": 2, "alliance": 1, "unit_type": 45, "position": [1.0, 1.0, 0.0]},
                {
                    "tag": 3,
                    "alliance": 1,
                    "unit_type": 48,
                    "position": [100.0, 100.0, 0.0],
                },
                {
                    "tag": 4,
                    "alliance": 4,
                    "unit_type": 105,
                    "position": [5.0, 1.0, 0.0],
                },
            ],
            "memory": [{"tag": 5, "position": [101.0, 100.0, 0.0]}],
        }
        self.assertEqual(
            [u["tag"] for u in combat_view(state)["units"] if u["alliance"] == 1], [1]
        )
        self.assertEqual([u["tag"] for u in state["units"]], [1, 2, 3, 4])
