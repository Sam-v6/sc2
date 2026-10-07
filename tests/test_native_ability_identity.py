"""Native nonproduction aliases require matching names and command indices."""

import unittest

from src.learning.native_ability_identity import native_ability_matches


class NativeAbilityIdentityTests(unittest.TestCase):
    def matches(self, source, friendly, button, index=0, original_index=0):
        event = {"m_abil": {"m_abilLink": 45, "m_abilCmdIndex": original_index}}
        catalog = {
            23: dict(friendly_name=friendly, button_name=button, link_index=index)
        }
        return native_ability_matches(
            {"ability": 23, "tags": [1]}, event, catalog, {(45, original_index): source}
        )

    def test_attack_button_corresponds_to_native_attack_family(self):
        self.assertTrue(self.matches("Attack", "Attack Attack", "Attack"))

    def test_hold_position_family_preserves_original_command_index(self):
        self.assertTrue(
            self.matches("HoldPosition", "HoldPosition Hold", "MoveHoldPosition", 2, 2)
        )
        self.assertFalse(
            self.matches("HoldPosition", "HoldPosition Hold", "MoveHoldPosition", 2, 0)
        )

    def test_named_effect_button_is_a_nonproduction_identity(self):
        self.assertTrue(
            self.matches("CalldownMULE", "Effect CalldownMULE", "CalldownMULE")
        )

    def test_wrong_reader_name_does_not_establish_ability(self):
        self.assertFalse(
            self.matches("AdeptShadePhaseShiftCancel", "Effect KD8Charge", "KD8Charge")
        )

    def test_extra_button_rule_cannot_guess_production(self):
        self.assertFalse(self.matches("Attack", "Build Attack", "Attack"))
