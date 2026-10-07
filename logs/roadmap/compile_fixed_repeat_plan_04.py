from pathlib import Path
from collections import Counter
import hashlib,json
from src.learning.tournament_record import decode_record
from src.learning.human_production_plan import compile_commands,compile_builder_moves
root=Path('logs/roadmap');out=root/'fixed-human-production-plan-04';out.mkdir(exist_ok=False)
reconciliation=root/'human-command-repeats-01/reconciliation.json';rawpath=root/'human-command-repeats-01/events.json';recordpath=root/'pro-preconverted-probe-01/fall-record-870.bin';data_path=root/'joint-frozen-native-wait-02/static.json';parentpath=root/'fixed-human-production-plan-03/plan.json'
g=json.loads(reconciliation.read_text())['games'][0];events={(e['_gameloop'],e['m_sequence']):e for e in json.loads(rawpath.read_text())};r=decode_record(recordpath.read_bytes());f=r['units']['fields'];own={}
for i,s in enumerate(r['units']['step']):
 if f['alliance'][i]==1:own.setdefault(int(r['steps']['game_loop'][s]),{})[int(f['id'][i])]=dict(unit_type=int(f['unitType'][i]))
accepted=[a for a in g['accepted'] if a['loop']<13440];plan=compile_commands(accepted,events,json.loads(data_path.read_text())['game_data'],own,g['metadata_mappings'])
parent=json.loads(parentpath.read_text());repeated={(t['loop'],t['sequence']):t for t in parent['repeated_present_orders']};old={(t['loop'],t['sequence']):t for t in parent['tickets']};tickets=[]
for t in plan['tickets']:
 k=t['loop'],t['sequence']
 if k in repeated:continue
 t['existing_queue_evidence']=old[k]['existing_queue_evidence'] if k in old else ['source_command_manager_repeat']
 if events[k].get('source_manager'):t['source_repeat_provenance']={name:events[k][name] for name in ('source_command','source_manager','source_target_update')}
 tickets.append(t)
n=r['neutral']['fields'];neutral={int(tag):list(map(float,n['pos'][i][:2])) for i,tag in enumerate(n['id'])}
moves=compile_builder_moves(accepted,events,tickets,own,neutral)
for t in moves:
 k=t['loop'],t['sequence']
 if events[k].get('source_manager'):t['source_repeat_provenance']={name:events[k][name] for name in ('source_command','source_manager','source_target_update')}
plan.update({k:v for k,v in parent.items() if k not in ('tickets','bindings','builder_movements','unresolved')})
plan.update(tickets=sorted(tickets+moves,key=lambda t:(t['loop'],t['sequence'])),builder_movements=len(moves),training=False,rl=False)
assert not plan['unresolved'];assert any(t['loop']==7171 and t['sequence']==637 and t['command']['units']==[4357619713] and t['command']['target_point']==[134.5,37.5] for t in plan['tickets'])
plan['limitations'].append('Source command-manager repetitions recovered only with verified unchanged selection context and mutually unique converted actions; other contexts remain excluded.')
paths=[Path(__file__),reconciliation,rawpath,recordpath,data_path,parentpath,Path('src/learning/human_production_plan.py'),Path('src/learning/production_execution.py'),Path('src/learning/tournament_record.py')];plan['bindings']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');snap=out/'source-snapshot';snap.mkdir()
for p in paths:
 if p.suffix=='.py':(snap/p.name).write_bytes(p.read_bytes())
print(json.dumps(dict(tickets=len(plan['tickets']),moves=len(moves),added_macro=len(tickets)-203,counts=dict(Counter(t['name'] for t in tickets if (t['loop'],t['sequence']) not in old)))))
