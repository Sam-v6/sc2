"""Frozen matched execution diagnostic, no training or RL."""
import hashlib
import json
import threading
import time
from pathlib import Path
import psutil
from src.learning.production_goal_play import play_production_goals
from src.runtime import supervise

from dataclasses import replace
import math
import src.learning.production_goal_play as goal_play
original_resolver = goal_play.resolve_production_placement
async def diagnostic_resolver(client, command, catalog, state, unit_type, reserved):
    commands, trace = await original_resolver(client, command, catalog, state, unit_type, reserved)
    if not commands and command.target_point is not None and catalog[command.ability].get('is_building'):
        center = tuple(v/2 for v in state['map_size'])
        for base in state['units']:
            if base['alliance'] != 1 or base['unit_type'] not in (18,132,130) or base.get('build_progress',1) < 1 or base.get('is_flying'):
                continue
            pos = base['position'][:2]; length = math.dist(pos,center)
            point = tuple(a+10*(b-a)/length for a,b in zip(pos,center))
            if math.dist(point,command.target_point)<.01:
                continue
            alternatives, diagnostics = await original_resolver(client, replace(command,target_point=point),catalog,state,unit_type,reserved)
            trace.append(dict(source='owned_base_probe',base=base['tag'],seed=point,commands=[c.as_dict() for c in alternatives],diagnostics=diagnostics))
    return commands, trace
goal_play.resolve_production_placement = diagnostic_resolver

ROOT = Path('logs/roadmap')
OUT = ROOT/'human-placement-native-02'
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=False)
    model = ROOT/'human-production-goals-02/model.pkl'
    prior = ROOT/'human-prior-openings-01.json'
    assert sha(model) == 'bba44d92c8bf2c5c62b5f529ca0078e1fa4daa7c3e2db2fc59697d4c0b423282'
    assert json.loads(prior.read_text())['status'] == 'verified_opening_prior_diagnostic'
    profile = ROOT/'professional-observation-profile-01.json'
    base = dict(model=str(model.resolve()), prior=str(prior.resolve()), profile=str(profile.resolve()),
        vocabulary=json.loads((ROOT/'joint-professional-fit-05/configuration.json').read_text())['vocabulary'],
        map='AcropolisLE', race='Zerg', difficulty='VeryEasy', build='Rush', seed=816201, seconds=600)
    jobs = [dict(base, intent_execution=True, output=str((OUT/name).resolve()),
                 **({'goal_library': str((ROOT/'human-goal-retrieval-01').resolve())} if name=='I' else {}))
            for name in ['I']]
    sources = [Path(__file__), model, prior, profile,
        Path('docs/superpowers/plans/2026-10-06-owned-base-placement-probe.md'),
        Path('src/bots/terran_primitives.py')] + list(Path('src/learning').glob('*.py'))
    sources += list((ROOT/'human-goal-retrieval-01').glob('*'))
    sources = [p for p in sources if p.is_file()]
    bindings = {str(p): sha(p) for p in sources}
    (OUT/'protocol.json').write_text(json.dumps(dict(jobs=jobs, bindings=bindings,
        gates=dict(barracks_start_seconds=90, military_births=4, living_workers=20), training=False, rl=False), indent=2)+'\n')
    for job in jobs:
        baseline = psutil.cpu_percent(interval=1)
        assert baseline < 70, baseline
        stop, done, samples = threading.Event(), threading.Event(), []
        def watch():
            high = 0
            while not done.is_set():
                cpu = psutil.cpu_percent(interval=1)
                samples.append(dict(time=time.time(), cpu=cpu))
                high = high+1 if cpu > 80 else 0
                if high >= 3:
                    stop.set()
                done.wait(4)
        watcher = threading.Thread(target=watch, daemon=True)
        watcher.start()
        result = supervise(play_production_goals, (job,), 240, stop_event=stop)
        done.set()
        watcher.join(5)
        for path, checksum in bindings.items():
            assert sha(path) == checksum, path
        report = dict(result=result, baseline_cpu=baseline,
            peak_cpu=max([baseline]+[s['cpu'] for s in samples]), samples=samples)
        name = Path(job['output']).name
        (OUT/f'{name}.supervision.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(dict(arm=name, status=result['status'], error=result.get('error'),
            wall_seconds=result['wall_seconds'], peak_cpu=report['peak_cpu'])), flush=True)
if __name__ == '__main__':
    main()
