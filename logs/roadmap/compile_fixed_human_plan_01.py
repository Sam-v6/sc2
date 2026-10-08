from pathlib import Path
import hashlib,json
from src.learning.tournament_record import decode_record
from src.learning.human_production_plan import compile_commands
root=Path('logs/roadmap');out=root/'fixed-human-production-plan-01';out.mkdir(exist_ok=False)
reconciliation=root/'human-refinery-snapshot-reimport-01/reconciliation.json'
raw_path=root/'pro-preconverted-probe-01/raw-commands-870.json'
record_path=root/'pro-preconverted-probe-01/fall-record-870.bin'
data_path=root/'joint-frozen-native-wait-02/static.json'
queue_path=root/'human-queue-transitions-01/audit.json'
g=json.loads(reconciliation.read_text())['games'][0]
events={(e['_gameloop'],e['m_sequence']):e for e in json.loads(raw_path.read_text())}
data=json.loads(data_path.read_text())['game_data'];record=decode_record(record_path.read_bytes())
f=record['units']['fields'];loops=record['steps']['game_loop'];own={int(loop):{} for loop in loops if loop<13440}
for i,step in enumerate(record['units']['step']):
 loop=int(loops[step])
 if loop<13440 and f['alliance'][i]==1:
  own[loop][int(f['id'][i])]=dict(unit_type=int(f['unitType'][i]))
accepted=[a for a in g['accepted'] if a['loop']<13440]
plan=compile_commands(accepted,events,data,own,g['metadata_mappings'])
queue=json.loads(queue_path.read_text())
proof={(e['loop'],e['sequence'],e['actor']):e['status'] for e in queue['entries']}
repeats=[];tickets=[]
for ticket in plan['tickets']:
 statuses=[proof.get((ticket['loop'],ticket['sequence'],actor)) for actor in ticket['command']['units']]
 ticket['existing_queue_evidence']=statuses
 if statuses and all(s=='already_present_no_count_increase' for s in statuses):
  repeats.append(ticket)
 else: tickets.append(ticket)
plan.update(tickets=tickets,repeated_present_orders=repeats,game=870,teacher='Clem',human_result='Win',
            map='AcropolisLE',seconds=600,training=False,rl=False,
            status='compiled_issued_production_plan' if not plan['unresolved'] else 'incomplete_specific_ability_resolution',
            limitations=['This is a fixed source plan, not a learned policy.',
                         'Four source repeated/present orders are retained as evidence, not new work tickets.',
                         'Queue flags and precise point coordinates require original-event recovery before native playback.',
                         'Unmatched source events and mode commands are outside this accepted-command compiler.',
                         'Original replay map differs from installed map bytes; native placement must be checked.',
                         'Paid starts/completions and new-building binding are not inferred from issued commands.'])
paths=[Path(__file__),reconciliation,raw_path,record_path,data_path,queue_path,
       Path('src/learning/human_production_plan.py'),Path('src/learning/production_execution.py'),Path('src/learning/tournament_record.py')]
plan['bindings']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
snapshot=out/'source-snapshot';snapshot.mkdir()
for p in paths:
 if p.suffix=='.py':(snapshot/p.name).write_bytes(p.read_bytes())
print(json.dumps(dict(status=plan['status'],tickets=len(tickets),repeats=len(repeats),unresolved=plan['unresolved'],opening=tickets[:8]),indent=2))
