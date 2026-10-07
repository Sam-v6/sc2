from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from src.learning.imitation_play import play_job
from src.runtime import supervise
from src.learning.broad_train import combat_return


def run(job):
    return supervise(play_job, (job,), job['wall_seconds'])


def main():
    root = Path('logs/roadmap/cadence-screen-01')
    root.mkdir(exist_ok=False)
    common = dict(
        policy=str(Path('logs/roadmap/imitation-prefix-240-01/policy.npz').resolve()),
        actor_policy=str(Path('logs/roadmap/actor-prefix-240-01/actors.npz').resolve()),
        argument_policy=str(Path('logs/roadmap/arguments-prefix-240-01/arguments.npz').resolve()),
        spatial_policy=str(Path('logs/roadmap/spatial-prefix-240-01/spatial.npz').resolve()),
        residual_policy=str(Path('logs/roadmap/broad-rl-24-01/zero.npz').resolve()),
        difficulty='VeryEasy',build='RandomBuild',map='Simple64',seconds=600,
        step=4,initial_harvest=False,idle_worker_harvest=True,
        wait_unavailable=False,sample=True,wall_seconds=240)
    jobs=[]
    for i in range(6):
        for arm in ('fixed','learned'):
            jobs.append(dict(common,race=('Terran','Protoss','Zerg')[i%3],
                seed=41600+i,fixed_cadence=arm=='fixed',learned_cadence=arm=='learned',
                output=str((root/f'case-{i:02d}-{arm}').resolve())))
    contract = dict(scope='execution screening only; no learning updates',jobs=jobs,
        component_sha256={k:hashlib.sha256(Path(v).read_bytes()).hexdigest()
            for k,v in common.items() if k.endswith('policy')},
        source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__),Path('src/learning/imitation_play.py'),
                      Path('logs/roadmap/cadence-execution-audit.py'))},
        gate='more completed army units in at least four of six pairs AND mean ordinary combat return not worse; no automatic RL extension')
    (root/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    started=time.monotonic()
    with ThreadPoolExecutor(max_workers=3) as pool:
        receipts=list(pool.map(run,jobs))
    (root/'receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    if any(r['status'] not in ('completed','truncated') for r in receipts):
        raise RuntimeError('Native failure; timing comparison invalid')
    subprocess.run([sys.executable,'logs/roadmap/cadence-execution-audit.py',str(root)],check=True)
    audit={r['game']:r for r in json.loads((root/'execution-audit.json').read_text())}
    pairs=[]
    for i in range(6):
        fixed,learned=receipts[2*i:2*i+2]
        a,b=audit[f'case-{i:02d}-fixed'],audit[f'case-{i:02d}-learned']
        pairs.append(dict(case=i,race=fixed['race'],seed=fixed['seed'],
            fixed_completed_army=a['completed_army_units'],
            learned_completed_army=b['completed_army_units'],
            completed_army_delta=b['completed_army_units']-a['completed_army_units'],
            combat_return_delta=combat_return(learned)-combat_return(fixed),
            fixed_queue_full_per_command=a['queue_full_per_command'],
            learned_queue_full_per_command=b['queue_full_per_command'],
            fixed_possible_construction_interruptions=a['possible_construction_interruptions'],
            learned_possible_construction_interruptions=b['possible_construction_interruptions']))
    improved=sum(p['completed_army_delta']>0 for p in pairs)
    delta=sum(p['combat_return_delta'] for p in pairs)/6
    report=dict(status='completed',pairs=pairs,improved_army_pairs=improved,
        mean_combat_return_delta=delta,screening_gate_passed=improved>=4 and delta>=0,
        hard_acceptance=False,wall_seconds=time.monotonic()-started)
    (root/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    main()
