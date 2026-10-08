"""Preserve immutable experiments; create timing-masked copies for future fits."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil

root=Path('logs/roadmap');out=root/'issued-timing-masked-01'
out.mkdir(exist_ok=False)
names=['51574','51573','51958','51890','51891','51957-p1','50925','51960-p1','51959-held-01']
results=[]
for name in names:
    source=root/('issued-'+name);target=out/source.name;target.mkdir()
    files=[source/n for n in ('dataset.json','static.json','examples.jsonl.gz')]
    before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    receipt=json.loads((source/'dataset.json').read_text())
    loops={x['event']['_gameloop'] for x in receipt['issued_command_audit']['unresolved_events']}
    with gzip.open(source/'examples.jsonl.gz','rt') as f:rows=[json.loads(line) for line in f]
    masked=[]
    for row in rows:
        gap=row['next_action_delay'];loop=row['action_loop']
        if gap is not None and any(loop<t<loop+gap for t in loops):
            masked.append({'loop':loop,'old_delay':gap});row['next_action_delay']=None
    with gzip.open(target/'examples.jsonl.gz','wt') as f:
        for row in rows:f.write(json.dumps(row,separators=(',',':'))+'\n')
    shutil.copyfile(source/'static.json',target/'static.json')
    receipt['examples']=str((target/'examples.jsonl.gz').resolve())
    receipt['timing_source_dataset']=str(source.resolve())
    receipt['timing_labels']='uncertain intervals crossing unresolved human commands masked; action identity retained'
    receipt['issued_command_audit']['masked_timing_rows']=len(masked)
    (target/'dataset.json').write_text(json.dumps(receipt,indent=2)+'\n')
    after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    assert before==after
    results.append({'source':str(source),'output':str(target),'masked':masked,'files_before':before,'files_after':after})
report={'status':'completed','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'datasets':results,
        'masked_rows':sum(len(x['masked']) for x in results),'fitting_performed':False}
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'datasets':len(results),'masked_rows':report['masked_rows']}))
