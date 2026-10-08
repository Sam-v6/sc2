"""Observe engine orders without changing the closed teacher or its commands."""
import json
from pathlib import Path
from sc2.ids.unit_typeid import UnitTypeId as U
import teacher_worker


def observation(bot):
    biological=bot.army_units().filter(lambda unit:unit.is_biological)
    rows=[]
    for unit in bot.units.of_type({U.MEDIVAC,U.SIEGETANK,U.SIEGETANKSIEGED}):
        nearby=bot.enemy_units.closer_than(14,unit)
        row={'tag':unit.tag,'type':unit.type_id.name,'health':unit.health,'energy':unit.energy,
             'orders':[order.ability.id.name for order in unit.orders],
             'nearby_enemy_ground':sum(not enemy.is_flying for enemy in nearby),
             'nearby_enemy_air':sum(enemy.is_flying for enemy in nearby),
             'enemy_ground_within12':sum(not enemy.is_flying for enemy in bot.enemy_units.closer_than(12,unit)),
             'enemy_air_within12':sum(enemy.is_flying for enemy in bot.enemy_units.closer_than(12,unit)),
             'ground_structures_within14':sum(not enemy.is_flying for enemy in bot.enemy_structures.closer_than(14,unit))}
        if unit.type_id==U.MEDIVAC:
            row['nearby_biological']=[{'tag':ally.tag,'type':ally.type_id.name,'health':ally.health,'maximum':ally.health_max,
                                     'distance':ally.distance_to(unit)} for ally in biological.closer_than(12,unit)]
        rows.append(row)
    return {'time':bot.time,'units':rows}


def episode(job):
    assert job['experiment']=='micro-order-diagnostic' and job['diagnostic_only'] is True
    path=Path(job['micro_trace']);path.parent.mkdir(parents=True,exist_ok=True)
    previous=teacher_worker.ObservedLearner
    with path.open('x',buffering=1) as file:
        class TracedLearner(previous):
            async def custom_on_step(self,iteration):
                file.write(json.dumps(observation(self))+'\n')
                await super().custom_on_step(iteration)
        teacher_worker.ObservedLearner=TracedLearner
        try:result=teacher_worker.episode(job)
        finally:teacher_worker.ObservedLearner=previous
    result.update(micro_trace_sha256=teacher_worker.digest(path),micro_trace_bytes=path.stat().st_size)
    return result


def entrypoint_probe():return {'file':__file__,'games_launched':0}
