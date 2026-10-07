import unittest

from src.learning.replay_command_events import command_events


def event(kind, loop, **fields):
    return dict(_event='NNet.Game.'+kind, _gameloop=loop,
                _userid=dict(m_userId=0), **fields)


class ReplayCommandEventsTests(unittest.TestCase):
    def command(self):
        return event('SCmdEvent', 10, m_sequence=1, m_cmdFlags=258,
                     m_abil=dict(m_abilLink=129, m_abilCmdIndex=10),
                     m_data=dict(TargetPoint=dict(x=4096, y=8192)))

    def test_target_update_and_subsequent_repeat_keep_ability_flags_and_provenance(self):
        original = self.command()
        update = event('SCmdUpdateTargetPointEvent', 12, m_target=dict(x=12288, y=16384))
        manager = event('SCommandManagerStateEvent', 12, m_sequence=2, m_state=1)
        repeat = event('SCommandManagerStateEvent', 13, m_sequence=3, m_state=1)
        rows, unresolved = command_events([original, update, manager, repeat], 0)
        self.assertFalse(unresolved)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1]['m_abil'], original['m_abil'])
        self.assertEqual(rows[1]['m_cmdFlags'], 258)
        self.assertEqual(rows[2]['m_data'], dict(TargetPoint=update['m_target']))
        self.assertEqual(rows[2]['source_command'], dict(loop=10, sequence=1))
        self.assertEqual(rows[1]['source_manager'], manager)
        self.assertEqual(original['m_data']['TargetPoint']['x'], 4096)

    def test_unit_update_and_no_target_repeat(self):
        original = self.command()
        original['m_data'] = {'None': None}
        update = event('SCmdUpdateTargetUnitEvent', 12, m_target=dict(m_tag=123))
        manager = event('SCommandManagerStateEvent', 12, m_sequence=2, m_state=1)
        rows, _ = command_events([original, manager], 0)
        self.assertEqual(rows[1]['m_data'], {'None': None})
        rows, _ = command_events([original, update, manager], 0)
        self.assertEqual(rows[1]['m_data'], dict(TargetUnit=dict(m_tag=123)))

    def test_unknown_state_selection_changes_and_unpaired_updates_cannot_create_labels(self):
        manager = event('SCommandManagerStateEvent', 12, m_sequence=2, m_state=1)
        for middle in (event('SSelectionDeltaEvent', 11),
                       event('SControlGroupUpdateEvent', 11),
                       event('SCmdUpdateTargetPointEvent', 11, m_target=dict(x=1,y=2))):
            rows, unresolved = command_events([self.command(), middle, manager], 0)
            self.assertEqual(len(rows), 1)
            self.assertEqual(len(unresolved), 1)
        manager['m_state'] = 2
        self.assertEqual(len(command_events([self.command(), manager], 0)[0]), 1)
        self.assertEqual(command_events([self.command()], 1)[0], [])
