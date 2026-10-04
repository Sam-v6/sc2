"""Live state and atomic macro actions; no scripted build order or unit mix."""
import json
from itertools import chain
from pathlib import Path
import numpy as np
from src.rl.unit_observation import observe_units, FEATURES as UNIT_FEATURES
from src.path import SC2_GAME_PATH
from src.common.void_bot_base import VoidBotBase
from sc2.data import Result
from sc2.ids.ability_id import AbilityId as A
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.ids.upgrade_id import UpgradeId as G

# Live observations respect fog; SC2 can retain previously scouted snapshots.
SCALES = {'time': 1200, 'minerals': 1000, 'gas': 1000, 'supply_left': 30,
          'workers': 80, 'army': 100, 'bases': 5, 'barracks': 8, 'factory': 4,
          'starport': 4, 'refinery': 8, 'marines': 80, 'marauders': 40,
          'tanks': 20, 'medivacs': 10, 'battlecruisers': 10,
          'enemy_ground': 40, 'enemy_air': 20, 'enemy_near_base': 20,
          'enemy_near_army': 20, 'enemy_distance': 100, 'attacking': 1,
          'pending_depot': 1, 'pending_barracks': 1, 'techlab': 4,
          'engineeringbay': 1, 'fusioncore': 1, 'infantry_weapons': 1,
          'idle_barracks': 8, 'idle_townhalls': 5, 'army_distance_home': 100,
          'army_distance_enemy_start': 100, 'stance_seconds': 20,
          'reapers': 40, 'hellions': 40, 'vikings': 20,
          'ravens': 10, 'turrets': 10, 'enemy_cloaked': 10,
          'match_limit': 1200, 'remaining_time': 1200}
FEATURES = ['bias', *SCALES, *UNIT_FEATURES]
NORMALIZATION = np.array(list(SCALES.values()), dtype=float)
REWARD_VERSION = 'combat-kills-v1'
BUILDINGS = {'depot': U.SUPPLYDEPOT, 'barracks': U.BARRACKS, 'refinery': U.REFINERY,
             'factory': U.FACTORY, 'starport': U.STARPORT, 'engineeringbay': U.ENGINEERINGBAY,
             'fusioncore': U.FUSIONCORE, 'expand': U.COMMANDCENTER, 'turret': U.MISSILETURRET}
UNITS = {'scv': (U.SCV, U.COMMANDCENTER, False), 'marine': (U.MARINE, U.BARRACKS, False),
         'marauder': (U.MARAUDER, U.BARRACKS, True), 'reaper': (U.REAPER, U.BARRACKS, False),
         'tank': (U.SIEGETANK, U.FACTORY, True), 'hellion': (U.HELLION, U.FACTORY, False),
         'medivac': (U.MEDIVAC, U.STARPORT, False), 'viking': (U.VIKINGFIGHTER, U.STARPORT, False),
         'battlecruiser': (U.BATTLECRUISER, U.STARPORT, True),
         'raven': (U.RAVEN, U.STARPORT, True)}
ADDONS = {'barracks_techlab': (U.BARRACKSTECHLAB, U.BARRACKS),
          'factory_techlab': (U.FACTORYTECHLAB, U.FACTORY),
          'starport_techlab': (U.STARPORTTECHLAB, U.STARPORT)}
PRODUCTION = {U.BARRACKS, U.FACTORY, U.STARPORT}
ACTIONS = ['wait', *BUILDINGS, *UNITS, *ADDONS, 'orbital', 'infantry_weapons', 'attack', 'retreat']


def avoids_addons(position, radius, reserved):
    return all(abs(position.x - site.x) >= radius + 1 or abs(position.y - site.y) >= radius + 1
               for site in reserved)


def encode(snapshot):
    values = np.fromiter((snapshot.get(key, 0) for key in SCALES), dtype=float, count=len(SCALES))
    units = np.zeros(len(UNIT_FEATURES))
    for index, value in snapshot.get('unit_state', {}).items():
        units[int(index)] = value
    return np.concatenate(([1.], np.clip(values / NORMALIZATION, 0, 2), units))


def capacity_potential(observation):
    return sum(weight * SCALES[name] * observation[FEATURES.index(name)]
               for name, weight in (('workers', .5), ('army', .2), ('bases', 2)))


def reward(previous_potential, next_potential, gamma, terminal_reward=0):
    return terminal_reward + gamma * next_potential - previous_potential


class TerranLearner(VoidBotBase):
    def __init__(self, policy, training, action_log, macro_seconds=5, random_policy=False, game_seconds=1200):
        super().__init__()
        self.policy = policy
        self.training = training
        self.action_log = Path(action_log)
        self.macro_seconds = macro_seconds
        self.game_seconds = game_seconds
        self.random_policy = random_policy
        self.attacking = False
        self.stance_changed = False
        self.stance_changed_at = 0
        self.next_macro = 0
        self.next_gather = 0
        self.previous = None
        self.previous_score = None
        self.transitions = []
        self.decisions = []
        self.expansion_target = None
        self.expansion_builder = None
        self.addon_candidates = {}
        self.execution_details = {}

    async def custom_on_start(self):
        self.client.game_step = 8

    def army_units(self):
        return self.units.exclude_type({U.SCV, U.MULE})

    def snapshot(self):
        army = self.army_units()
        enemies = self.enemy_units
        home = self.townhalls.first.position if self.townhalls else self.start_location
        center = army.center if army else home
        unit_state = observe_units(chain(self.units, self.structures),
                    chain(self.enemy_units, self.enemy_structures), self.game_info.playable_area)
        return {'unit_state': {int(i): float(unit_state[i]) for i in np.flatnonzero(unit_state)},
                'time': self.time, 'minerals': self.minerals, 'gas': self.vespene,
                'supply_left': self.supply_left, 'workers': self.supply_workers,
                'army': self.supply_army, 'bases': self.townhalls.amount,
                'barracks': self.structures(U.BARRACKS).amount,
                'factory': self.structures(U.FACTORY).amount,
                'starport': self.structures(U.STARPORT).amount,
                'refinery': self.gas_buildings.amount,
                'marines': self.units(U.MARINE).amount, 'marauders': self.units(U.MARAUDER).amount,
                'tanks': self.units.of_type({U.SIEGETANK, U.SIEGETANKSIEGED}).amount,
                'medivacs': self.units(U.MEDIVAC).amount,
                'battlecruisers': self.units(U.BATTLECRUISER).amount,
                'reapers': self.units(U.REAPER).amount,
                'hellions': self.units.of_type({U.HELLION, U.HELLIONTANK}).amount,
                'vikings': self.units.of_type({U.VIKINGFIGHTER, U.VIKINGASSAULT}).amount,
                'ravens': self.units(U.RAVEN).amount,
                'turrets': self.structures(U.MISSILETURRET).ready.amount,
                'enemy_cloaked': enemies.filter(lambda unit: unit.is_cloaked).amount,
                'match_limit': self.game_seconds, 'remaining_time': max(0, self.game_seconds - self.time),
                'enemy_ground': enemies.not_flying.amount, 'enemy_air': enemies.flying.amount,
                'enemy_near_base': enemies.closer_than(20, home).amount,
                'enemy_near_army': enemies.closer_than(15, center).amount,
                'enemy_distance': enemies.closest_to(center).distance_to(center) if enemies else 100,
                'attacking': float(self.attacking),
                'pending_depot': self.already_pending(U.SUPPLYDEPOT),
                'pending_barracks': self.already_pending(U.BARRACKS),
                'techlab': self.structures.of_type({U.BARRACKSTECHLAB, U.FACTORYTECHLAB, U.STARPORTTECHLAB}).ready.amount,
                'engineeringbay': self.structures(U.ENGINEERINGBAY).ready.amount,
                'fusioncore': self.structures(U.FUSIONCORE).ready.amount,
                'infantry_weapons': float(G.TERRANINFANTRYWEAPONSLEVEL1 in self.state.upgrades),
                'idle_barracks': self.structures(U.BARRACKS).ready.idle.amount,
                'idle_townhalls': self.townhalls.ready.idle.amount,
                'army_distance_home': center.distance_to(home),
                'army_distance_enemy_start': center.distance_to(self.enemy_start_locations[0]),
                'stance_seconds': self.time - self.stance_changed_at}

    def producers(self, unit, producer, needs_lab):
        structures = self.townhalls if unit == U.SCV else self.structures(producer)
        labs = self.structures.of_type({U.BARRACKSTECHLAB, U.FACTORYTECHLAB, U.STARPORTTECHLAB}).ready.tags
        return structures.ready.idle.filter(lambda p: not needs_lab or p.add_on_tag in labs)

    def geysers(self):
        return self.vespene_geyser.filter(lambda g: any(g.distance_to(b) < 12 for b in self.townhalls.ready)
                                         and not self.gas_buildings.closer_than(1, g))

    def legal_mask(self, spatial=True):
        legal = {'wait': True}
        for name, unit in BUILDINGS.items():
            legal[name] = bool(self.workers and self.townhalls and self.can_afford(unit)
                               and self.tech_requirement_progress(unit) == 1 and self.already_pending(unit) < 1)
        legal['depot'] &= self.supply_cap < 200
        legal['refinery'] &= bool(self.geysers())
        for name, (unit, producer, needs_lab) in UNITS.items():
            legal[name] = bool(self.can_afford(unit) and self.can_feed(unit)
                               and self.tech_requirement_progress(unit) == 1
                               and self.producers(unit, producer, needs_lab))
        for name, (unit, producer) in ADDONS.items():
            legal[name] = bool(self.can_afford(unit) and self.structures(producer).ready.idle.filter(lambda p: not p.has_add_on))
        legal['orbital'] = bool(self.townhalls(U.COMMANDCENTER).ready.idle and self.can_afford(U.ORBITALCOMMAND)
                                and self.tech_requirement_progress(U.ORBITALCOMMAND) == 1)
        upgrade = G.TERRANINFANTRYWEAPONSLEVEL1
        legal['infantry_weapons'] = bool(self.structures(U.ENGINEERINGBAY).ready.idle and self.can_afford(upgrade)
                                          and self.already_pending_upgrade(upgrade) == 0)
        legal['attack'] = bool(self.army_units()) and not self.attacking
        legal['retreat'] = bool(self.army_units()) and self.attacking
        if spatial:
            legal['expand'] &= self.expansion_target is not None
            for name in ADDONS:
                legal[name] &= bool(self.addon_candidates.get(name))
        return np.array([legal[name] for name in ACTIONS])

    async def prepare_macro_options(self):
        raw = self.legal_mask(spatial=False)
        self.expansion_target = None
        self.expansion_builder = None
        if raw[ACTIONS.index('expand')]:
            reserved = self.reserved_addons()
            radius = self.game_data.units[U.COMMANDCENTER.value].footprint_radius
            sites = [site for site in self.expansion_locations_list
                     if avoids_addons(site, radius, reserved)
                     and not any(base.distance_to(site) < self.EXPANSION_GAP_THRESHOLD for base in self.townhalls)]
            if sites:
                placement = await self.client._query_building_placement_fast(A.TERRANBUILD_COMMANDCENTER, sites)
                eligible = [(site, self.select_build_worker(site)) for site, valid in zip(sites, placement) if valid]
                eligible = [(site, builder) for site, builder in eligible if builder]
                if eligible:
                    distances = await self.client.query_pathings([[builder.position, site] for site, builder in eligible])
                    feasible = [(distance, site, builder) for (site, builder), distance in zip(eligible, distances) if distance > 0]
                    if feasible:
                        _, self.expansion_target, self.expansion_builder = min(feasible, key=lambda item: item[0])
        self.addon_candidates = {}
        for name, (_, producer) in ADDONS.items():
            feasible = []
            if raw[ACTIONS.index(name)]:
                for candidate in self.structures(producer).ready.idle.filter(lambda p: not p.has_add_on):
                    if await self.can_place_single(U.SUPPLYDEPOT, candidate.add_on_position):
                        feasible.append(candidate)
            self.addon_candidates[name] = feasible

    def reserved_addons(self):
        return [p.add_on_position for p in self.structures.of_type(PRODUCTION) if not p.has_add_on]

    async def build_location(self, unit, near):
        # Keep empty add-on footprints clear when any later structure is placed.
        reserved = self.reserved_addons()
        radius = self.game_data.units[unit.value].footprint_radius
        positions = [near.offset((x, y)) for x in range(-18, 19, 3) for y in range(-18, 19, 3)]
        positions = [p for p in positions if avoids_addons(p, radius, reserved)]
        if unit in PRODUCTION:
            positions = [p for p in positions if avoids_addons(p.offset((2.5, -.5)), 1, reserved)]
        if not positions:
            return None
        ability = self.game_data.units[unit.value].creation_ability.id
        valid = await self.client._query_building_placement_fast(ability, positions)
        positions = [p for p, allowed in zip(positions, valid) if allowed]
        if unit in PRODUCTION and positions:
            valid = await self.client._query_building_placement_fast(A.TERRANBUILD_SUPPLYDEPOT,
                                                                    [p.offset((2.5, -.5)) for p in positions])
            positions = [p for p, allowed in zip(positions, valid) if allowed]
        return min(positions, key=lambda p: p.distance_to(near)) if positions else None

    def potential(self):
        # Potential shaping, rather than repeated reward for unchanged stockpiles.
        return capacity_potential(encode({'workers': self.supply_workers, 'army': self.supply_army, 'bases': self.townhalls.amount}))

    async def execute(self, name):
        self.execution_details = {}
        if name in ('attack', 'retreat'):
            self.attacking = name == 'attack'
            self.stance_changed = True
            self.stance_changed_at = self.time
            return True
        if name == 'wait':
            return True
        if name in UNITS:
            unit, producer, needs_lab = UNITS[name]
            producers = self.producers(unit, producer, needs_lab)
            if producers:
                return bool(producers.first.train(unit))
        elif name in ADDONS:
            unit, _ = ADDONS[name]
            candidates = self.addon_candidates.get(name, [])
            if candidates:
                self.execution_details = {'producer': getattr(candidates[0], 'tag', None)}
                return bool(candidates[0].build(unit))
        elif name == 'orbital':
            return bool(self.townhalls(U.COMMANDCENTER).ready.idle.first(A.UPGRADETOORBITAL_ORBITALCOMMAND))
        elif name == 'infantry_weapons':
            return bool(self.research(G.TERRANINFANTRYWEAPONSLEVEL1))
        elif name == 'expand':
            location = self.expansion_target
            if location:
                self.execution_details = {'destination': list(location), 'builder': self.expansion_builder.tag}
                return bool(await self.build(U.COMMANDCENTER, near=location, max_distance=0, build_worker=self.expansion_builder))
        elif name == 'refinery':
            geysers = self.geysers()
            if geysers:
                worker = self.select_build_worker(geysers.first.position)
                if worker:
                    return bool(worker.build_gas(geysers.first))
        elif name in BUILDINGS and self.townhalls:
            base = self.townhalls.ready.first if self.townhalls.ready else self.townhalls.first
            location = await self.build_location(BUILDINGS[name], base.position.towards(self.game_info.map_center, 8))
            if location:
                self.execution_details = {'destination': list(location)}
                return bool(await self.build(BUILDINGS[name], near=location, max_distance=0))
            self.execution_details = {'reason': 'no placement with reserved add-on clearance'}
        return False

    async def micro(self):
        for depot in self.structures(U.SUPPLYDEPOT).ready:
            depot(A.MORPH_SUPPLYDEPOT_LOWER)
        if self.time >= self.next_gather:
            await self.distribute_workers()
            self.next_gather = self.time + 4
        for orbital in self.townhalls(U.ORBITALCOMMAND).ready:
            if orbital.energy >= 50 and self.mineral_field:
                orbital(A.CALLDOWNMULE_CALLDOWNMULE, self.mineral_field.closest_to(orbital))
        army = self.army_units()
        if not army:
            return
        home = self.townhalls.first.position if self.townhalls else self.start_location
        threats = self.enemy_units.closer_than(20, home)
        target = self.enemy_structures.closest_to(army.center).position if self.enemy_structures else self.enemy_start_locations[0]
        if not self.attacking:
            target = threats.closest_to(home).position if threats else home.towards(self.game_info.map_center, 8)
        for unit in army:
            if unit.type_id == U.SIEGETANK and self.enemy_units.closer_than(12, unit):
                unit(A.SIEGEMODE_SIEGEMODE)
            elif unit.type_id == U.SIEGETANKSIEGED and not self.enemy_units.closer_than(14, unit):
                unit(A.UNSIEGE_UNSIEGE)
            elif unit.type_id in {U.MEDIVAC, U.RAVEN}:
                combat = army.exclude_type({U.MEDIVAC, U.RAVEN})
                if combat:
                    unit.move(combat.center)
            elif unit.type_id != U.SIEGETANKSIEGED:
                if self.stance_changed or unit.is_idle or (unit.order_target != target and not unit.is_attacking):
                    unit.attack(target)
        self.stance_changed = False

    def combat_score(self):
        score = self.state.score
        return {'killed': score.killed_value_units + score.killed_value_structures,
                'lost': sum(getattr(score, f'lost_{resource}_{category}')
                            for resource in ('minerals', 'vespene')
                            for category in ('none', 'army', 'economy', 'technology', 'upgrade'))}

    def transition(self, observation, mask, potential, terminal=False, terminal_reward=0):
        score = self.combat_score()
        if self.previous is not None:
            state, action, old_potential = self.previous
            event = (score['killed'] - self.previous_score['killed']) / 100
            shaped = self.policy.reward_scale * (reward(old_potential, potential, self.policy.gamma, terminal_reward) + event)
            self.transitions.append((state, action, shaped, observation, mask, terminal))
            self.decisions[-1]['reward'] = shaped
            self.decisions[-1]['reward_components'] = {'terminal': terminal_reward, 'potential_previous': old_potential, 'potential_next': potential, 'scale': self.policy.reward_scale,
                                                     'combat_previous': self.previous_score, 'combat_next': score, 'combat_event': event}
        self.previous_score = score

    async def custom_on_step(self, iteration):
        # Gather first so redistribution cannot overwrite a newly selected builder.
        await self.micro()
        if self.time >= self.next_macro:
            await self.prepare_macro_options()
            snapshot = self.snapshot()
            state, mask, potential = encode(snapshot), self.legal_mask(), self.potential()
            self.transition(state, mask, potential)
            action = self.policy.act(state, mask, explore=self.training or self.random_policy)
            executed = await self.execute(ACTIONS[action])
            self.decisions.append({'time': self.time, 'action': ACTIONS[action], 'executed': executed, 'execution': self.execution_details,
                                   'snapshot': snapshot, 'legal': [name for name, allowed in zip(ACTIONS, mask) if allowed]})
            self.previous = (state, action, potential)
            self.next_macro = self.time + self.macro_seconds

    async def custom_on_end(self, result):
        if self.started and not self.callback_error:
            # Finite-match objective: time-limit ties end this task, with no win payoff.
            bonus = 100 if result == Result.Victory else 0
            self.transition(encode(self.snapshot()), self.legal_mask(), 0, True, bonus)
        self.action_log.parent.mkdir(parents=True, exist_ok=True)
        with self.action_log.open('w') as file:
            for decision in self.decisions:
                file.write(json.dumps(decision) + '\n')
