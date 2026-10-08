"""Rerun panel game 830017 on frozen source: it started while primitive_terran.py was briefly edited."""
import json
from pathlib import Path
from src.runner import play_job
from src.runtime import supervise


def main():
    c = json.load(open('logs/roadmap/scripted-veryhard-panel-01/panel/contract.json'))
    job = next(j for j in c['jobs'] if j['seed'] == 830017)
    out = Path('logs/roadmap/scripted-veryhard-panel-01/rerun-830017')
    out.mkdir(exist_ok=False)
    job = dict(job, replay=str((out/'game.SC2Replay').resolve()))
    r = supervise(play_job, (job,), 300)
    (out/'receipt.json').write_text(json.dumps(dict(job=job, **r), indent=2)+'\n')
    print(job['race'], job['build'], job['map'], r['status'], r.get('result'), 'original: Victory')


if __name__ == '__main__':
    main()
