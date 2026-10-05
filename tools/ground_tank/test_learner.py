from types import SimpleNamespace as NS
import unittest
from sc2.position import Point2
from sc2.units import Units
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.ids.ability_id import AbilityId as A
from learner import tank_ability,ground_micro
from src.rl.terran import TerranLearner


class TankTests(unittest.TestCase):
    def test_air_only_does_not_siege_and_sieged_tank_unsieges(self):
        flying=NS(is_flying=True,distance_to=lambda unit:6)
        self.assertIsNone(tank_ability(NS(type_id=U.SIEGETANK),[flying]))
        self.assertEqual(tank_ability(NS(type_id=U.SIEGETANKSIEGED),[flying]),A.UNSIEGE_UNSIEGE)

    def test_ground_units_or_structures_siege_and_preserve_hysteresis(self):
        for structure in [False,True]:
            enemy=NS(is_flying=False,is_structure=structure,distance_to=lambda unit:6)
            self.assertEqual(tank_ability(NS(type_id=U.SIEGETANK),[enemy]),A.SIEGEMODE_SIEGEMODE)
        edge=NS(is_flying=False,distance_to=lambda unit:13)
        self.assertIsNone(tank_ability(NS(type_id=U.SIEGETANK),[edge]))
        self.assertIsNone(tank_ability(NS(type_id=U.SIEGETANKSIEGED),[edge]))
        far=NS(is_flying=False,distance_to=lambda unit:14)
        self.assertEqual(tank_ability(NS(type_id=U.SIEGETANKSIEGED),[far]),A.UNSIEGE_UNSIEGE)


class UnchangedMicroTests(unittest.IsolatedAsyncioTestCase):
    async def test_marine_medivac_raven_orders_match_original(self):
        class Unit:
            def __init__(self,kind,x):
                self.type_id=kind;self.position=Point2((x,0));self._proto=NS(pos=self.position)
                self.is_idle=True;self.commands=[]
            def move(self,target):self.commands.append(('move',tuple(target)))
            def attack(self,target):self.commands.append(('attack',tuple(target)))
        results=[]
        for routine in [TerranLearner.micro,ground_micro]:
            bot=NS(time=0,next_gather=100,attacking=True,stance_changed=False,
                   start_location=Point2((0,0)),enemy_start_locations=[Point2((100,0))])
            bot.units=Units([Unit(U.MARINE,20),Unit(U.MEDIVAC,30),Unit(U.RAVEN,40)],bot)
            bot.structures=bot.townhalls=bot.enemy_units=bot.enemy_structures=Units([],bot)
            bot.army_units=lambda:bot.units
            await routine(bot)
            results.append([unit.commands for unit in bot.units])
        self.assertEqual(results[0],results[1])


if __name__=='__main__':unittest.main()
