import unittest
from s2clientprotocol import query_pb2 as query, sc2api_pb2 as pb, data_pb2 as data
from src.learning.gameplay import Command

try:
    from src.learning.live import ability_query, legal_commands, ability_catalog
except ImportError:
    ability_query = legal_commands = ability_catalog = None


class LiveInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            ability_query, "Live command legality interface is missing"
        )

    def test_query_batches_all_own_units_and_respects_resource_requirements(self):
        q = ability_query([101, 102])
        self.assertEqual([x.unit_tag for x in q.abilities], [101, 102])
        self.assertFalse(q.ignore_resource_requirements)

    def test_genuine_unavailable_ability_is_rejected_without_restricting_unit_targets(
        self,
    ):
        response = query.ResponseQuery()
        response.abilities.add(unit_tag=101).abilities.add(ability_id=23)
        response.abilities.add(unit_tag=102).abilities.add(ability_id=16)
        cmds = [
            Command(23, (101,), target_unit=201),
            Command(16, (102,), target_point=(20.0, 30.0)),
        ]
        self.assertEqual(legal_commands(cmds, response), cmds)
        with self.assertRaises(ValueError):
            legal_commands([Command(23, (102,), target_unit=201)], response)
        with self.assertRaises(ValueError):
            legal_commands([Command(23, (201,), target_unit=101)], response)

    def test_catalog_retains_engine_targets_autocast_and_remaps(self):
        response = pb.ResponseData()
        response.abilities.add(
            ability_id=316,
            link_name="Repair",
            target=data.AbilityData.Unit,
            allow_autocast=True,
            remaps_to_ability_id=316,
            available=True,
        )
        row = ability_catalog(response)[0]
        self.assertEqual(row["ability_id"], 316)
        self.assertEqual(row["target"], 3)
        self.assertTrue(row["allow_autocast"])
