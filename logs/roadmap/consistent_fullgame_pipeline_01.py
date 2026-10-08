"""One fixed supervised rebuild of the three command components."""
import gzip,hashlib,json,os,subprocess,time,traceback
from pathlib import Path
root=Path('logs/roadmap');out=root/'consistent-fullgame-01';out.mkdir(exist_ok=False)
ids=[51574,51573,51958,51890,51891];datasets=[root/'issued-timing-masked-01'/f'issued-{i}' for i in ids];validation=root/'issued-timing-masked-01/issued-50925'
python=str(Path('.venv/bin/python').resolve());macro=out/'macro';actors=out/'actors';arguments=out/'arguments'
# Audit code is frozen before any fit; it uses unmasked teacher-game reconstruction.
audit_source=Path('logs/roadmap/command_stage_teaching_01.py').read_text().replace("out=root/'command-stage-teaching-01'", "out=root/'command-stage-consistent-fullgame-01'")
audit_source=audit_source.replace("root/'imitation-prefix-240-01/policy.npz'", "root/'consistent-fullgame-01/macro/policy.npz'").replace("root/'actor-prefix-240-01/actors.npz'", "root/'consistent-fullgame-01/actors/actors.npz'").replace("root/'arguments-full-human-01/arguments.npz'", "root/'consistent-fullgame-01/arguments/arguments.npz'")
audit_script=out/'audit_teaching.py';audit_script.write_text(audit_source)
files=[Path(__file__),audit_script,*sorted(Path('src/learning').glob('*.py')),*[directory/name for directory in datasets+[validation] for name in ('dataset.json','static.json','examples.jsonl.gz')],root/'command-stage-teaching-01/report.json']
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=hashes();inventory=[]
for directory in datasets:
 with gzip.open(directory/'examples.jsonl.gz','rt') as stream:rows=list(map(json.loads,stream))
 commands=sum(len(r['commands']) for r in rows);max_loop=max(r['action_loop'] for r in rows);assert max_loop<=10000*22.4
 inventory.append({'dataset':str(directory),'commands':commands,'last_action_loop':max_loop,'sha256':json.loads((directory/'dataset.json').read_text())['sha256']})
assert sum(r['commands'] for r in inventory)==1999
steps=[('macro',[python,'-m','src.learning.imitation_train','--train',*map(str,datasets),'--validation',str(validation),'--output',str(macro),'--epochs','600','--seed','4000','--decision-level','global','--balance-abilities','--prefix-seconds','10000'],900),('actors',[python,'-m','src.learning.actor_train','--macro',str(macro/'policy.npz'),'--datasets',*map(str,datasets),'--output',str(actors),'--seconds','10000','--epochs','350'],2400),('arguments',[python,'-m','src.learning.argument_train','--macro',str(macro/'policy.npz'),'--datasets',*map(str,datasets),'--output',str(arguments),'--seconds','10000','--epochs','600'],300),('teaching_audit',[python,str(audit_script)],300)]
contract={'scope':'single consistent whole-game supervised pipeline; same five human sources for all components; frozen full-game macro shared by actor/argument fits; no RL/live play/professional teacher claim','train_inventory':inventory,'validation':'reused Lyra diagnostic only; reserved 51886 untouched','bounds':{name:seconds for name,_,seconds in steps},'epochs':{'macro':600,'actors':350,'arguments':600},'cpu':'OPENBLAS_NUM_THREADS=2; no GPU','gate':'both periods >=95% ability, >=90% actor sets and >=75% complete commands in unmasked teaching reconstruction; these are sanity gates, not live competence or permission to resume RL','files_before':before}
(out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n');environment=dict(os.environ,OPENBLAS_NUM_THREADS='2',PYTHONPATH='.')
start=time.monotonic();receipts=[]
try:
 for name,command,limit in steps:
  (out/'stage.json').write_text(json.dumps({'status':'running','stage':name,'wall_seconds':time.monotonic()-start})+'\n');print(json.dumps({'starting':name,'wall_limit':limit}),flush=True)
  begin=time.monotonic()
  with (out/(name+'.console.log')).open('w') as stream:result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,env=environment,timeout=limit,check=True)
  receipts.append({'stage':name,'status':'completed','exit_code':result.returncode,'wall_seconds':time.monotonic()-begin})
  if name!='teaching_audit':assert json.loads((out/name/'report.json').read_text())['status']=='completed'
 assert hashes()==before
 audit=json.loads((root/'command-stage-consistent-fullgame-01/report.json').read_text());gate=True
 for summary in audit['aggregate'].values():
  s=summary['stages']['joint'];n=summary['commands'];gate &= s['ability_hits']/n>=.95 and s['actor_set_hits']/n>=.9 and s['complete_hits']/n>=.75
 models={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [macro/'policy.npz',actors/'actors.npz',arguments/'arguments.npz']}
 report=dict(contract,status='completed',steps=receipts,gate_passed=bool(gate),aggregate=audit['aggregate'],model_hashes=models,files_after=hashes(),wall_seconds=time.monotonic()-start)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'stage.json').write_text(json.dumps({'status':'completed','gate_passed':bool(gate)})+'\n');print(json.dumps({'status':'completed','gate_passed':bool(gate),'aggregate':audit['aggregate']}),flush=True)
except BaseException as error:
 (out/'failure.json').write_text(json.dumps({'status':'failed','error_type':type(error).__name__,'reason':str(error),'completed_steps':receipts,'wall_seconds':time.monotonic()-start},indent=2)+'\n');raise
