"""Read-only case summaries; observations do not establish causal attribution."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ARM=ROOT/'logs/macro-teacher/preflight'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    summary=json.loads((ARM/'summary.json').read_text());assert summary['completed']
    ledger=json.loads((ARM/'ledger.json').read_text())
    hashes={str(path):digest(path) for path in [Path(__file__),ARM/'inputs.json',ARM/'summary.json',ARM/'ledger.json']}
    cases=[]
    fields=['workers','army','bases','minerals','gas','marines','marauders','tanks','medivacs','vikings','ravens','enemy_air','enemy_near_base','attacking']
    for job in ledger:
        paths=[Path(job[key]) for key in ['actions','production','commands']]
        hashes.update({str(path):digest(path) for path in paths})
        actions,production,commands=[[json.loads(line) for line in path.read_text().splitlines()] for path in paths]
        attacks=[row['time'] for row in actions if row['action']=='attack']
        threats=[row['time'] for row in actions if row['snapshot']['enemy_near_base']]
        snapshots=[]
        for seconds in [180,300,480,720,960]:
            rows=[row for row in actions if row['time']<=seconds]
            if seconds<=job['game_seconds'] and rows:
                row=rows[-1];snapshots.append({'time':row['time'],**{key:row['snapshot'][key] for key in fields}})
        cases.append({**{key:job[key] for key in ['seed','race','build','map','result','game_seconds']},
            'requests':dict(Counter(row['action'] for row in actions)),
            'unstaged_requests':sum(not row['executed'] for row in actions),
            'observed_appearances_including_initial':dict(Counter(row['type'] for row in production if row['event']=='unit_appeared')),
            'observed_building_completions_including_initial':dict(Counter(row['type'] for row in production if row['event']=='building_completed')),
            'queued_abilities_not_engine_acknowledgements':dict(Counter(command['ability'] for row in commands for command in row['queued'])),
            'first_attack':attacks[0] if attacks else None,'first_home_threat':threats[0] if threats else None,
            'peak_observed_counts':{key:max(row['snapshot'][key] for row in actions) for key in fields},
            'snapshots':snapshots,'last_snapshot':{key:actions[-1]['snapshot'][key] for key in fields}})
    for path,expected in hashes.items():assert digest(path)==expected,path
    output=ARM.parent/'preflight-diagnosis.json';assert not output.exists()
    output.write_text(json.dumps({'source_and_input_hashes':hashes,'cases':cases,
        'limits':'Current counts and appearances include starting units; requests and queued commands do not prove completed production. Descriptive summaries do not isolate causal strategy or execution effects.'},indent=2)+'\n')
    print(output)


if __name__=='__main__':main()
