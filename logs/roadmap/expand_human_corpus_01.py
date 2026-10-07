"""Extract five cached human games; no fitting, downloading or RL."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path.cwd()
BASE = ROOT / 'logs/roadmap'
OUT = BASE / 'human-corpus-expansion-01'
PYTHON = str((ROOT / '.venv/bin/python').absolute())
IDS = [51572,51685,51885,51754,51483]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=False)
    paths = [Path(__file__),ROOT/'src/runtime.py',ROOT/'src/path.py']
    paths += sorted((ROOT/'src/learning').glob('*.py'))
    paths += [BASE/f'human-replays/{n}.SC2Replay' for n in IDS]
    before = {str(p):digest(p) for p in paths}
    contract = {'sources_before':before,'replay_roles':{str(n):'candidate_teaching' for n in IDS},
                'reserved_game_excluded':51886,'fit':False,'RL':False,'new_downloads':False,
                'player':1,'disable_fog':False,'observation_stride':1,'max_loops':50000,
                'per_extract_wall_seconds':300,'per_subprocess_timeout_seconds':330,
                'selection':'All five previously screened compatible unextracted games; no outcome-based subset'}
    (OUT/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    results=[]
    started=time.monotonic()
    for n in IDS:
        native=BASE/f'human-{n}-expansion-01'
        issued=BASE/f'issued-{n}-expansion-01'
        args=[PYTHON,'-m','src.learning.replay_extract',str(BASE/f'human-replays/{n}.SC2Replay'),
              '--player','1','--output',str(native),'--wall-seconds','300','--max-loops','50000',
              '--observation-stride','1','--source',f'https://lotv.spawningtool.com/{n}/']
        item={'id':n,'native_output':str(native),'issued_output':str(issued),'commands':[args]}
        t=time.monotonic()
        with (OUT/f'{n}.extract.log').open('w') as log:
            process=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=330)
        item['extract_exit']=process.returncode
        item['extract_wall_seconds']=time.monotonic()-t
        if process.returncode==0:
            args=[PYTHON,'-m','src.learning.issued_commands',str(native),'--output',str(issued)]
            item['commands'].append(args)
            with (OUT/f'{n}.issued.log').open('w') as log:
                process=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=60)
            item['issued_exit']=process.returncode
            if process.returncode==0:
                receipt=json.loads((issued/'dataset.json').read_text())
                audit=receipt['issued_command_audit']
                item.update(status=receipt['status'],rows=receipt['rows'],last_loop=receipt['last_loop'],
                    observation_rows=receipt['recorded_observations'],matched_commands=audit['matched_issued_commands'],
                    issued_events=audit['issued_events'],unresolved_count=len(audit['unresolved_events']),
                    masked_timing_rows=audit['masked_timing_rows'],
                    output_hashes={str(p):digest(p) for folder in (native,issued) for p in sorted(folder.iterdir()) if p.is_file()})
        results.append(item)
        (OUT/'progress.json').write_text(json.dumps(results,indent=2)+'\n')
        print(json.dumps({k:v for k,v in item.items() if k not in ('commands','output_hashes')}),flush=True)
    after={str(p):digest(p) for p in paths}
    report={'status':'completed' if all(r.get('issued_exit')==0 and r.get('status')=='completed' for r in results) else 'incomplete',
            'wall_seconds':time.monotonic()-started,'sources_after':after,'sources_unchanged':before==after,'results':results}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('sources_after','results')}),flush=True)

if __name__=='__main__':
    main()
