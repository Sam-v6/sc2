import unittest

from src.learning.production_identity import producer_ability


class ProductionIdentityTests(unittest.TestCase):
    def catalog(self):
        return dict(
            units=[dict(unit_id=33, name="SiegeTank", ability_id=591)],
            abilities=[
                dict(ability_id=591, friendly_name="Train SiegeTank", link_index=1)
            ],
        )

    def test_uses_exact_unit_name_and_producer_index_not_reader_numeric_id(self):
        self.assertEqual(producer_ability("SiegeTank", 1, self.catalog()), 591)
        self.assertIsNone(producer_ability("siegetank", 1, self.catalog()))
        self.assertIsNone(producer_ability("SiegeTank", 0, self.catalog()))

    def test_missing_and_ambiguous_metadata_remain_unknown(self):
        catalog = self.catalog()
        catalog["units"].append(dict(unit_id=999, name="SiegeTank", ability_id=591))
        self.assertIsNone(producer_ability("SiegeTank", 1, catalog))
        catalog = self.catalog()
        catalog["abilities"] = []
        self.assertIsNone(producer_ability("SiegeTank", 1, catalog))
        self.assertIsNone(producer_ability(None, 1, self.catalog()))
