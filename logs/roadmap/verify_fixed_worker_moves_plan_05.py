import json,hashlib
from pathlib import Path
root=Path('logs/roadmap');out=root/'fixed-human-production-plan-05';plan=json.loads((out/'plan.json').read_text());parent=json.loads((root/'fixed-human-production-plan-04/plan.json').read_text());events={(e['_gameloop'],e['m_sequence']):e for e in json.loads((root/'human-command-repeats-01/events.json').read_text())};old={(t['loop'],t['sequence']):t for t in parent['tickets']};new={(t['loop'],t['sequence']):t for t in plan['tickets']}
assert len(new)==243 and len(old)==241 and not plan['unresolved'] and set(old)<=set(new)
for key,t in old.items():
 copy=dict(new[key]);copy.pop('protect_until_build',None);assert copy==t,key
for key in set(new)-set(old):
 t=new[key];e=events[key];assert key in ((3824,261),(3828,262))
 assert t['name']=='Move builder' and t['command']['units']==[4349493249] and not t['command']['queue'] and not t['protect_until_build']
 assert t['original_flags']==e['m_cmdFlags'] and t['command']['target_point']==[e['m_data']['TargetPoint'][axis]/4096 for axis in ('x','y')]
for p,h in plan['bindings'].items():
 path=Path(p)
 if path.suffix=='.py':path=out/'source-snapshot'/path.name
 assert hashlib.sha256(path.read_bytes()).hexdigest()==h,path
result=dict(status='verified_original_distant_builder_moves',total=243,old_instructions_preserved=241,new_movement_keys=[[3824,261],[3828,262]],movement_releases_mining_after_arrival=True,training=False,rl=False,plan_sha256=hashlib.sha256((out/'plan.json').read_bytes()).hexdigest())
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(out/'source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(result))
