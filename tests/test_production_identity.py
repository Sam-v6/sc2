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

    def test_legacy_viking_producer_requires_native_training_index(self):
        catalog=dict(units=[dict(name='VikingFighter',ability_id=624)],
                     abilities=[dict(ability_id=624,link_index=4)])
        self.assertEqual(producer_ability('Viking',4,catalog),624)
        self.assertIsNone(producer_ability('Viking',0,catalog))

    def test_research_uses_upgrade_name_and_specific_index(self):
        from src.learning.production_identity import research_ability
        catalog=dict(upgrades=[dict(name='TerranVehicleAndShipArmorsLevel1',ability_id=2297),
                               dict(name='TerranVehicleWeaponsLevel1',ability_id=855),
                               dict(name='CycloneLockOnDamageUpgrade',ability_id=769)],
                     abilities=[dict(ability_id=2297,link_index=14),
                                dict(ability_id=855,link_index=5),
                                dict(ability_id=769,link_index=9)])
        for name,index,ability in [('ResearchTerranVehicleAndShipArmorsLevel1',14,2297),
                                   ('UpgradeVehicleWeapons1',5,855),
                                   ('ResearchCycloneLockOnDamageUpgrade',9,769)]:
            self.assertEqual(research_ability(name,index,catalog),ability)
            self.assertIsNone(research_ability(name,index+1,catalog))
        self.assertIsNone(research_ability('ThorAPMode',0,catalog))

    def test_research_upgrade_pointer_can_name_an_inactive_legacy_ability(self):
        from src.learning.production_identity import research_ability
        catalog=dict(upgrades=[dict(name='TerranVehicleAndShipArmorsLevel1',ability_id=2297)],
                     abilities=[dict(ability_id=2297,link_index=3,available=False,
                                     friendly_name='Research TerranVehicleAndShipPlatingLevel1'),
                                dict(ability_id=864,link_index=14,available=True,
                                     friendly_name='Research TerranVehicleAndShipPlatingLevel1')])
        self.assertEqual(research_ability('ResearchTerranVehicleAndShipArmorsLevel1',14,catalog),864)
        self.assertIsNone(research_ability('ResearchTerranVehicleAndShipArmorsLevel1',3,catalog))
