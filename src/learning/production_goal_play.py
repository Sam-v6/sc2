"""Bounded learned production with scripted execution and combat assistance. No RL."""

import gzip
import hashlib
import json
import math
import pickle
from collections import Counter
from pathlib import Path

import numpy as np

from sc2.bot_ai import BotAI
from sc2.data import Race, Difficulty, AIBuild
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.position import Point2
from s2clientprotocol import sc2api_pb2 as pb

from src.learning.actor_selection import construction_products
from src.learning.entity_execution import validate_order_aliases
from src.learning.gameplay import Command, PlayerView, protocol_dict
from src.learning.live import ability_query, issue
from src.learning.production_clearance import reservations, resolve_production_placement, claimed_geysers, site_reservations, refinery_sites
from src.learning.production_execution import (canonical, eligible_actors,
                                              goal_catalog, queued_work)
from src.learning.production_goal_policy import current_features, predict_goals
from src.learning.production_ledger import ProductionLedger
from src.learning.production_intents import ProductionIntents, remaining_budget
from src.learning.production_prior import prior_scores
from src.learning.production_scout import WorkerScout
from src.learning.production_inventory import observation_stock
from src.learning.production_inventory_goals import HumanGoalLibrary, InventoryIntents, inventory_queued, opponent_selected_race
from src.runner import validate_map
from src.learning.production_primitives import primitive_assistance, scripted_army_destination


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ProductionGoalBot(BotAI):
    def __init__(self, job, stream):
        super().__init__()
        self.job, self.stream = job, stream
        self.model = pickle.loads(Path(job['model']).read_bytes())
        self.vocabulary = job['vocabulary']
        self.profile = json.loads(Path(job['profile']).read_text())
        self.view = PlayerView()
        self.inventory_library = HumanGoalLibrary.load(job['goal_library']) if job.get('goal_library') else None
        self.intent_mode = job.get('intent_execution', False) or self.inventory_library is not None
        if self.inventory_library and self.inventory_library.names != self.model['names']:
            raise ValueError('Human inventory and execution families differ')
        self.prior = json.loads(Path(job['prior']).read_text()) if job.get('prior') else None
        if self.prior and self.prior['names'] != self.model['names']:
            raise ValueError('Human prior and count checkpoint families differ')
        self.ledger = InventoryIntents() if self.inventory_library else (ProductionIntents() if self.intent_mode else ProductionLedger())
        self.last_sent = {}
        self.next_plan = 0
        self.next_mining = 0
        self.attacking = False
        self.search_index = 0
        self.frames = 0
        self.callback_error = None
        self.observed_types = {}
        self.earned_upgrades = set()
        self.production = []
        self.result_counts = Counter()
        self.requested = Counter()
        self.acknowledged = Counter()
        self.blocks = Counter()
        self.snapshots = []
        self.scout = WorkerScout()
        self.scout_commands = []

    async def on_start(self):
        self.client.game_step = 8
        data = (await self.client._execute(data=pb.RequestData(
            ability_id=True, unit_type_id=True, upgrade_id=True))).data
        self.data = protocol_dict(data)
        actual = [max(row[key] for row in self.data[group]) + 1
                  for group, key in [('units', 'unit_id'), ('abilities', 'ability_id'),
                                     ('upgrades', 'upgrade_id')]]
        if actual != self.vocabulary:
            raise ValueError('Native vocabulary differs from professional source')
        self.catalog = {a['ability_id']: a for a in self.data['abilities']}
        self.units_by_id = {u['unit_id']: u for u in self.data['units']}
        self.unit_names = {k: u['name'] for k, u in self.units_by_id.items()}
        self.goals = goal_catalog(self.data, self.model['names'])
        self.products = construction_products(self.data)
        if self.inventory_library:
            self.public_race = opponent_selected_race(self.game_info._proto, self.player_id)
        validate_order_aliases(self.profile, self.catalog)
        (Path(self.job['output'])/'static.json').write_text(json.dumps(self.data)+'\n')

    def record_outcomes(self, state):
        own = [u for u in state['units'] if u['alliance'] == 1]
        for u in own:
            tag, kind = u['tag'], u['unit_type']
            name = 'unit:' + self.unit_names[kind]
            previous = self.observed_types.get(tag)
            if self.frames > 0 and name in self.goals and (
                previous is None or (kind != previous and name in
                                     ('unit:OrbitalCommand', 'unit:PlanetaryFortress'))):
                self.production.append(dict(loop=state['game_loop'], goal=name, tag=tag))
            self.observed_types[tag] = kind
        for goal, info in self.goals.items():
            upgrade = info['upgrade']
            if upgrade is not None and upgrade in state['upgrades'] and upgrade not in self.earned_upgrades:
                self.production.append(dict(loop=state['game_loop'], goal=goal))
                self.earned_upgrades.add(upgrade)
        counts = Counter(self.unit_names[u['unit_type']] for u in own)
        army = sum(1 for u in own if 8 not in self.units_by_id[u['unit_type']].get('attributes', [])
                   and self.unit_names[u['unit_type']] not in ('SCV', 'MULE'))
        bases = sum(counts[n] for n in ('CommandCenter', 'OrbitalCommand', 'PlanetaryFortress'))
        self.snapshots.append(dict(loop=state['game_loop'], workers=counts['SCV'],
                                   army=army, bases=bases, units=dict(counts),
                                   player=state['player']))

    def building_point(self, goal, state):
        own = [u for u in state['units'] if u['alliance'] == 1]
        if goal == 'unit:CommandCenter':
            bases = [u for u in own if self.unit_names[u['unit_type']] in
                     ('CommandCenter', 'OrbitalCommand', 'PlanetaryFortress')]
            points = [p for p in self.expansion_locations_list
                      if all(math.dist((p.x, p.y), u['position'][:2]) > 8 for u in bases)]
            if not points:
                return None
            point = min(points, key=lambda p: p.distance_to(self.start_location))
            return point.x, point.y
        point = self.start_location.towards(self.game_info.map_center, 10)
        return point.x, point.y

    def assistance(self, state, selected):
        mining = state['game_loop'] >= self.next_mining
        if mining:
            self.next_mining = state['game_loop']+24
        destination, self.attacking, self.search_index = scripted_army_destination(
            state, self.units_by_id, tuple(self.start_location), tuple(self.enemy_start_locations[0]),
            tuple(self.game_info.map_center), [tuple(p) for p in self.expansion_locations_list],
            self.attacking, self.search_index)
        self.assistance_destination = destination
        return self.scout_commands + primitive_assistance(state, selected, self.units_by_id, self.catalog,
            destination, lambda p: self.in_map_bounds(Point2(p)) and self.in_pathing_grid(Point2(p)), mining)

    async def on_step(self, iteration):
        try:
            state = self.view.observe(self.state.response_observation)
            state['map_size'] = [self.game_info.map_size.x, self.game_info.map_size.y]
            loop = state['game_loop']
            claimed = {item['actor'] for item in self.ledger.pending.values()}
            self.scout_commands = self.scout.update(state, claimed, tuple(self.enemy_start_locations[0]), tuple(self.start_location))
            if loop < self.next_plan:
                selected = claimed | self.scout.protected
                assistance = self.assistance(state, selected)
                result = await issue(self.client, assistance) if assistance else pb.ResponseAction()
                if len(result.result) != len(assistance):
                    raise ValueError('Incomplete primitive acknowledgement batch')
                self.result_counts.update(map(str, result.result))
                self.stream.write(json.dumps(dict(phase='micro', observation=state, goals=None,
                    pending=self.ledger.pending, scouting=dict(tag=self.scout.tag, protected=sorted(self.scout.protected), events=self.scout.events), assistance_destination=self.assistance_destination, execution=[],
                    assistance=[c.as_dict() for c in assistance], results=list(result.result)),
                    separators=(',', ':'))+'\n')
                return
            self.record_outcomes(state)
            self.frames += 1
            self.next_plan = loop + 44
            stock, source_goal, full_target = None, None, None
            if self.inventory_library:
                stock = dict(observation_stock(state, self.data))
                target, source_goal = self.inventory_library.select(loop, stock, self.public_race)
                full_target = self.inventory_library.target
                counts = np.array([full_target.get(n, 0) for n in self.model['names']])
                predicted = {n: v-stock.get(n, 0) for n,v in target.items() if v > stock.get(n, 0)}
                queued, active = inventory_queued(state, self.goals, self.catalog, self.unit_names)
            else:
                features = current_features(state, self.vocabulary, self.products, self.profile)
                predicted, counts = predict_goals(self.model, features)
                queued, active = queued_work(state, self.goals, self.catalog, self.unit_names)
            self.requested.update(predicted)
            tags = {u['tag'] for u in state['units'] if u['alliance'] == 1}
            if self.intent_mode:
                self.ledger.events.clear()
            changes = self.ledger.reconcile(active, tags, loop)
            if self.intent_mode:
                self.ledger.plan(predicted, queued, loop)
            else:
                self.ledger.plan(predicted, queued)
            packets = [(await self.client._execute(query=ability_query(sorted(tags), ignore_resources=ignore))).query
                       for ignore in (False, True)]
            available = [{row.unit_tag: {a.ability_id for a in row.abilities}
                          for row in packet.abilities} for packet in packets]
            actual = {tag: {canonical(a, self.catalog) for a in abilities}
                      for tag, abilities in available[0].items()}
            selected = {item['actor'] for item in self.ledger.pending.values()} | self.scout.protected
            commands, tickets, execution = [], [], []
            reserved = reservations(state, self.units_by_id, self.catalog)
            geyser_claims = claimed_geysers(state, self.catalog)
            minerals = state['player'].get('minerals', 0)
            gas = state['player'].get('vespene', 0)
            requests = self.ledger.requests() if self.intent_mode else list(predicted)
            priority, unsupported, cycles = prior_scores(self.prior, requests) if self.prior else ({}, 0, 0)
            requests.sort(key=(lambda g: (-priority[g], g)) if self.prior else
                          (lambda g: (self.last_sent.get(g, -1), self.goals[g]['ability'])))
            allocations = []
            placement_checks = []
            food = state['player'].get('food_cap', 0)-state['player'].get('food_used', 0)
            for goal in requests:
                if self.ledger.remaining(goal) < 1:
                    continue
                info = self.goals[goal]
                if info['upgrade'] is not None and info['upgrade'] in state['upgrades']:
                    continue
                candidates = [u for u in eligible_actors(state, info['ability'], available[1], self.catalog, self.unit_names)
                              if u['tag'] not in selected]
                if not candidates:
                    self.blocks['prerequisite_or_busy:' + goal] += 1
                    continue
                needed_food = self.units_by_id.get(info['unit_type'], {}).get('food_required', 0)
                if self.intent_mode and needed_food > food:
                    self.blocks['supply:' + goal] += 1
                    continue
                if not self.intent_mode and (minerals < info['minerals'] or gas < info['gas']):
                    self.blocks['resource_reservation:' + goal] += 1
                    continue
                point = None
                target = None
                mode = info['descriptor'].get('target', 1)
                if mode == 3:
                    geysers = [u for u in refinery_sites(state, self.catalog)
                               if u['tag'] not in geyser_claims]
                    if not geysers:
                        self.blocks['no_geyser:' + goal] += 1
                        continue
                    target = min(geysers, key=lambda u: math.dist(u['position'][:2], (self.start_location.x, self.start_location.y)))
                    candidates.sort(key=lambda u: math.dist(u['position'][:2], target['position'][:2]))
                elif mode == 2:
                    point = self.building_point(goal, state)
                    if point is None:
                        self.blocks['no_placement_seed:' + goal] += 1
                        continue
                    candidates.sort(key=lambda u: math.dist(u['position'][:2], point))
                else:
                    candidates.sort(key=lambda u: u['tag'])
                actor = candidates[0]
                if not self.intent_mode and canonical(info['ability'], self.catalog) not in actual.get(actor['tag'], set()):
                    self.blocks['engine_unavailable:' + goal] += 1
                    continue
                command = Command(info['ability'], (actor['tag'],), target_point=point,
                                  target_unit=target['tag'] if target else None)
                resolved, placement = await resolve_production_placement(self.client, command, self.catalog, state, info['unit_type'], reserved)
                if info['descriptor'].get('is_building') or not resolved:
                    placement_checks.append(dict(goal=goal, actor=actor['tag'], command=command.as_dict(), diagnostics=placement, resolved=bool(resolved)))
                if not resolved:
                    self.blocks['placement:' + goal] += 1
                    continue
                command = resolved[0]
                if self.intent_mode:
                    affordable = minerals >= info['minerals'] and gas >= info['gas']
                    allocation = dict(goal=goal, before=[minerals, gas], cost=[info['minerals'], info['gas']], affordable=affordable)
                    allocations.append(allocation)
                    if not affordable:
                        minerals, gas = remaining_budget((minerals, gas), (info['minerals'], info['gas']))
                        allocation.update(outcome='reserved', after=[minerals, gas])
                        self.blocks['resource_reservation:' + goal] += 1
                        continue
                    if canonical(info['ability'], self.catalog) not in actual.get(actor['tag'], set()):
                        allocation.update(outcome='engine_unavailable', after=[minerals, gas])
                        self.blocks['engine_unavailable:' + goal] += 1
                        continue
                    allocation.update(outcome='submitted', after=[minerals-info['minerals'], gas-info['gas']])
                if target is not None:
                    geyser_claims.add(target['tag'])
                if command.target_point is not None and info['descriptor'].get('is_building'):
                    x, y = command.target_point
                    reserved.extend(site_reservations(info['unit_type'], (x, y),
                        info['descriptor'].get('footprint_radius', 1)))
                ticket = self.ledger.reserve(goal, actor['tag'], loop)
                commands.append(command)
                tickets.append((ticket, goal))
                execution.append(dict(goal=goal, ticket=ticket, command=command.as_dict(), placement=placement))
                selected.add(actor['tag'])
                minerals -= info['minerals']
                gas -= info['gas']
                food -= needed_food
            assistance = self.assistance(state, set(selected))
            all_commands = commands + assistance
            result = await issue(self.client, all_commands) if all_commands else pb.ResponseAction()
            if len(result.result) != len(all_commands):
                raise ValueError('Incomplete native acknowledgement batch')
            for (ticket, goal), code in zip(tickets, result.result, strict=False):
                self.ledger.acknowledge(ticket, code == 1)
                if code == 1:
                    self.acknowledged[goal] += 1
                    self.last_sent[goal] = loop
            self.result_counts.update(map(str, result.result))
            self.stream.write(json.dumps(dict(phase='forecast', observation=state, goals=predicted,
                raw_counts=counts.tolist(), queued=queued, reconciliation=changes,
                inventory_stock=stock, source_goal=source_goal, inventory_target=full_target,
                placement_checks=placement_checks,
                priority=priority, unsupported_prior_pairs=unsupported, prior_cycles=cycles, allocations=allocations,
                intents=self.ledger.intents if self.intent_mode else {},
                intent_events=self.ledger.events if self.intent_mode else [],
                recent_fulfilments=self.ledger.recent if self.intent_mode else [],
                effective_queued=self.ledger.effective_queued if self.intent_mode else queued,
                pending=self.ledger.pending, scouting=dict(tag=self.scout.tag, protected=sorted(self.scout.protected), events=self.scout.events), assistance_destination=self.assistance_destination, execution=execution,
                assistance=[c.as_dict() for c in assistance], results=list(result.result)),
                separators=(',', ':'))+'\n')
        except Exception as error:
            self.callback_error = repr(error)
            raise


def play_production_goals(job):
    from loguru import logger
    logger.remove()
    output = Path(job['output'])
    output.mkdir(parents=True, exist_ok=False)
    checksum = digest(job['model'])
    prior_checksum = digest(job['prior']) if job.get('prior') else None
    with gzip.open(output/'trace.jsonl.gz', 'xt') as stream:
        bot = ProductionGoalBot(job, stream)
        result = run_game(validate_map(job['map']),
            [Bot(Race.Terran, bot), Computer(Race[job['race']], Difficulty[job['difficulty']], AIBuild[job['build']])],
            realtime=False, random_seed=job['seed'], game_time_limit=job['seconds'],
            save_replay_as=str(output/'game.SC2Replay'))
    if bot.callback_error or not bot.frames:
        raise RuntimeError(bot.callback_error or 'No goal-planning frames')
    if digest(job['model']) != checksum:
        raise ValueError('Checkpoint changed during native play')
    if prior_checksum and digest(job['prior']) != prior_checksum:
        raise ValueError('Human prior changed during native play')
    report = dict(status='truncated' if result.name == 'Tie' else 'completed', result=result.name,
                  model_sha256=checksum, prior_sha256=prior_checksum, training=False, rl=False, job=job,
                  frames=bot.frames, requested=dict(bot.requested), acknowledged=dict(bot.acknowledged),
                  blocks=dict(bot.blocks), results=dict(bot.result_counts),
                  production=bot.production, snapshots=bot.snapshots,
                  goal_library=job.get('goal_library'),
                  assistance='scripted mining/gas assignment, protected worker scouting, construction execution, MULEs, depot lowering, attack timing/destinations, per-unit combat micro; production choices learned')
    (output/'episode.json').write_text(json.dumps(report, indent=2)+'\n')
    return report
