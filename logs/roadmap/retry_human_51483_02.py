"""Bounded complete-game retry after terminal 300-second extraction timeout."""
import hashlib,json,subprocess,time
from pathlib import Path
ROOT=Path.cwd();BASE=ROOT/'logs/roadmap';OUT=BASE/'human-51483-retry-02-receipts'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    previous=json.loads((BASE/'human-51483-expansion-01.supervision.json').read_text())
    assert previous['status'] not in ('completed','truncated')
    OUT.mkdir(exist_ok=False)
    paths=[Path(__file__),ROOT/'src/runtime.py',ROOT/'src/path.py',BASE/'human-replays/51483.SC2Replay',*sorted((ROOT/'src/learning').glob('*.py'))]
    before={str(p):sha(p) for p in paths}
    native=BASE/'human-51483-expansion-02';issued=BASE/'issued-51483-expansion-02'
    python=str((ROOT/'.venv/bin/python').absolute())
    args=[python,'-m','src.learning.replay_extract',str(BASE/'human-replays/51483.SC2Replay'),'--player','1','--output',str(native),'--wall-seconds','600','--max-loops','50000','--observation-stride','1','--source','https://lotv.spawningtool.com/51483/']
    contract={'source_before':before,'role':'candidate_teaching','professional':False,'no_fit':True,'no_RL':True,'reserved51886_not_used':True,'native_wall_bound':600,'subprocess_wall_bound':630,'prior_terminal_receipt':previous,'command':args}
    (OUT/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    start=time.monotonic()
    with (OUT/'extract.log').open('w') as f:run=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=630)
    report={'extract_exit':run.returncode}
    if run.returncode==0:
        args=[python,'-m','src.learning.issued_commands',str(native),'--output',str(issued)]
        with (OUT/'issued.log').open('w') as f:run=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=90)
        report['issued_exit']=run.returncode
        if run.returncode==0:
            receipt=json.loads((issued/'dataset.json').read_text());report.update(dataset_status=receipt['status'],rows=receipt['rows'],last_loop=receipt['last_loop'],audit=receipt['issued_command_audit'],output_hashes={str(p):sha(p) for d in (native,issued) for p in d.iterdir() if p.is_file()})
    after={str(p):sha(p) for p in paths}
    report.update(source_after=after,sources_unchanged=before==after,wall_seconds=time.monotonic()-start)
    report['status']='completed' if report.get('dataset_status')=='completed' and report.get('issued_exit')==0 and before==after else 'incomplete'
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_after','output_hashes','audit')}),flush=True)
if __name__=='__main__':main()
