"""Bounded native assisted human-outcome imitation. No RL or strategic script."""

import gzip
import hashlib
import json
import math
import pickle
from collections import Counter
from pathlib import Path

from sc2.bot_ai import BotAI
from sc2.data import Race, Difficulty, AIBuild
from sc2.main import run_game
from sc2.player import Bot, Computer
from s2clientprotocol import sc2api_pb2 as pb

from src.learning.actor_selection import construction_products
from src.learning.entity_execution import validate_order_aliases
from src.learning.gameplay import Command, PlayerView, protocol_dict
from src.learning.imitation_play import idle_worker_harvest
from src.learning.live import ability_query, issue
from src.learning.production_clearance import reservations, resolve_production_placement, PRODUCERS, claimed_geysers
from src.learning.production_execution import (canonical, eligible_actors,
                                              goal_catalog, queued_work)
from src.learning.production_goal_policy import current_features, predict_goals
from src.learning.production_ledger import ProductionLedger
from src.runner import validate_map


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
        self.ledger = ProductionLedger()
        self.last_sent = {}
        self.next_plan = 0
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
        own = [u for u in state['units'] if u['alliance'] == 1]
        workers = [u for u in own if u['unit_type'] == 45 and u['tag'] not in selected
                   and not any(self.catalog.get(o['ability_id'], {}).get('friendly_name', '').startswith('Build ')
                               for o in u.get('orders', []))]
        commands = []
        for refinery in [u for u in own if self.unit_names[u['unit_type']] == 'Refinery'
                         and u.get('build_progress', 1) == 1]:
            shortage = max(0, 3 - refinery.get('assigned_harvesters', 0))
            gas_tags = {u['tag'] for u in workers if any(o.get('target_unit_tag') == refinery['tag']
                                                      for o in u.get('orders', []))}
            candidates = [u for u in workers if u['tag'] not in gas_tags and u['tag'] not in selected]
            candidates.sort(key=lambda u: math.dist(u['position'][:2], refinery['position'][:2]))
            for worker in candidates[:shortage]:
                commands.append(Command(295, (worker['tag'],), target_unit=refinery['tag']))
                selected.add(worker['tag'])
        commands.extend(idle_worker_harvest(state, selected))
        enemies = [u for u in state['units'] if u['alliance'] == 4]
        if enemies:
            for unit in own:
                descriptor = self.units_by_id[unit['unit_type']]
                if unit['tag'] in selected or 8 in descriptor.get('attributes', []) or unit['unit_type'] == 45 or not descriptor.get('weapons'):
                    continue
                enemy = min(enemies, key=lambda e: math.dist(unit['position'][:2], e['position'][:2]))
                commands.append(Command(23, (unit['tag'],), target_unit=enemy['tag']))
        return commands

    async def on_step(self, iteration):
        try:
            state = self.view.observe(self.state.response_observation)
            state['map_size'] = [self.game_info.map_size.x, self.game_info.map_size.y]
            loop = state['game_loop']
            if loop < self.next_plan:
                return
            self.record_outcomes(state)
            self.frames += 1
            self.next_plan = loop + 44
            features = current_features(state, self.vocabulary, self.products, self.profile)
            predicted, counts = predict_goals(self.model, features)
            self.requested.update(predicted)
            queued, active = queued_work(state, self.goals, self.catalog, self.unit_names)
            tags = {u['tag'] for u in state['units'] if u['alliance'] == 1}
            changes = self.ledger.reconcile(active, tags, loop)
            self.ledger.plan(predicted, queued)
            packets = [(await self.client._execute(query=ability_query(sorted(tags), ignore_resources=ignore))).query
                       for ignore in (False, True)]
            available = [{row.unit_tag: {a.ability_id for a in row.abilities}
                          for row in packet.abilities} for packet in packets]
            actual = {tag: {canonical(a, self.catalog) for a in abilities}
                      for tag, abilities in available[0].items()}
            selected = {item['actor'] for item in self.ledger.pending.values()}
            commands, tickets, execution = [], [], []
            reserved = reservations(state, self.units_by_id, self.catalog)
            geyser_claims = claimed_geysers(state, self.catalog)
            minerals = state['player'].get('minerals', 0)
            gas = state['player'].get('vespene', 0)
            requests = sorted(predicted, key=lambda g: (self.last_sent.get(g, -1), self.goals[g]['ability']))
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
                if minerals < info['minerals'] or gas < info['gas']:
                    self.blocks['resource_reservation:' + goal] += 1
                    break
                point = None
                target = None
                mode = info['descriptor'].get('target', 1)
                if mode == 3:
                    geysers = [u for u in state['units'] if u['alliance'] == 3 and u.get('vespene_contents', 0) > 0 and u['tag'] not in geyser_claims
                               and not any(v['unit_type'] == info['unit_type'] and math.dist(v['position'][:2], u['position'][:2]) < 1
                                           for v in state['units'] if v['alliance'] == 1)]
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
                if canonical(info['ability'], self.catalog) not in actual.get(actor['tag'], set()):
                    self.blocks['engine_unavailable:' + goal] += 1
                    continue
                command = Command(info['ability'], (actor['tag'],), target_point=point,
                                  target_unit=target['tag'] if target else None)
                resolved, placement = await resolve_production_placement(self.client, command, self.catalog, state, info['unit_type'], reserved)
                if not resolved:
                    self.blocks['placement:' + goal] += 1
                    continue
                command = resolved[0]
                if target is not None:
                    geyser_claims.add(target['tag'])
                if command.target_point is not None and info['descriptor'].get('is_building'):
                    x, y = command.target_point
                    radius = 2.5 if info['unit_type'] in PRODUCERS else info['descriptor'].get('footprint_radius', 1)
                    reserved.append((x, y, radius))
                    if info['unit_type'] in PRODUCERS:
                        reserved.append((x + 2.5, y - .5, 1))
                ticket = self.ledger.reserve(goal, actor['tag'], loop)
                commands.append(command)
                tickets.append((ticket, goal))
                execution.append(dict(goal=goal, command=command.as_dict(), placement=placement))
                selected.add(actor['tag'])
                minerals -= info['minerals']
                gas -= info['gas']
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
            self.stream.write(json.dumps(dict(observation=state, goals=predicted,
                raw_counts=counts.tolist(), queued=queued, reconciliation=changes,
                pending=self.ledger.pending, execution=execution,
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
    report = dict(status='truncated' if result.name == 'Tie' else 'completed', result=result.name,
                  model_sha256=checksum, training=False, rl=False, job=job,
                  frames=bot.frames, requested=dict(bot.requested), acknowledged=dict(bot.acknowledged),
                  blocks=dict(bot.blocks), results=dict(bot.result_counts),
                  production=bot.production, snapshots=bot.snapshots,
                  assistance='placement, resource-worker execution, visible-contact combat')
    (output/'episode.json').write_text(json.dumps(report, indent=2)+'\n')
    return report
