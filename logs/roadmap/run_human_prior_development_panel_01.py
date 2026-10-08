"""Frozen matched execution diagnostic, no training or RL."""
import hashlib
import json
import threading
import time
from pathlib import Path
import psutil
from src.learning.production_goal_play import play_production_goals
from src.runtime import supervise

ROOT = Path('logs/roadmap')
OUT = ROOT/'human-prior-native-panel-01'
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
        map='AcropolisLE', race='Zerg', difficulty='VeryEasy', build='Macro', seed=816003, seconds=600)
    jobs = [dict(base, race=race, build=build, seed=816101+i, intent_execution=True,
                 output=str((OUT/f'{race}-{build}').resolve()))
            for i, (race, build) in enumerate((r,b) for r in ('Zerg','Protoss','Terran') for b in ('Rush','Macro'))]
    sources = [Path(__file__), model, prior, profile,
        Path('docs/superpowers/plans/2026-10-06-human-prior-development-panel.md'),
        Path('src/bots/terran_primitives.py')] + list(Path('src/learning').glob('*.py'))
    bindings = {str(p): sha(p) for p in sources}
    (OUT/'protocol.json').write_text(json.dumps(dict(jobs=jobs, bindings=bindings,
        gates=dict(barracks_start_seconds=90, military_births=4, living_workers=20, sustained_phases=[[120,300],[300,600]], phase_workers=3, phase_military=5, joint_workers=30, joint_army=8), training=False, rl=False), indent=2)+'\n')
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
