import unittest
import numpy as np

try:
    from src.learning.imitation_play import decode_commands
except ImportError:
    decode_commands = None


class ImitationPlayTests(unittest.TestCase):
    def predictions(self):
        return {
            "ability": np.zeros((1, 600)),
            "mode": np.array([[0.0, 0.0, 10.0, 0.0]]),
            "target_type": np.array([[0.0, 0.0, 10.0]]),
            "alliance": np.array([[0.0, 0.0, 0.0, 0.0, 10.0]]),
            "queue": np.array([[0.0, 10.0]]),
            "delay": np.zeros((1, 10)),
            "point": np.array([[5 / 128, 0.0]]),
        }

    def test_live_targets_remap_to_current_tags_and_engine_rules_mask_abilities(self):
        self.assertIsNotNone(decode_commands)
        own = {"tag": 10, "unit_type": 48, "alliance": 1, "position": [10.0, 10.0, 0.0]}
        enemy = {
            "tag": 99,
            "unit_type": 105,
            "alliance": 4,
            "position": [15.0, 10.0, 0.0],
        }
        output = self.predictions()
        output["ability"][0, 23] = 10
        output["ability"][0, 524] = 20
        commands, rows = decode_commands(
            {"units": [own, enemy]},
            [own],
            output,
            {10: {23}},
            {23: {"target": 4}},
            [48, 105],
            (64, 64),
        )
        self.assertEqual(commands[0].ability, 23)
        self.assertEqual(commands[0].target_unit, 99)
        self.assertTrue(commands[0].queue)
        self.assertEqual(rows[0]["raw_ability"], 524)
        self.assertEqual(rows[0]["ability"], 23)

    def test_no_target_and_empty_availability_do_not_fabricate_targets(self):
        self.assertIsNotNone(decode_commands)
        own = {"tag": 10, "unit_type": 48, "alliance": 1, "position": [10.0, 10.0, 0.0]}
        output = self.predictions()
        output["ability"][0, 524] = 10
        commands, _ = decode_commands(
            {"units": [own]},
            [own],
            output,
            {10: {524}},
            {524: {"target": 1}},
            [48, 105],
            (64, 64),
        )
        self.assertIsNone(commands[0].target_unit)
        self.assertIsNone(commands[0].target_point)
        self.assertEqual(
            decode_commands(
                {"units": [own]},
                [own],
                output,
                {10: set()},
                {524: {"target": 1}},
                [48, 105],
                (64, 64),
            )[0],
            [],
        )


class WorkerExecutionTests(unittest.TestCase):
    def test_idle_worker_execution_preserves_ongoing_and_current_model_orders(self):
        from src.learning.imitation_play import idle_worker_harvest

        units = [
            {"tag": 1, "unit_type": 45, "alliance": 1, "position": [1.0, 1.0]},
            {"tag": 2, "unit_type": 45, "alliance": 1, "position": [2.0, 1.0]},
            {
                "tag": 3,
                "unit_type": 45,
                "alliance": 1,
                "position": [2.0, 1.0],
                "orders": [{"ability_id": 319}],
            },
            {"tag": 4, "unit_type": 45, "alliance": 1, "position": [2.0, 1.0]},
            {
                "tag": 5,
                "unit_type": 341,
                "alliance": 3,
                "position": [3.0, 1.0],
                "mineral_contents": 900,
            },
        ]
        commands = idle_worker_harvest({"units": units}, {4})
        self.assertEqual(len(commands), 2)
        self.assertEqual([c.units for c in commands], [(1,), (2,)])
        self.assertEqual(commands[0].target_unit, 5)


class ExplorationTests(unittest.TestCase):
    def test_learned_cadence_waits_only_after_engine_accepted_commands(self):
        from src.learning.imitation_play import command_delay

        job = {"step": 4, "learned_cadence": True}
        self.assertEqual(command_delay(job, True, 128, [1]), 128)
        self.assertEqual(command_delay(job, True, 128, [203]), 4)
        self.assertEqual(command_delay(job, True, 128, []), 4)
        self.assertEqual(command_delay({"step": 4}, True, 128, [1]), 4)
        self.assertEqual(command_delay({"step": 4}, False, 128, [203]), 128)

    def test_unavailable_intent_can_wait_instead_of_issuing_unrelated_command(self):
        from src.learning.imitation_play import choose_ability

        logits = np.array([0.0, 1.0, 8.0, 2.0])
        self.assertEqual(
            choose_ability(
                logits,
                [0, 1, 3],
                np.random.default_rng(1),
                False,
                wait_unavailable=True,
            ),
            0,
        )
        self.assertEqual(
            choose_ability(
                logits,
                [0, 1, 2, 3],
                np.random.default_rng(1),
                False,
                wait_unavailable=True,
            ),
            2,
        )

    def test_argument_predictions_preserve_macro_ability_and_convert_coordinates(self):
        from src.learning.imitation_play import replace_arguments

        macro = {"ability": np.array([[0.0, 3.0, 2.0]]), "point": np.zeros((1, 5))}
        arguments = {
            "ability": np.zeros((1, 1)),
            "point": np.array([[0.2, 0.3]]),
            "mode": np.ones((1, 4)),
        }
        output = replace_arguments(macro, arguments, [-1.0, 1.0])
        np.testing.assert_array_equal(output["ability"], macro["ability"])
        np.testing.assert_allclose(output["point"], [[-0.2, 0.3]])
        np.testing.assert_allclose(arguments["point"], [[0.2, 0.3]])

    def test_sampling_uses_only_engine_legal_commands_and_reproducible_seed(self):
        from src.learning.imitation_play import choose_ability

        logits = np.array([0.0, 0.0, 100.0, 0.0])
        first = np.random.default_rng(7)
        second = np.random.default_rng(7)
        a = [choose_ability(logits, [1, 3], first, True) for _ in range(100)]
        b = [choose_ability(logits, [1, 3], second, True) for _ in range(100)]
        self.assertEqual(a, b)
        self.assertEqual(set(a), {1, 3})
        self.assertEqual(choose_ability(logits, [1, 3], first, False), 1)


class ResidualTerminalTests(unittest.IsolatedAsyncioTestCase):
    async def test_terminal_observation_unwraps_response_and_keeps_final_kills(self):
        from src.learning.imitation_play import ImitationBot
        from s2clientprotocol import sc2api_pb2 as pb
        from types import SimpleNamespace

        response = pb.Response()
        response.observation.observation.game_loop = 128
        response.observation.observation.score.score_details.killed_value_units = 50

        async def observe():
            return response

        bot = object.__new__(ImitationBot)
        bot.residual = True
        bot.client = SimpleNamespace(observation=observe)
        await bot.on_end(None)
        self.assertEqual(bot.rl_final_loop, 128)
        self.assertEqual(bot.final_score["killed_value"], 50)
