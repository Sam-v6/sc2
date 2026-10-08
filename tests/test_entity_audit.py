import unittest

from src.learning.entity_encoder import JointEntityEncoder
from src.learning.entity_examples import command_label, state_inputs
from src.learning.entity_policy import JointEntityPolicy
from src.learning.gameplay import Command

try:
    from src.learning.entity_audit import audit_commands
except ImportError:
    audit_commands = None


class EntityAuditTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            audit_commands, "complete predicted-command audit is missing"
        )
        state = dict(
            game_loop=10,
            map_size=[10, 6],
            player={},
            upgrades=[],
            units=[
                dict(tag=tag, unit_type=2, alliance=1, position=[2, 3, 0])
                for tag in (11, 12)
            ],
        )
        self.inputs = state_inputs(state, 8, 12)
        self.policy = JointEntityPolicy(
            JointEntityEncoder(94, 13, 9, 8, 12, hidden=4), (0, 1, 8)
        )
        for parameter in self.policy.parameters.values():
            parameter[:] = 0
        self.policy.heads["ability_bias"][3] = 100
        self.policy.heads["mode_bias"][0] = 100
        self.policy.heads["queue_bias"][0] = 100
        self.policy.heads["delay_bias"][2] = 100
        self.command = Command(3, (11,))
        self.label = command_label(self.command, self.inputs, (0, 1, 8), 8)

    def test_complete_audit_uses_predicted_actors_and_reports_oracles_separately(self):
        report = audit_commands(
            self.policy, [(self.inputs, self.label, self.command, None)]
        )
        self.assertEqual(report["commands"], 1)
        self.assertEqual(report["predicted"]["ability"], 1)
        self.assertEqual(report["predicted"]["actors"], 0)
        self.assertEqual(report["predicted"]["complete"], 0)
        self.assertEqual(report["ability_actor_oracle"]["complete"], 1)

    def test_excluded_labels_still_count_against_complete_command_denominator(self):
        missing = Command(3, (11,), target_unit=999)
        report = audit_commands(
            self.policy, [(self.inputs, None, missing, "unobserved target")]
        )
        self.assertEqual(report["commands"], 1)
        self.assertEqual(report["representable"], 0)
        self.assertEqual(report["predicted"]["complete"], 0)
        self.assertEqual(report["exclusions"], {"unobserved target": 1})

    def test_unknown_timing_is_not_a_correct_delay_prediction(self):
        self.label["delay"] = None
        report = audit_commands(
            self.policy, [(self.inputs, self.label, self.command, None)]
        )
        self.assertEqual(report["timed_commands"], 0)
        self.assertEqual(report["predicted"]["delay"], 0)
        self.assertEqual(report["predicted"]["complete_with_timing"], 0)


if __name__ == "__main__":
    unittest.main()
