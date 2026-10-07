import unittest

from src.learning.human_production_plan import compile_commands, compile_builder_moves


class HumanProductionPlanTests(unittest.TestCase):
    def test_queued_worker_movement_retains_original_building_relation(self):
        accepted = [dict(loop=10, sequence=1, command=dict(ability=1, units=[99],
                        target_point=[131.5, 47.5], queue=False))]
        events = {(10, 1): dict(m_cmdFlags=266, m_data=dict(TargetPoint=dict(x=538624, y=194560)))}
        tickets = [dict(loop=20, sequence=2, actor_types=[45], name='Build Barracks',
                        command=dict(units=[99], target_point=[131.5, 47.5]))]
        own = {10: {99: dict(unit_type=45)}}
        moves = compile_builder_moves(accepted, events, tickets, own, {})
        self.assertEqual(len(moves), 1)
        self.assertTrue(moves[0]['command']['queue'])
        self.assertEqual(moves[0]['source_build'], dict(loop=20, sequence=2))
        tickets[0]['command']['units'] = [100]
        self.assertEqual(compile_builder_moves(accepted, events, tickets, own, {}), [])

    def test_original_precise_point_and_queue_recovered(self):
        data = dict(units=[dict(unit_id=45, name='SCV')], abilities=[
            dict(ability_id=321, friendly_name='Build Barracks')])
        accepted = [dict(loop=10, sequence=1, command=dict(
            ability=321, units=[99], target_point=[131, 47], queue=False))]
        events = {(10, 1): dict(m_abil=None, m_cmdFlags=258,
                               m_data=dict(TargetPoint=dict(x=538624, y=194560)))}
        own = {10: {99: dict(unit_type=45)}}
        plan = compile_commands(accepted, events, data, own, [])
        command = plan['tickets'][0]['command']
        self.assertEqual(command['target_point'], [131.5, 47.5])
        self.assertTrue(command['queue'])
        events[(10, 1)]['m_data']['TargetPoint']['x'] += 4096
        self.assertEqual(compile_commands(accepted, events, data, own, [])['tickets'], [])

    def test_specific_research_preserves_source_tier(self):
        data = dict(units=[dict(unit_id=29, name='Armory', attributes=[8])], abilities=[
            dict(ability_id=3700, friendly_name='Research Armor'),
            dict(ability_id=864, friendly_name='Research ArmorLevel1', remaps_to_ability_id=3700),
            dict(ability_id=865, friendly_name='Research ArmorLevel2', remaps_to_ability_id=3700)])
        accepted = [dict(loop=10, sequence=1, command=dict(ability=3700, units=[99]))]
        events = {(10, 1): dict(m_abil=dict(m_abilLink=169, m_abilCmdIndex=15), m_cmdFlags=256)}
        own = {10: {99: dict(unit_type=29)}}
        mapping = [dict(link=169, index=15, native_specific=865)]
        plan = compile_commands(accepted, events, data, own, mapping)
        self.assertEqual(plan['unresolved'], [])
        self.assertEqual(plan['tickets'][0]['command']['ability'], 865)
        mapping.append(dict(link=169, index=15, native_specific=864))
        self.assertEqual(compile_commands(accepted, events, data, own, mapping)['tickets'], [])

    def test_combat_cancel_is_not_a_production_ticket(self):
        data = dict(units=[dict(unit_id=692, name='Cyclone', attributes=[])],
                    abilities=[dict(ability_id=3659, friendly_name='Cancel')])
        accepted = [dict(loop=10, sequence=1, command=dict(ability=3659, units=[99]))]
        plan = compile_commands(accepted, {}, data, {10: {99: dict(unit_type=692)}}, [])
        self.assertEqual(plan, dict(tickets=[], unresolved=[]))
