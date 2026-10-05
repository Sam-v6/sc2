import unittest
from s2clientprotocol import sc2api_pb2 as pb, query_pb2 as query
from src.learning.gameplay import Command
from src.learning.placement import resolve_placements


class PlacementTests(unittest.IsolatedAsyncioTestCase):
    async def test_learned_map_ranking_uses_highest_scored_engine_legal_position(self):
        class Client:
            async def _execute(self, **kwargs):
                return pb.Response(
                    query=query.ResponseQuery(
                        placements=[
                            query.ResponseQueryBuildingPlacement(result=41),
                            query.ResponseQueryBuildingPlacement(result=1),
                        ]
                    )
                )

        command = Command(318, (7,), target_point=(87.99, 40.0))
        commands, trace = await resolve_placements(
            Client(),
            [command],
            {318: {"is_building": True}},
            {"units": [], "map_size": [88, 96]},
            ranked_points={(318, (7,)): [(30.5, 30.5), (34.5, 30.5)]},
        )
        self.assertEqual(commands[0].target_point, (34.5, 30.5))
        self.assertEqual(trace[0]["source"], "learned_spatial_candidates")

    async def test_nearest_legal_point_keeps_learned_ability_group_and_queue(self):
        class Client:
            async def _execute(self, **kwargs):
                self.request = kwargs["query"]
                return pb.Response(
                    query=query.ResponseQuery(
                        placements=[
                            query.ResponseQueryBuildingPlacement(
                                result=1
                                if p.target_pos.x == 11 and p.target_pos.y == 10
                                else 41
                            )
                            for p in self.request.placements
                        ]
                    )
                )

        client = Client()
        command = Command(321, (7,), target_point=(10.0, 10.0), queue=True)
        commands, trace = await resolve_placements(
            client,
            [command],
            {321: {"is_building": True}},
            {"units": [], "map_size": [64.0, 64.0]},
        )
        self.assertEqual(commands[0].target_point, (11.0, 10.0))
        self.assertEqual(commands[0].units, (7,))
        self.assertTrue(commands[0].queue)
        self.assertEqual(trace[0]["requested_point"], [10.0, 10.0])
        self.assertTrue(all(p.placing_unit_tag == 7 for p in client.request.placements))

    async def test_no_legal_local_placement_is_reported_without_fabricated_action(self):
        class Client:
            async def _execute(self, **kwargs):
                return pb.Response(
                    query=query.ResponseQuery(
                        placements=[
                            query.ResponseQueryBuildingPlacement(result=41)
                            for _ in kwargs["query"].placements
                        ]
                    )
                )

        commands, trace = await resolve_placements(
            Client(),
            [Command(321, (7,), target_point=(10.0, 10.0))],
            {321: {"is_building": True}},
            {"units": [], "map_size": [64.0, 64.0]},
        )
        self.assertEqual(commands, [])
        self.assertEqual(trace[0]["rejected"], "no_legal_local_placement")

    async def test_nonconstruction_commands_do_not_query_or_change_targets(self):
        class Client:
            async def _execute(self, **kwargs):
                raise AssertionError("Unexpected placement query")

        command = Command(23, (7,), target_point=(10.0, 10.0))
        commands, trace = await resolve_placements(
            Client(), [command], {23: {}}, {"units": [], "map_size": [64.0, 64.0]}
        )
        self.assertEqual(commands, [command])
        self.assertEqual(trace, [])
