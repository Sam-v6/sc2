"""Scripted Terran baseline; shared primitives remain usable by learned policies.

Design references and pinned source licenses are documented in
docs/primitives-reset-2026-10-06.md. No model training happens in this bot.
"""
import gzip
import json
from pathlib import Path

from sc2.bot_ai import BotAI
from sc2.data import Race
from sc2.ids.ability_id import AbilityId as A
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.ids.upgrade_id import UpgradeId as G
from sc2.position import Point2
from s2clientprotocol import sc2api_pb2 as pb

from src.bots.macro_rules import depot_limit, spend_float
from src.bots.terran_primitives import combat_command, mining_commands, scripted_targets, destination_reached, changes_order, scripted_attack, worker_defense_commands
from src.learning.gameplay import Command, PlayerView, protocol_dict
from src.learning.live import issue
from src.learning.production_clearance import reservations, resolve_production_placement, site_reservations

ARMY_TYPES = {U.MARINE, U.SIEGETANK, U.SIEGETANKSIEGED, U.VIKINGFIGHTER}


class PrimitiveTerranBot(BotAI):
    def __init__(self):
        super().__init__()
        self.unit_command_uses_self_do = True
        self.started, self.callback_error = False, None
        self.view = PlayerView()
        self.next_macro = 0
        self.attacking = False
        self.scouted, self.scout_tag = False, None
        self.search_index = 0
        self.summary = dict(worker_peak=0, army_peak=0, collected_minerals=0,
                            mining_commands=0, combat_commands=0, defense_commands=0, resumed_builds=0,
                            raw_action_errors=0, delayed_action_errors=0)

    async def on_start(self):
        self.client.game_step = self.requested_game_step
        response = await self.client._execute(data=pb.RequestData(ability_id=True, unit_type_id=True, upgrade_id=True))
        self.data = protocol_dict(response.data)
        self.catalog = {a['ability_id']: a for a in self.data['abilities']}
        self.types = {u['unit_id']: u for u in self.data['units']}
        self.stream = gzip.open(self.trace_path, 'xt')
        path = Path(self.trace_path)
        path.with_name(path.name.removesuffix('.jsonl.gz')+'.data.json').write_text(json.dumps(self.data)+'\n')
        self.started = True

    def free_worker(self, point):
        workers = self.workers.filter(lambda w: (w.is_idle or w.is_gathering)
                                      and w.tag not in self.unit_tags_received_action
                                      and w.tag != self.scout_tag)
        return workers.closest_to(point) if workers else None

    async def construct(self, kind, state, reserved, point=None):
        if not self.can_afford(kind) or self.tech_requirement_progress(kind) < 1:
            return False
        point = point or self.start_location.towards(self.game_info.map_center, 10)
        worker = self.free_worker(point)
        if worker is None:
            return False
        ability = self.game_data.units[kind.value].creation_ability.id.value
        resolved, _ = await resolve_production_placement(self.client,
            Command(ability, (worker.tag,), target_point=tuple(point)), self.catalog, state, kind.value, reserved)
        if not resolved:
            return False
        location = Point2(resolved[0].target_point)
        self.do(worker.build(kind, location), subtract_cost=True)
        reserved.extend(site_reservations(kind.value, tuple(location), self.catalog[ability].get('footprint_radius', 1)))
        return True

    def continue_and_repair(self):
        constructors = self.workers.filter(lambda w: w.is_constructing_scv)
        addons = {U.BARRACKSTECHLAB, U.FACTORYTECHLAB, U.STARPORTTECHLAB,
                  U.BARRACKSREACTOR, U.FACTORYREACTOR, U.STARPORTREACTOR, U.TECHLAB, U.REACTOR}
        for building in self.structures.not_ready.exclude_type(addons):
            if constructors.closer_than(building.radius+1, building):
                continue
            worker = self.free_worker(building.position)
            if worker:
                self.do(worker(A.SMART, building))
                self.summary['resumed_builds'] += 1
        if self.minerals < 100:
            return
        for building in self.structures.ready.filter(lambda u: u.health_percentage < (1 if u.type_id == U.BUNKER else .8)):
            bunker = building.type_id == U.BUNKER
            # A Bunker is repaired under fire; other buildings wait until the fight moves away.
            if not bunker and self.enemy_units.filter(lambda e: e.is_visible).closer_than(10, building):
                continue
            repairing = self.workers.filter(lambda w: w.is_repairing and w.order_target == building.tag)
            if repairing.amount >= (3 if bunker else 2):
                continue
            worker = self.free_worker(building.position)
            if worker:
                self.do(worker.repair(building))

    async def macro(self, state, targets):
        targets = spend_float(targets, state)
        self.continue_and_repair()
        for depot in self.structures(U.SUPPLYDEPOT).ready:
            self.do(depot(A.MORPH_SUPPLYDEPOT_LOWER))
        planned_workers = self.workers.amount + self.already_pending(U.SCV)
        for base in self.townhalls.ready.idle:
            if base.type_id == U.COMMANDCENTER and self.structures(U.BARRACKS).ready and self.can_afford(U.ORBITALCOMMAND):
                self.do(base(A.UPGRADETOORBITAL_ORBITALCOMMAND), subtract_cost=True)
            elif planned_workers < targets['workers'] and self.can_afford(U.SCV):
                self.do(base.train(U.SCV), subtract_cost=True, subtract_supply=True)
                planned_workers += 1
        for orbital in self.townhalls(U.ORBITALCOMMAND).filter(lambda b: b.energy >= 50):
            minerals = self.mineral_field.closer_than(10, orbital)
            if minerals and orbital.tag not in self.unit_tags_received_action:
                self.do(orbital(A.CALLDOWNMULE_CALLDOWNMULE, max(minerals, key=lambda m: m.mineral_contents)))
        reserved = reservations(state, self.types, self.catalog)
        if targets['supply'] and self.already_pending(U.SUPPLYDEPOT) < depot_limit(state):
            await self.construct(U.SUPPLYDEPOT, state, reserved)
        if (self.enemy_race == Race.Terran and self.time < 360
                and not self.structures(U.BUNKER) and not self.already_pending(U.BUNKER)):
            # Early Marine pressure hits the natural while its Command Center is still building.
            natural = self.townhalls.filter(lambda t: t.distance_to(self.start_location) > 5)
            if natural:
                await self.construct(U.BUNKER, state, reserved,
                                     natural.first.position.towards(self.enemy_start_locations[0], 6))
        if self.townhalls.amount+self.already_pending(U.COMMANDCENTER) < targets['bases'] and self.can_afford(U.COMMANDCENTER):
            point = await self.get_next_expansion()
            if point:
                await self.construct(U.COMMANDCENTER, state, reserved, point)
        barracks_lab_needed = not self.structures(U.BARRACKSTECHLAB) and not self.already_pending(U.BARRACKSTECHLAB)
        planned_tanks = self.units.of_type({U.SIEGETANK, U.SIEGETANKSIEGED}).amount+self.already_pending(U.SIEGETANK)
        enemy_air = self.enemy_units.filter(lambda e: e.is_visible and e.is_flying and e.can_attack)
        viking_target = min(8, max(2, 2*enemy_air.amount))
        for kind in (U.BARRACKS, U.FACTORY, U.STARPORT):
            addon = {U.BARRACKS: U.BARRACKSTECHLAB, U.FACTORY: U.FACTORYTECHLAB,
                     U.STARPORT: U.STARPORTTECHLAB}[kind]
            for building in self.structures(kind).ready.idle:
                if building.tag in self.unit_tags_received_action:
                    continue
                need_lab = kind == U.FACTORY or (kind == U.BARRACKS and barracks_lab_needed)
                if need_lab and not building.has_add_on and self.can_afford(addon):
                    ability = self.game_data.units[addon.value].creation_ability.id.value
                    resolved, _ = await resolve_production_placement(self.client,
                        Command(ability, (building.tag,)), self.catalog, state, addon.value, reserved)
                    if resolved:
                        self.do(building.build(addon), subtract_cost=True)
                        if kind == U.BARRACKS:
                            barracks_lab_needed = False
                    continue
                product = {U.BARRACKS: U.MARINE, U.FACTORY: U.SIEGETANK, U.STARPORT: U.MEDIVAC}[kind]
                if kind == U.FACTORY and building.add_on_tag not in self.techlab_tags:
                    continue
                if kind == U.FACTORY and planned_tanks >= targets['tanks']:
                    continue
                if kind == U.STARPORT:
                    if (enemy_air or self.units(U.MEDIVAC).amount >= 2) and self.units(U.VIKINGFIGHTER).amount+self.already_pending(U.VIKINGFIGHTER) < viking_target:
                        product = U.VIKINGFIGHTER
                    elif self.units(U.MEDIVAC).amount+self.already_pending(U.MEDIVAC) >= 4:
                        continue
                if self.can_afford(product):
                    self.do(building.train(product), subtract_cost=True, subtract_supply=True)
                    if product == U.SIEGETANK:
                        planned_tanks += 1
        for kind, key in ((U.BARRACKS, 'barracks'), (U.FACTORY, 'factories'),
                          (U.STARPORT, 'starports'), (U.ENGINEERINGBAY, 'engineering_bays')):
            if self.structures(kind).amount+self.already_pending(kind) < targets[key]:
                await self.construct(kind, state, reserved)
        if self.gas_buildings.amount+self.already_pending(U.REFINERY) < targets['refineries'] and self.can_afford(U.REFINERY):
            geysers = self.vespene_geyser.filter(lambda g: any(g.distance_to(b) < 10 for b in self.townhalls.ready)
                                               and not self.gas_buildings.closer_than(1, g))
            for geyser in geysers:
                if await self.can_place_single(U.REFINERY, geyser.position):
                    worker = self.free_worker(geyser.position)
                    if worker:
                        self.do(worker.build_gas(geyser), subtract_cost=True)
                        break
        if (self.vespene >= 300 and self.structures(U.ENGINEERINGBAY).ready
                and not self.structures(U.ARMORY) and not self.already_pending(U.ARMORY)):
            await self.construct(U.ARMORY, state, reserved)
        for upgrade in (G.STIMPACK, G.SHIELDWALL, G.TERRANINFANTRYWEAPONSLEVEL1, G.TERRANINFANTRYARMORSLEVEL1,
                        G.TERRANINFANTRYWEAPONSLEVEL2, G.TERRANINFANTRYARMORSLEVEL2):
            if not self.already_pending_upgrade(upgrade) and self.can_afford(upgrade):
                self.research(upgrade)
        if not self.scouted and self.time > 75 and self.structures(U.BARRACKS).ready:
            worker = self.free_worker(self.start_location)
            if worker:
                self.scout_tag, self.scouted = worker.tag, True
        scout = self.workers.find_by_tag(self.scout_tag) if self.scout_tag else None
        if scout and scout.health_percentage > .6 and self.time < 135:
            self.do(scout.move(self.enemy_start_locations[0]))
        else:
            if scout and self.townhalls.ready:
                minerals = self.mineral_field.closer_than(10, self.townhalls.ready.closest_to(scout))
                if minerals:
                    self.do(scout.gather(minerals.closest_to(scout)))
            self.scout_tag = None

    strategy_record = None

    def man_bunkers(self):
        """Keep ready Bunkers full while holding; empty them when the army attacks."""
        self.loading = set()
        for bunker in self.structures(U.BUNKER).ready:
            if self.attacking:
                if bunker.cargo_used:
                    self.do(bunker(A.UNLOADALL_BUNKER))
                continue
            marines = self.units(U.MARINE)
            heading = marines.filter(lambda m: m.order_target == bunker.tag)
            self.loading |= heading.tags
            room = bunker.cargo_max - bunker.cargo_used - heading.amount
            free = marines.filter(lambda m: m.tag not in self.loading and m.tag not in self.unit_tags_received_action)
            for marine in free.sorted_by_distance_to(bunker)[:max(0, room)]:
                self.do(marine.smart(bunker))
                self.loading.add(marine.tag)

    def strategy_targets(self, state, macro):
        return scripted_targets(state)

    def strategy_attack(self, state):
        return scripted_attack(state, self.attacking)

    def army_destination(self, state):
        army = self.units.of_type(ARMY_TYPES)
        self.attacking = self.strategy_attack(state)
        threats = self.enemy_units.filter(lambda e: e.is_visible and e.can_attack_ground
                                         and any(e.distance_to(b) < 22 for b in self.townhalls))
        if threats:
            return threats.closest_to(self.start_location).position
        if not self.attacking:
            return self.start_location.towards(self.game_info.map_center, 12)
        structures = self.enemy_structures.filter(lambda e: e.is_visible and e.type_id != U.KD8CHARGE)
        if structures:
            return structures.closest_to(army.center if army else self.start_location).position
        search = [self.enemy_start_locations[0]] + sorted(self.expansion_locations_list,
                                                           key=lambda p: p.distance_to(self.enemy_start_locations[0]))
        target = search[self.search_index % len(search)]
        if destination_reached([tuple(u.position) for u in army], tuple(target)):
            self.search_index += 1
        return target

    async def on_step(self, iteration):
        try:
            state = self.view.observe(self.state.response_observation)
            state['map_size'] = [self.game_info.map_size.x, self.game_info.map_size.y]
            macro = self.state.game_loop >= self.next_macro
            targets = self.strategy_targets(state, macro)
            commands = []
            if macro:
                self.next_macro = self.state.game_loop+24
                await self.macro(state, targets)
            scout = {self.scout_tag} if self.scout_tag else set()
            defense = worker_defense_commands(state, self.types, self.unit_tags_received_action | scout)
            self.summary['defense_commands'] += len(defense)
            commands.extend(defense)
            if macro:
                protected = self.unit_tags_received_action | scout | {c.units[0] for c in defense}
                mining = mining_commands(state, targets['gas_workers'], protected)
                self.summary['mining_commands'] += len(mining)
                commands.extend(mining)
            enemies = [u for u in state['units'] if u['alliance'] == 4]
            destination = self.army_destination(state)
            self.man_bunkers()
            ground = self.units.of_type({U.MARINE, U.SIEGETANK, U.SIEGETANKSIEGED})
            bio = self.units(U.MARINE).filter(lambda u: u.health_percentage > .65 and not u.has_buff(BuffId.STIMPACK)
                                             and any(u.distance_to(e) < 8 for e in self.enemy_units if e.is_visible))
            if G.STIMPACK in self.state.upgrades and bio:
                abilities = await self.get_available_abilities(bio)
                for marine, available in zip(bio, abilities):
                    if A.EFFECT_STIM_MARINE in available:
                        self.do(marine(A.EFFECT_STIM_MARINE))
            for unit in state['units']:
                if (unit['alliance'] != 1 or unit['unit_type'] not in (48, 33, 32, 35)
                        or unit['tag'] in self.unit_tags_received_action or unit['tag'] in self.loading):
                    continue
                target = destination
                if unit['unit_type'] == 35:
                    air = [e for e in enemies if e.get('is_flying') and e.get('cloak') in (2, 3)
                           and e.get('health', 0) > 0]
                    if air:
                        enemy = min(air, key=lambda e: Point2(e['position'][:2]).distance_to(Point2(unit['position'][:2])))
                        target = Point2(enemy['position'][:2])
                    elif ground:
                        target = ground.center
                command = combat_command(unit, enemies, self.types, tuple(target),
                                          lambda p: self.in_map_bounds(Point2(p)) and self.in_pathing_grid(Point2(p)))
                if command and changes_order(unit, command):
                    commands.append(command)
                    self.summary['combat_commands'] += 1
            army = self.units.of_type(ARMY_TYPES)
            injured = self.units(U.MARINE).filter(lambda u: u.health_percentage < 1)
            for medivac in self.units(U.MEDIVAC):
                if injured and medivac.energy > 0:
                    self.do(medivac(A.MEDIVACHEAL_HEAL, injured.closest_to(medivac)))
                elif army:
                    self.do(medivac.move(army.center))
            response = await issue(self.client, commands) if commands else pb.ResponseAction()
            if len(response.result) != len(commands):
                raise ValueError('Incomplete primitive action response')
            errors = [dict(ability=e.ability_id, tag=e.unit_tag, result=e.result)
                      for e in self.state.response_observation.action_errors]
            self.summary['raw_action_errors'] += sum(code != 1 for code in response.result)
            self.summary['delayed_action_errors'] += len(errors)
            self.summary['worker_peak'] = max(self.summary['worker_peak'], self.workers.amount)
            self.summary['army_peak'] = max(self.summary['army_peak'], army.amount)
            self.summary['collected_minerals'] = self.state.score.collected_minerals
            self.stream.write(json.dumps(dict(loop=self.state.game_loop,
                observation=state if macro else None, targets=targets if macro else None,
                strategy=self.strategy_record if macro else None,
                destination=list(destination), commands=[c.as_dict() for c in commands], results=list(response.result),
                delayed_errors=errors,
                sdk_actions=[dict(ability=a.ability.value, tag=a.unit.tag,
                                  target=a.target.tag if hasattr(a.target, 'tag') else list(a.target) if a.target else None)
                             for a in self.actions], score={k: float(v) for k,v in self.state.score.summary} if macro else None))+'\n')
        except Exception as error:
            self.callback_error = repr(error)
            raise

    async def on_end(self, game_result):
        self.stream.close()
