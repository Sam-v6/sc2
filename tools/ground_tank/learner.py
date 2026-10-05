"""Isolated tank guard correction; archived learner source stays immutable."""
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.ids.ability_id import AbilityId as A
from src.rl.terran import TerranLearner


def tank_ability(unit,enemies):
    if unit.type_id not in {U.SIEGETANK,U.SIEGETANKSIEGED}:return None
    ground=[enemy for enemy in enemies if not enemy.is_flying and enemy.distance_to(unit)<14]
    if unit.type_id==U.SIEGETANK and any(enemy.distance_to(unit)<12 for enemy in ground):
        return A.SIEGEMODE_SIEGEMODE
    if unit.type_id==U.SIEGETANKSIEGED and not ground:return A.UNSIEGE_UNSIEGE
    return None


async def ground_micro(self):
    # Preserve the frozen micro body except the tank guard. Keeping this adapter
    # separate lets archived studies continue to verify their original source.
    for depot in self.structures(U.SUPPLYDEPOT).ready:
        depot(A.MORPH_SUPPLYDEPOT_LOWER)
    if self.time >= self.next_gather:
        await self.distribute_workers()
        self.next_gather = self.time + 4
    for orbital in self.townhalls(U.ORBITALCOMMAND).ready:
        if orbital.energy >= 50 and self.mineral_field:
            orbital(A.CALLDOWNMULE_CALLDOWNMULE, self.mineral_field.closest_to(orbital))
    army = self.army_units()
    if not army:return
    home = self.townhalls.first.position if self.townhalls else self.start_location
    threats = self.enemy_units.closer_than(20, home)
    target = self.enemy_structures.closest_to(army.center).position if self.enemy_structures else self.enemy_start_locations[0]
    if not self.attacking:
        target = threats.closest_to(home).position if threats else home.towards(self.game_info.map_center, 8)
    enemies=list(self.enemy_units)+list(self.enemy_structures)
    for unit in army:
        ability=tank_ability(unit,enemies)
        if ability is not None:
            unit(ability)
        elif unit.type_id in {U.MEDIVAC, U.RAVEN}:
            combat = army.exclude_type({U.MEDIVAC, U.RAVEN})
            if combat:unit.move(combat.center)
        elif unit.type_id != U.SIEGETANKSIEGED:
            if self.stance_changed or unit.is_idle or (unit.order_target != target and not unit.is_attacking):
                unit.attack(target)
    self.stance_changed = False


class GroundTankLearner(TerranLearner):
    micro=ground_micro
