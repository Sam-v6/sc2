"""Micro sandbox v2: debug-spawned attacks into the VeryHard Terran AI outside its base; the AI controls its side.

Unlike v1, every enemy army unit on the map is removed before each spawn, so the AI's own army never joins a
fight, and each game runs 12 fights.

Usage: micro_sandbox_01.py OUT_DIR VARIANT SCENARIO SEED_START GAMES
VARIANT: 'combat' (this checkout's src.bots.terran_primitives.combat_command) or 'amove' (plain attack-move).
SCENARIO: a key of SCENARIOS. Each game runs TRIALS fights; a fight ends after 30 game s or when a side is gone.
Run the same command in two worktrees to compare code versions on identical seeds. 80% whole-host CPU guard.
"""
import hashlib
import json
import math
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psutil
from sc2.bot_ai import BotAI
from sc2.data import AIBuild, Difficulty, Race
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.position import Point2
from s2clientprotocol import sc2api_pb2 as pb

from src.bots.terran_primitives import changes_order, combat_command
from src.learning.gameplay import Command, PlayerView, protocol_dict
from src.learning.live import issue
from src.runner import validate_map
from src.runtime import supervise

WORKERS, TRIALS, MAP = 4, 12, 'AcropolisLE'
SOURCES = ['src/bots/terran_primitives.py', 'src/learning/gameplay.py', 'src/learning/live.py']
ARMY = {U.MARINE, U.MARAUDER, U.SIEGETANK, U.SIEGETANKSIEGED, U.MEDIVAC, U.VIKINGFIGHTER}
# (ours, theirs): lists of (unit type, count).
SCENARIOS = {
    'marines': ([(U.MARINE, 20)], [(U.MARINE, 20)]),
    'mixed': ([(U.MARINE, 16), (U.SIEGETANK, 2)], [(U.MARINE, 16), (U.SIEGETANK, 2)]),
    'into-siege': ([(U.MARINE, 24)], [(U.MARINE, 10), (U.SIEGETANKSIEGED, 2)]),
}


class Sandbox(BotAI):
    def __init__(self, variant, scenario):
        super().__init__()
        self.variant, self.scenario = variant, scenario
        self.view, self.trials, self.phase, self.enemy_positions = PlayerView(), [], 'idle', {}

    async def on_start(self):
        self.client.game_step = 8
        response = await self.client._execute(data=pb.RequestData(unit_type_id=True))
        self.types = {u['unit_id']: u for u in protocol_dict(response.data)['units']}
        # The AI pulls units home from the open map, so its side spawns outside its base, where it defends,
        # and ours 14 further out attacks in: the fight our TvT losses are made of.
        here, there = self.start_location, self.enemy_start_locations[0]
        self.theirs = there.towards(here, 16)
        self.ours = self.theirs.towards(here, 14)
        await self.client.debug_show_map()  # the fights start out of sight range; only our view changes

    def fighters(self, units):
        return units.filter(lambda u: u.type_id in ARMY and u.distance_to(self.ours) < 40)

    async def on_step(self, iteration):
        if self.phase == 'idle' and self.time > 5:
            stray = self.enemy_units.filter(lambda u: not u.is_structure and u.type_id not in (U.SCV, U.MULE))
            if stray:
                await self.client.debug_kill_unit(stray.tags)
            ours, theirs = SCENARIOS[self.scenario]
            await self.client.debug_create_unit([[t, n, self.ours, 1] for t, n in ours]
                                                + [[t, n, self.theirs, 2] for t, n in theirs])
            self.phase, self.start = 'fight', self.time + 1
            return
        if self.phase == 'fight' and self.time > self.start:
            own, enemy = self.fighters(self.units), self.fighters(self.enemy_units)
            if self.time - self.start > 30 or not own or (not enemy and self.time - self.start > 3):
                self.trials.append(dict(own_hp=sum(u.health for u in own), own_alive=own.amount,
                                        enemy_hp=sum(u.health for u in enemy), enemy_alive=enemy.amount,
                                        seconds=self.time - self.start))
                await self.client.debug_kill_unit(own.tags | enemy.tags)
                self.phase, self.resume = ('done' if len(self.trials) >= TRIALS else 'wait'), self.time + 3
                if self.phase == 'done':
                    await self.client.leave()
                return
            state = self.view.observe(self.state.response_observation)
            commands = []
            if self.variant == 'amove':
                for u in own:
                    if not u.orders:
                        commands.append(Command(23, (u.tag,), target_point=tuple(self.theirs)))
            else:
                enemies = [dict(e, previous_position=self.enemy_positions.get(e['tag'], e['position']))
                           for e in state['units'] if e['alliance'] == 4]
                self.enemy_positions = {e['tag']: e['position'] for e in enemies}
                tags = own.tags
                for unit in state['units']:
                    if unit['tag'] not in tags:
                        continue
                    command = combat_command(unit, enemies, self.types, tuple(self.theirs),
                                             lambda p: self.in_map_bounds(Point2(p)) and self.in_pathing_grid(Point2(p)))
                    if isinstance(command, tuple):
                        commands.extend(command)
                    elif command and changes_order(unit, command):
                        commands.append(command)
            if commands:
                await issue(self.client, commands)
        if self.phase == 'wait' and self.time > self.resume:
            self.phase = 'idle'


def play(job):
    bot = Sandbox(job['variant'], job['scenario'])
    run_game(validate_map(MAP), [Bot(Race.Terran, bot), Computer(Race.Terran, Difficulty.VeryHard, AIBuild.Macro)],
             realtime=False, random_seed=job['seed'], game_time_limit=600)
    return dict(status='completed', result=None, trials=bot.trials)


def main():
    out, variant, scenario, seed, games = Path(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
    out.mkdir(parents=True, exist_ok=False)
    bindings = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in [__file__, *SOURCES]}
    jobs = [dict(variant=variant, scenario=scenario, seed=seed + i) for i in range(games)]
    stop, done = threading.Event(), threading.Event()

    def watch():
        high = 0
        while not done.is_set():
            high = high + 1 if psutil.cpu_percent(interval=1) > 80 else 0
            if high >= 3:
                stop.set()
            done.wait(4)

    threading.Thread(target=watch, daemon=True).start()

    def run(job):
        if stop.is_set():
            return dict(job=job, status='skipped_cpu_guard')
        r = supervise(play, (job,), 300, stop_event=stop)
        print(json.dumps(dict(seed=job['seed'], status=r['status'], trials=len(r.get('trials') or []))), flush=True)
        return dict(job=job, **r)

    try:
        with ThreadPoolExecutor(WORKERS) as pool:
            results = list(pool.map(run, jobs))
    finally:
        done.set()
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in bindings.items())
    trials = [t for r in results for t in r.get('trials') or []]
    summary = dict(trials=len(trials),
                   own_hp=sum(t['own_hp'] for t in trials) / max(len(trials), 1),
                   enemy_hp=sum(t['enemy_hp'] for t in trials) / max(len(trials), 1),
                   won=sum(t['own_alive'] > 0 and t['enemy_alive'] == 0 for t in trials))
    (out / 'report.json').write_text(json.dumps(dict(summary=summary, results=results, bindings=bindings), indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
