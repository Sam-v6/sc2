import unittest

from src.learning import tournament_commands


class TournamentCommandsTests(unittest.TestCase):
    def event(self, sequence=1, flags=258):
        return dict(
            _gameloop=12,
            m_sequence=sequence,
            m_cmdFlags=flags,
            m_abil=dict(m_abilLink=7, m_abilCmdIndex=0),
            m_data=dict(TargetPoint=dict(x=40961, y=81923)),
        )

    def reconcile(self, events, actions, selections=None):
        return tournament_commands.reconcile_commands(
            events,
            [dict(loop=12, actions=actions)],
            selections if selections is not None else {(12, 1): [17]},
            {
                3: dict(friendly_name="Move", link_index=0),
                4: dict(friendly_name="Attack", link_index=0),
            },
            {(7, 0): "Move"},
        )

    def test_restores_precise_point_queue_and_full_native_actor_tag(self):
        tag = 2**40 + 17
        actions = [dict(ability=3, tags=[tag], target_type=2, target=[10, 20])]
        accepted, audit = self.reconcile([self.event()], actions)
        self.assertEqual(len(accepted), 1)
        command = accepted[0]["command"]
        self.assertEqual(command.units, (tag,))
        self.assertEqual(command.target_point, (40961 / 4096, 81923 / 4096))
        self.assertTrue(command.queue)
        self.assertFalse(command.autocast)
        self.assertEqual(audit["matched_issued_commands"], 1)

    def test_names_and_selection_disambiguate_same_loop_target(self):
        actions = [
            dict(ability=4, tags=[17], target_type=2, target=[10, 20]),
            dict(ability=3, tags=[19], target_type=2, target=[10, 20]),
            dict(ability=3, tags=[17], target_type=2, target=[10, 20]),
        ]
        accepted, _ = self.reconcile([self.event()], actions)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]["command"].ability, 3)
        self.assertEqual(accepted[0]["command"].units, (17,))

    def test_ambiguous_original_events_cannot_reuse_one_converted_action(self):
        actions = [dict(ability=3, tags=[17], target_type=2, target=[10, 20])]
        accepted, audit = self.reconcile(
            [self.event(), self.event(sequence=2)],
            actions,
            {(12, 1): [17], (12, 2): [17]},
        )
        self.assertEqual(accepted, [])
        self.assertEqual(len(audit["unresolved_events"]), 2)

    def test_unknown_selection_flags_and_autocast_are_explicitly_excluded(self):
        actions = [dict(ability=3, tags=[17], target_type=2, target=[10, 20])]
        for flags, selection in (
            (258, None),
            (258 | 0x40, [17]),
            (258 | 0x1000000, [17]),
        ):
            accepted, audit = self.reconcile(
                [self.event(flags=flags)], actions, {(12, 1): selection}
            )
            self.assertEqual(accepted, [])
            self.assertEqual(len(audit["unresolved_events"]), 1)
            self.assertTrue(audit["unresolved_events"][0]["reason"])

    def test_unverified_event_still_blocks_ambiguous_reuse_of_its_action(self):
        actions = [dict(ability=3, tags=[17], target_type=2, target=[10, 20])]
        for flags, selection in ((258, None), (258 | 0x1000000, [17])):
            accepted, _ = self.reconcile(
                [self.event(), self.event(sequence=2, flags=flags)],
                actions,
                {(12, 1): [17], (12, 2): selection},
            )
            self.assertEqual(accepted, [])

    def test_smart_unit_target_retains_full_tag_and_requires_original_identity(self):
        event = dict(
            _gameloop=12,
            m_sequence=1,
            m_cmdFlags=264,
            m_abil=None,
            m_data=dict(TargetUnit=dict(m_tag=21)),
        )
        action = dict(ability=1, tags=[17], target_type=1, target=2**40 + 21)
        accepted, _ = tournament_commands.reconcile_commands(
            [event],
            [dict(loop=12, actions=[action])],
            {(12, 1): [17]},
            {1: dict(friendly_name="Smart", link_index=255)},
            {},
        )
        self.assertEqual(accepted[0]["command"].target_unit, 2**40 + 21)
        self.assertFalse(accepted[0]["command"].queue)

    def test_unknown_ability_name_reserves_compatible_action_identity(self):
        unknown = self.event(sequence=2)
        unknown["m_abil"]["m_abilLink"] = 8
        accepted, audit = self.reconcile(
            [self.event(), unknown],
            [dict(ability=3, tags=[17], target_type=2, target=[10, 20])],
            {(12, 1): [17], (12, 2): [17]},
        )
        self.assertEqual(accepted, [])
        self.assertEqual(len(audit["unresolved_events"]), 2)
