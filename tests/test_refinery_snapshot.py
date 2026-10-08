import unittest
from copy import deepcopy
from src.learning.tournament_targets import refinery_snapshot_label


class RefinerySnapshotTests(unittest.TestCase):
    def fixture(self):
        return dict(
            event=dict(
                _gameloop=100,
                m_sequence=1,
                m_cmdFlags=256,
                m_abil=dict(m_abilCmdIndex=2),
                m_data=dict(
                    TargetUnit=dict(
                        m_tag=0,
                        m_snapshotControlPlayerId=0,
                        m_snapshotUpkeepPlayerId=0,
                        m_snapshotUnitLink=512,
                        m_snapshotPoint=dict(x=464896, y=219136),
                    )
                ),
            ),
            action=dict(ability=320, tags=[17], target_type=1, target=99),
            actor=dict(tag=17, alliance=1, name="SCV"),
            raw_name="BuildRefinery",
            resources=[
                dict(
                    tag=99,
                    alliance=3,
                    unit_type=343,
                    display_type=1,
                    position=[113.5, 53.5],
                    is_blip=False,
                )
            ],
            map_resource=dict(
                _gameloop=0,
                m_upkeepPlayerId=0,
                m_controlPlayerId=0,
                m_unitTypeName=b"SpacePlatformGeyser",
                m_x=113,
                m_y=53,
            ),
            resource_types={343: "SpacePlatformGeyser"},
        )

    def test_zero_tag_snapshot_uses_unique_current_resource_and_original_map(self):
        args = self.fixture()
        prior = deepcopy(args)
        result = refinery_snapshot_label(**args)
        self.assertIsNotNone(result)
        command, proof = result
        self.assertEqual(command.target_unit, 99)
        self.assertEqual(proof["source_event"], args["event"])
        self.assertEqual(args, prior)

    def test_static_map_snapshot_keeps_target_unobserved(self):
        args = self.fixture()
        args['resources'][0]['display_type'] = 2
        command, proof = refinery_snapshot_label(**args)
        self.assertEqual(command.target_unit, 99)
        self.assertFalse(proof['target_observed'])
        self.assertTrue(proof['target_requires_representation_check'])

    def test_nonzero_foreign_unknown_or_ambiguous_targets_are_not_guessed(self):
        changes = [
            lambda a: a["event"]["m_data"]["TargetUnit"].update(m_tag=7),
            lambda a: a["event"]["m_data"]["TargetUnit"].update(
                m_snapshotUpkeepPlayerId=1
            ),
            lambda a: a["resources"].append(dict(a["resources"][0], tag=98)),
            lambda a: a["resources"][0].update(display_type=3),
            lambda a: a["actor"].update(name="Marine"),
            lambda a: a["map_resource"].update(m_unitTypeName=b"MineralField"),
            lambda a: a["map_resource"].update(_gameloop=100),
        ]
        for change in changes:
            args = self.fixture()
            change(args)
            self.assertIsNone(refinery_snapshot_label(**args))
