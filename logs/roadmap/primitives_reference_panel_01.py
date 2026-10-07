"""Measure existing Reaper primitives, with no training or strategic changes."""
import gzip
import hashlib
import json
import threading
import time
from collections import Counter
from pathlib import Path

import psutil
from sc2.data import AIBuild, Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer

from src.bots.mass_reaper import MassReaperBot
from src.runner import validate_map
from src.runtime import supervise

OUT = Path('logs/roadmap/primitives-reference-01/panel')


class ObservedReaper(MassReaperBot):
    def __init__(self, stream):
        super().__init__()
        self.stream = stream
        self.requested_game_step = 8
        self.next_sample = 0

    async def custom_on_step(self, iteration):
        await super().custom_on_step(iteration)
        if self.state.game_loop < self.next_sample:
            return
        self.next_sample = self.state.game_loop + 48
        row = dict(loop=self.state.game_loop, seconds=self.time,
                   minerals=self.minerals, gas=self.vespene,
                   supply_used=self.supply_used, supply_cap=self.supply_cap,
                   workers=self.workers.amount, idle_workers=self.workers.idle.amount,
                   gathering_workers=self.workers.gathering.amount,
                   reapers=self.units.filter(lambda u: u.type_id.name == 'REAPER').amount,
                   own_units=dict(Counter(u.type_id.name for u in self.units | self.structures)),
                   score={k: float(v) for k, v in self.state.score.summary})
        self.stream.write(json.dumps(row)+'\n')


def play(job):
    from loguru import logger
    logger.remove()
    path = Path(job['output'])
    path.mkdir(exist_ok=False)
    with gzip.open(path/'telemetry.jsonl.gz', 'xt') as stream:
        bot = ObservedReaper(stream)
        result = run_game(validate_map('AcropolisLE'),
                          [Bot(Race.Terran, bot), Computer(Race[job['race']], Difficulty.Hard,
                                                         AIBuild[job['build']])],
                          realtime=False, random_seed=job['seed'], game_time_limit=1200,
                          save_replay_as=str(path/'game.SC2Replay'))
    if bot.callback_error or not bot.started:
        raise RuntimeError(bot.callback_error or 'Bot did not start')
    replay = path/'game.SC2Replay'
    assert replay.is_file() and replay.stat().st_size
    return dict(status='truncated' if result.name == 'Tie' else 'completed',
                result=result.name, game_seconds=bot.time, replay_bytes=replay.stat().st_size)


def main():
    OUT.mkdir(exist_ok=False)
    paths = [Path(__file__), Path('src/bots/mass_reaper.py'), Path('src/common/void_bot_base.py')]
    bindings = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    jobs = [dict(race=r, build=b, seed=817101+i,
                 output=str((OUT/f'{r}-{b}').resolve()))
            for i, (r, b) in enumerate((r, b) for r in ('Terran', 'Zerg', 'Protoss')
                                      for b in ('Rush', 'Macro'))]
    contract = dict(jobs=jobs, bindings=bindings, bot='existing scripted MassReaperBot',
                    training=False, rl=False, game_seconds=1200, wall_seconds=300,
                    game_step=8, whole_host_cpu_limit=80)
    (OUT/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    stop, done = threading.Event(), threading.Event()
    samples = []
    def watch():
        high = 0
        while not done.is_set():
            cpu = psutil.cpu_percent(interval=1)
            samples.append(cpu)
            high = high+1 if cpu > 80 else 0
            if high >= 3:
                stop.set()
            done.wait(4)
    assert psutil.cpu_percent(interval=1) < 70, 'Insufficient CPU headroom'
    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    results = []
    try:
        for job in jobs:
            if stop.is_set():
                break
            result = dict(job=job, **supervise(play, (job,), 300, stop_event=stop))
            results.append(result)
            print(json.dumps(result), flush=True)
            (OUT/'progress.json').write_text(json.dumps(results, indent=2)+'\n')
            if result['status'] not in ('completed', 'truncated'):
                break
    finally:
        done.set()
        watcher.join(6)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in bindings.items())
    (OUT/'report.json').write_text(json.dumps(dict(results=results, cpu_samples=samples,
                                                  bindings=bindings, training=False,
                                                  peak_cpu=max(samples, default=0)), indent=2)+'\n')


if __name__ == '__main__':
    main()
