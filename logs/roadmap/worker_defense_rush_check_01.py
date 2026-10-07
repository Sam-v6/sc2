"""Diagnostic: rerun the six VeryHard Rush losses (same seeds) with worker defense. Not a fresh benchmark."""
import hashlib
import json
from pathlib import Path
from src.runner import play_job
from src.runtime import supervise

OUT = Path('logs/roadmap/worker-defense-rush-check-01')


def main():
    OUT.mkdir(exist_ok=False)
    contract = json.load(open('logs/roadmap/scripted-veryhard-panel-01/panel/contract.json'))
    jobs = [dict(j, replay=str((OUT/f"{j['race']}-{j['build']}-{j['map']}"/'game.SC2Replay').resolve()))
            for j in contract['jobs'] if j['build'] == 'Rush']
    bindings = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
                for p in (__file__, 'src/bots/primitive_terran.py', 'src/bots/terran_primitives.py')}
    results = []
    for job in jobs:
        Path(job['replay']).parent.mkdir()
        r = dict(job=job, **supervise(play_job, (job,), 300))
        results.append(r)
        print(job['race'], job['map'], r['status'], r.get('result'), round(r.get('game_seconds', 0)),
              r.get('primitives', {}).get('defense_commands'), flush=True)
    (OUT/'report.json').write_text(json.dumps(dict(results=results, bindings=bindings), indent=2)+'\n')


if __name__ == '__main__':
    main()
