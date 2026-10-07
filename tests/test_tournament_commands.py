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

    def test_generic_lift_land_alias_requires_observed_matching_producer(self):
        catalog = {
            3679: dict(friendly_name='Lift', link_index=0),
            485: dict(friendly_name='Lift Factory', link_index=0,
                      remaps_to_ability_id=3679),
            3678: dict(friendly_name='Land', link_index=0),
            520: dict(friendly_name='Land Factory', link_index=0,
                      remaps_to_ability_id=3678),
        }
        for ability, name, flying in [(3679, 'LiftFactory', False),
                                     (3678, 'LandFactory', True)]:
            event = self.event(flags=256)
            event['m_data'] = ({'None': None} if ability == 3679
                               else event['m_data'])
            action = dict(ability=ability, tags=[17],
                          target_type=0 if ability == 3679 else 2,
                          target=None if ability == 3679 else [10, 20])
            for types, expected in [({17: 'FactoryFlying' if flying else 'Factory'}, 1),
                                    ({17: 'Barracks'}, 0), ({}, 0)]:
                accepted, _ = tournament_commands.reconcile_commands(
                    [event], [dict(loop=12, actions=[action], unit_types=types)],
                    {(12, 1): [17]}, catalog, {(7, 0): name})
                self.assertEqual(len(accepted), expected)
                if accepted and ability == 3678:
                    self.assertEqual(accepted[0]['command'].target_point,
                                     (40961 / 4096, 81923 / 4096))

    def test_generic_alias_still_reserves_unsupported_duplicate(self):
        event = self.event(flags=256)
        event['m_data'] = {'None': None}
        duplicate = dict(event, m_sequence=2, m_cmdFlags=256 | 0x1000000)
        accepted, audit = tournament_commands.reconcile_commands(
            [event, duplicate],
            [dict(loop=12, unit_types={17: 'Factory'},
                  actions=[dict(ability=3679, tags=[17], target_type=0, target=None)])],
            {(12, 1): [17], (12, 2): [17]},
            {3679: dict(friendly_name='Lift', link_index=0),
             485: dict(friendly_name='Lift Factory', link_index=0,
                       remaps_to_ability_id=3679)}, {(7, 0): 'LiftFactory'})
        self.assertEqual(accepted, [])
        self.assertEqual([e['candidate_count'] for e in audit['unresolved_events']], [1, 1])

    def test_generic_reactor_alias_keeps_point_and_specific_command_index(self):
        event = self.event(flags=256)
        event['m_abil']['m_abilCmdIndex'] = 1
        action = dict(ability=3683, tags=[17], target_type=2, target=[10, 20])
        catalog = {
            3683: dict(friendly_name='Build Reactor', link_index=0),
            422: dict(friendly_name='Build Reactor Barracks', link_index=1,
                      remaps_to_ability_id=3683),
        }
        names = {(7, 1): 'BuildBarracksReactor'}
        for types, expected in [({17: 'BarracksFlying'}, 1),
                                ({17: 'FactoryFlying'}, 0), ({}, 0)]:
            accepted, _ = tournament_commands.reconcile_commands(
                [event], [dict(loop=12, actions=[action], unit_types=types)],
                {(12, 1): [17]}, catalog, names)
            self.assertEqual(len(accepted), expected)
            if accepted:
                self.assertEqual(accepted[0]['command'].target_point,
                                 (40961 / 4096, 81923 / 4096))
        event['m_abil']['m_abilCmdIndex'] = 0
        accepted, _ = tournament_commands.reconcile_commands(
            [event], [dict(loop=12, actions=[action], unit_types={17: 'Barracks'})],
            {(12, 1): [17]}, catalog, {(7, 0): 'BuildBarracksReactor'})
        self.assertEqual(accepted, [])

    def test_addon_point_cannot_be_dropped_or_unknown_flags_admitted(self):
        event = self.event(flags=256)
        catalog = {
            3682: dict(friendly_name='Build TechLab', link_index=0),
            421: dict(friendly_name='Build TechLab Barracks', link_index=0,
                      remaps_to_ability_id=3682),
        }
        for target_type, flags in [(0, 256), (2, 256 | 0x1000000)]:
            event['m_cmdFlags'] = flags
            accepted, _ = tournament_commands.reconcile_commands(
                [event], [dict(loop=12, unit_types={17: 'Barracks'}, actions=[
                    dict(ability=3682, tags=[17], target_type=target_type,
                         target=[10, 20] if target_type == 2 else None)])],
                {(12, 1): [17]}, catalog, {(7, 0): 'BuildBarracksTechLab'})
            self.assertEqual(accepted, [])
