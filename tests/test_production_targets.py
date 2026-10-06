import unittest
from src.learning.production_targets import production_targets


def row(loop, sequence, ability):
    return dict(
        action_loop=loop,
        source_sequence=sequence,
        commands=[dict(ability=ability)],
        observation={"sentinel": loop},
    )


class ProductionTargetsTests(unittest.TestCase):
    def test_same_loop_order_current_production_and_end_censoring(self):
        rows = [
            row(10, 1, 1),
            row(10, 2, 319),
            row(10, 3, 1),
            row(20, 4, 524),
            row(30, 5, 1),
        ]
        result = production_targets(rows, {319, 524}, [])
        self.assertEqual(
            result[0], dict(ability=319, delay_loops=0, target_key=[10, 2])
        )
        self.assertEqual(result[1], result[0])
        self.assertEqual(
            result[2], dict(ability=524, delay_loops=10, target_key=[20, 4])
        )
        self.assertEqual(result[3]["delay_loops"], 0)
        self.assertIsNone(result[4])
        self.assertEqual(rows[0]["observation"], {"sentinel": 10})

    def test_unknown_intervening_event_censors_even_at_same_loop(self):
        rows = [row(10, 1, 1), row(10, 3, 319), row(20, 5, 524)]
        result = production_targets(rows, {319, 524}, [(10, 2), (20, 6)])
        self.assertIsNone(result[0])
        self.assertIsNotNone(result[1])
        self.assertIsNotNone(result[2])

    def test_empty_input_and_invalid_source_contract(self):
        self.assertEqual(production_targets([], {319}, []), [])
        with self.assertRaisesRegex(ValueError, "increasing"):
            production_targets([row(20, 2, 319), row(10, 1, 1)], {319}, [])
        with self.assertRaisesRegex(ValueError, "both retained"):
            production_targets([row(10, 1, 319)], {319}, [(10, 1)])
        grouped = row(10, 1, 319)
        grouped["commands"].append(dict(ability=524))
        with self.assertRaisesRegex(ValueError, "one issued command"):
            production_targets([grouped], {319}, [])
