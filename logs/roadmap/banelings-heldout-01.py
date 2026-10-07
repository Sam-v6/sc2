from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import time
from src.learning.sandbox import sandbox_job
from src.runtime import supervise


def run(job):
    return supervise(sandbox_job,(job,),120)


def main():
    root=Path('logs/roadmap/banelings-heldout-01');root.mkdir(exist_ok=False)
    policy=Path('logs/roadmap/banelings-search-01/best.json').resolve()
    contract=dict(scope='held-out scored-wave micro primitive; ordinary-game transfer unproved',
        seeds=list(range(42200,42208)),policy_sha256=hashlib.sha256(policy.read_bytes()).hexdigest(),
        seconds=60,step=4,workers=1,
        gate='strictly greater mean killed value AND at least1.5x baseline AND no worse aggregate damage/killed value; native outcomes reported but wave clearing respawns enemies',
        mechanics=json.loads(Path('logs/roadmap/banelings-map-mechanics.json').read_text()))
    (root/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    jobs=[]
    for seed in contract['seeds']:
        for arm in ('baseline','learned'):
            jobs.append(dict(map='DefeatZerglingsAndBanelings',seed=seed,seconds=60,step=4,
                policy=str(policy) if arm=='learned' else None,
                output=str((root/f'{arm}-{seed}').resolve())))
    start=time.monotonic()
    with ThreadPoolExecutor(max_workers=1) as pool:
        receipts=list(pool.map(run,jobs))
    (root/'receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    if any(r['status'] not in ('completed','truncated') for r in receipts):
        raise RuntimeError('Native worker failure; primitive comparison invalid')
    metrics=[]
    for arm,rows in (('baseline',receipts[::2]),('learned',receipts[1::2])):
        kills=sum(r['score']['killed_value'] for r in rows)
        damage=sum(r['score']['damage_taken'] for r in rows)
        metrics.append(dict(arm=arm,mean_killed_value=kills/8,
            mean_damage_taken=damage/8,damage_per_killed_value=damage/kills if kills else None,
            mean_official_score=sum(r['score']['score'] for r in rows)/8,
            mean_survival_seconds=sum(r['game_seconds'] for r in rows)/8,
            native_outcomes={name:sum(r['sandbox_result']==name for r in rows)
                for name in ('Victory','Defeat','Tie')}))
    a,b=metrics
    pass_kills=b['mean_killed_value']>a['mean_killed_value'] and b['mean_killed_value']>=1.5*a['mean_killed_value']
    pass_efficiency=b['damage_per_killed_value'] is not None and (a['damage_per_killed_value'] is None or b['damage_per_killed_value']<=a['damage_per_killed_value'])
    report=dict(contract,status='completed',metrics=metrics,
        primitive_gate_passed=pass_kills and pass_efficiency,
        ordinary_game_transfer=False,hard_acceptance=False,wall_seconds=time.monotonic()-start)
    (root/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':main()
