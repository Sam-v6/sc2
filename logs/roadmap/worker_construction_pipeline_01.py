"""One fixed human-supervised argument fit; frozen macro/actors and diagnostics."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

root = Path('logs/roadmap')
out = root / 'worker-construction-arguments-01'
out.mkdir(exist_ok=False)
datasets = [root / 'issued-timing-masked-01' / f'issued-{i}' for i in (51574,51573,51958,51890,51891)]
macro = root / 'consistent-fullgame-02/macro/policy.npz'
actors = root / 'consistent-fullgame-02/actors/actors.npz'
baseline = root / 'consistent-fullgame-02/arguments/arguments.npz'
model = out / 'arguments/arguments.npz'
queue_script = (root / 'worker_queue_diagnosis_01.py').read_text()
queue_script = queue_script.replace("out = root / 'worker-queue-diagnosis-01'", "out = root / 'worker-queue-construction-01'")
queue_script = queue_script.replace("root / 'consistent-fullgame-02/arguments/arguments.npz'", "root / 'worker-construction-arguments-01/arguments/arguments.npz'")
queue_script = queue_script.replace("macro.command_context(x, command['ability']))", "macro.command_context(x, command['ability']), arguments.evidence.get('worker_construction_products'))")
queue_script = queue_script.replace("assert not live['predicted_queue'] and not command['queue']", "assert not command['queue']  # Record the frozen counterfactual; no prescribed result.")
(out / 'audit_queue.py').write_text(queue_script)
stage_script = (root / 'command_stage_teaching_01.py').read_text()
stage_script = stage_script.replace("out=root/'command-stage-teaching-01'", "out=root/'command-stage-worker-construction-01'")
stage_script = stage_script.replace("root/'imitation-prefix-240-01/policy.npz'", "root/'consistent-fullgame-02/macro/policy.npz'").replace("root/'actor-prefix-240-01/actors.npz'", "root/'consistent-fullgame-02/actors/actors.npz'").replace("root/'arguments-full-human-01/arguments.npz'", "root/'worker-construction-arguments-01/arguments/arguments.npz'")
stage_script = stage_script.replace("origin, context)\n                        output = replace_arguments", "origin, context, arguments.evidence.get('worker_construction_products'))\n                        output = replace_arguments")
(out / 'audit_teaching.py').write_text(stage_script)
files = [Path(__file__), out/'audit_queue.py', out/'audit_teaching.py', macro, actors, baseline, *sorted(Path('src/learning').glob('*.py')), *[d/n for d in datasets for n in ('dataset.json','static.json','examples.jsonl.gz')], root/'command-stage-consistent-fullgame-02/report.json', root/'worker-queue-diagnosis-01/report.json']
def hashes():
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before = hashes()
contract = {'scope':'Only argument model refit on same five whole human teaching games, seed5001/600epochs/equal replay weights, with five opt-in observed construction cues. Frozen macro/actor weights. Same architecture except input size/initialization; no isolated causal-effect claim. Reused other-player diagnostics and traced native state are evaluation only; no RL/live play/professional claim.', 'datasets':list(map(str,datasets)), 'bounds':{'fit':300,'queue_audit':60,'teaching_audit':300}, 'gate':'Other-player no-foundation queue copying >=6/8 and teaching11/11; all68queue hits>=57; joint complete teaching commands not below342prefix/778late. This gate authorizes consideration of a functional frozen test, never promotion or RL.', 'files_before':before, 'cpu':'two BLAS threads, CPU only; reserved51886 untouched'}
(out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
python = str(Path('.venv/bin/python').absolute())
steps = [('fit',[python,'-m','src.learning.argument_train','--macro',str(macro),'--datasets',*map(str,datasets),'--output',str(out/'arguments'),'--seconds','10000','--epochs','600','--worker-construction'],300),('queue_audit',[python,str(out/'audit_queue.py')],60),('teaching_audit',[python,str(out/'audit_teaching.py')],300)]
start = time.monotonic()
receipts = []
env = dict(os.environ,OPENBLAS_NUM_THREADS='2',PYTHONPATH='.')
try:
    for name, command, limit in steps:
        print(json.dumps({'starting':name,'limit':limit}),flush=True)
        (out/'stage.json').write_text(json.dumps({'status':'running','stage':name})+'\n')
        begin = time.monotonic()
        with (out/(name+'.console.log')).open('w') as stream:
            result = subprocess.run(command,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=limit,check=True)
        receipts.append({'stage':name,'exit_code':result.returncode,'wall_seconds':time.monotonic()-begin})
    queue = json.loads((root/'worker-queue-construction-01/report.json').read_text())
    stage = json.loads((root/'command-stage-worker-construction-01/report.json').read_text())
    old = json.loads((root/'worker-queue-diagnosis-01/report.json').read_text())
    assert [(r['dataset'],r['loop'],r['teacher']) for r in queue['records']] == [(r['dataset'],r['loop'],r['teacher']) for r in old['records']]
    teach_names = {d.name for d in datasets}
    no_foundation = [r for r in queue['records'] if 'no_visible_foundation' in r['selected_builder_stages']]
    subgroups = {label:{'commands':len(rows),'queue_hits':sum(r['correct'] for r in rows)} for label,rows in [('teaching',[r for r in no_foundation if Path(r['dataset']).name in teach_names]),('diagnostic',[r for r in no_foundation if Path(r['dataset']).name not in teach_names])]}
    assert subgroups['teaching']['commands']==11 and subgroups['diagnostic']['commands']==8
    joint = {k:r['stages']['joint']['complete_hits'] for k,r in stage['aggregate'].items()}
    gate = subgroups['teaching']['queue_hits']==11 and subgroups['diagnostic']['queue_hits']>=6 and queue['summary']['all']['queue_hits']>=57 and joint['prefix_240']>=342 and joint['after_240']>=778
    assert hashes()==before
    report = dict(contract,status='completed',steps=receipts,queue_summary=queue['summary'],queue_subgroups=subgroups,live_counterfactual=queue['live'],joint_complete=joint,gate_passed=gate,model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),files_after=hashes(),wall_seconds=time.monotonic()-start)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'stage.json').write_text(json.dumps({'status':'completed','gate_passed':gate})+'\n')
    print(json.dumps({k:report[k] for k in ('status','queue_summary','queue_subgroups','live_counterfactual','joint_complete','gate_passed','wall_seconds')},indent=2),flush=True)
except BaseException as error:
    (out/'failure.json').write_text(json.dumps({'status':'failed','error':str(error),'completed_steps':receipts},indent=2)+'\n')
    raise
