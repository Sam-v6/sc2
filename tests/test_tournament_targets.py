from dataclasses import replace
import unittest

from src.learning.gameplay import Command
from src.learning.tournament_targets import normalized_resource_target


class TournamentTargetsTests(unittest.TestCase):
    def setUp(self):
        self.command = Command(1, (17,), target_unit=2**32 + 21, queue=True)
        self.event = dict(
            m_data=dict(
                TargetUnit=dict(
                    m_tag=21,
                    m_snapshotControlPlayerId=0,
                    m_snapshotUpkeepPlayerId=0,
                    m_snapshotPoint=dict(x=10 * 4096, y=20 * 4096),
                )
            )
        )
        self.state = dict(
            units=[
                dict(
                    tag=99,
                    unit_type=665,
                    alliance=3,
                    display_type=1,
                    position=[10, 20, 0],
                )
            ]
        )

    def resolve(self, **kwargs):
        return normalized_resource_target(
            kwargs.get("command", self.command),
            self.event,
            self.state,
            kwargs.get("original_type", 665),
            {665, 666},
        )

    def test_exact_visible_resource_identity_preserves_command_arguments(self):
        command, mapping = self.resolve()
        self.assertEqual(command, replace(self.command, target_unit=99))
        self.assertEqual(mapping["original_tag"], self.command.target_unit)
        self.assertEqual(mapping["source_tag"], 99)
        self.assertEqual(mapping["position"], [10, 20])

    def test_hidden_mismatched_nonresource_and_ambiguous_targets_are_not_guessed(self):
        for modification in (
            dict(display_type=2),
            dict(alliance=4),
            dict(unit_type=666),
            dict(position=[10.001, 20, 0]),
            dict(is_blip=True),
        ):
            original = self.state["units"][0].copy()
            self.state["units"][0].update(modification)
            self.assertEqual(self.resolve(), (self.command, None))
            self.state["units"][0] = original
        self.assertEqual(self.resolve(original_type=111), (self.command, None))
        self.state["units"].append(dict(self.state["units"][0], tag=100))
        self.assertEqual(self.resolve(), (self.command, None))

    def test_existing_target_and_nonunit_modes_are_unchanged(self):
        self.state["units"][0]["tag"] = self.command.target_unit
        self.assertEqual(self.resolve(), (self.command, None))
        command = Command(1, (17,), target_point=(10, 20))
        self.assertEqual(self.resolve(command=command), (command, None))

    def test_original_tag_and_neutral_ownership_must_agree(self):
        target = self.event["m_data"]["TargetUnit"]
        target["m_tag"] = 22
        self.assertEqual(self.resolve(), (self.command, None))
        target["m_tag"] = 21
        target["m_snapshotControlPlayerId"] = 2
        self.assertEqual(self.resolve(), (self.command, None))
