import tempfile
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.units import Units
import micro_trace_worker as trace


class MicroTraceTests(unittest.TestCase):
    def test_observation_records_current_orders_and_air_ground_without_commands(self):
        bot=NS(time=123)
        marine=NS(tag=1,type_id=U.MARINE,is_biological=True,health=20,health_max=45,distance_to=lambda unit:3)
        medivac=NS(tag=2,type_id=U.MEDIVAC,health=150,energy=80,position=(0,0),
                   orders=[NS(ability=NS(id=NS(name='MOVE_MOVE')))])
        tank=NS(tag=3,type_id=U.SIEGETANKSIEGED,health=175,energy=0,position=(0,0),orders=[])
        class Nearby:
            def filter(self,fn):return self
            def closer_than(self,distance,unit):return [marine]
        bot.army_units=lambda:Nearby()
        bot.units=Units([medivac,tank],bot)
        bot.enemy_units=NS(closer_than=lambda distance,unit:[NS(is_flying=True)])
        bot.enemy_structures=NS(closer_than=lambda distance,unit:[])
        result=trace.observation(bot)
        self.assertEqual(result['units'][0]['orders'],['MOVE_MOVE'])
        self.assertEqual(result['units'][0]['nearby_biological'][0]['health'],20)
        self.assertEqual(result['units'][1]['nearby_enemy_ground'],0)
        self.assertEqual(result['units'][1]['nearby_enemy_air'],1)
        self.assertEqual(result['units'][1]['ground_structures_within14'],0)

    def test_failure_restores_original_observer_and_flushes_trace(self):
        previous=trace.teacher_worker.ObservedLearner
        with tempfile.TemporaryDirectory() as temp:
            job={'experiment':'micro-order-diagnostic','diagnostic_only':True,'micro_trace':str(Path(temp)/'trace.jsonl')}
            with patch.object(trace.teacher_worker,'episode',side_effect=RuntimeError('native failure')):
                with self.assertRaisesRegex(RuntimeError,'native failure'):trace.episode(job)
            self.assertIs(trace.teacher_worker.ObservedLearner,previous)
            self.assertTrue(Path(job['micro_trace']).exists())


if __name__=='__main__':unittest.main()
