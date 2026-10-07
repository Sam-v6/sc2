"""Native adapter execution test with an explicitly scripted production fixture."""
import gzip
import hashlib
import json
import threading
import time
from pathlib import Path
import psutil
from sc2.data import AIBuild, Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer
from src.bots.primitive_terran import PrimitiveTerranBot
from src.bots.terran_primitives import scripted_targets
from src.learning.entity_play import JointImitationBot
from src.learning.production_scout import WorkerScout
from src.runner import validate_map
from src.runtime import supervise

OUT = Path('logs/roadmap/broad-scout-canary-02')

class AdapterFixture(PrimitiveTerranBot):
    def __init__(self):
        super().__init__()
        self.requested_game_step = 8
        self.trace_path = str(OUT/'fixture.jsonl.gz')
        self.scouted = True  # Disable the baseline's own scout.
        self.scout = WorkerScout()
        self.next_mining = 0
        self.primitive_commands = 0
        self.primitive_results = {}

    def free_worker(self, point):
        workers = self.workers.filter(lambda w: (w.is_idle or w.is_gathering)
            and w.tag not in self.unit_tags_received_action and w.tag != self.scout.tag)
        return workers.closest_to(point) if workers else None

    async def on_start(self):
        await super().on_start()
        self.units_by_id = self.types

    async def on_step(self, iteration):
        state = self.view.observe(self.state.response_observation)
        state['map_size'] = [self.game_info.map_size.x, self.game_info.map_size.y]
        if self.state.game_loop >= self.next_macro:
            self.next_macro = self.state.game_loop+24
            await self.macro(state, scripted_targets(state))
        protected = self.unit_tags_received_action
        commands, result = await JointImitationBot.run_primitives(self, state, protected)
        errors = [dict(ability=e.ability_id, tag=e.unit_tag, result=e.result)
                  for e in self.state.response_observation.action_errors]
        self.stream.write(json.dumps(dict(loop=state['game_loop'], observation=state,
            assistance=[c.as_dict() for c in commands], results=list(result.result),
            scout_events=self.scout.events, scout_protected=sorted(self.scout.protected),
            fixture_protected=sorted(protected), delayed_errors=errors,
            collected_minerals=self.state.score.collected_minerals))+'\n')


def play():
    bot = AdapterFixture()
    result = run_game(validate_map('AcropolisLE'),
        [Bot(Race.Terran, bot), Computer(Race.Zerg, Difficulty.VeryEasy, AIBuild.Macro)],
        realtime=False, random_seed=823002, game_time_limit=200,
        save_replay_as=str(OUT/'game.SC2Replay'))
    return dict(result=result.name, primitive_results=bot.primitive_results,
                learned_commands=0, scripted_production_fixture=True)


def main():
    OUT.mkdir(exist_ok=False)
    paths = [Path(__file__), Path('src/learning/entity_play.py'),
             Path('src/learning/production_scout.py'), Path('src/learning/production_primitives.py'),
             Path('src/bots/primitive_terran.py'), Path('src/bots/terran_primitives.py')]
    bindings = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (OUT/'contract.json').write_text(json.dumps(dict(bindings=bindings,
        seed=823002, seconds=200, wall_seconds=120, cpu_limit=80,
        training=False, rl=False, learned_competence=False,
        production='Existing scripted baseline, only an execution fixture',
        gates=['scout selected and protected', 'native Move accepted',
               'native Gather return accepted', 'observed return mining order',
               'income increases', 'no raw or delayed action errors']),indent=2)+'\n')
    stop, done, samples = threading.Event(), threading.Event(), []
    def watch():
        high=0
        while not done.is_set():
            cpu=psutil.cpu_percent(interval=1)
            samples.append(cpu)
            high=high+1 if cpu>80 else 0
            if high>=3:
                stop.set()
            done.wait(1)
    watcher=threading.Thread(target=watch,daemon=True)
    watcher.start()
    result=supervise(play, (), 120, stop_event=stop)
    done.set()
    watcher.join(3)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in bindings.items())
    report=dict(supervision=result, peak_cpu=max(samples,default=0),samples=samples)
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)

if __name__=='__main__':
    main()
