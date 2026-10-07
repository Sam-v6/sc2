from pathlib import Path
import hashlib,json
from src.learning.tournament_record import decode_record
from src.learning.human_production_plan import compile_builder_moves
root=Path('logs/roadmap');out=root/'fixed-human-production-plan-03';out.mkdir(exist_ok=False)
parent=root/'fixed-human-production-plan-02/plan.json';plan=json.loads(parent.read_text())
recpath=root/'human-refinery-snapshot-reimport-01/reconciliation.json';g=json.loads(recpath.read_text())['games'][0]
rawpath=root/'pro-preconverted-probe-01/raw-commands-870.json';events={(e['_gameloop'],e['m_sequence']):e for e in json.loads(rawpath.read_text())}
recordpath=root/'pro-preconverted-probe-01/fall-record-870.bin';record=decode_record(recordpath.read_bytes());f=record['units']['fields'];own={}
for i,step in enumerate(record['units']['step']):
 if f['alliance'][i]==1:own.setdefault(int(record['steps']['game_loop'][step]),{})[int(f['id'][i])]=dict(unit_type=int(f['unitType'][i]))
n=record['neutral']['fields'];neutral={int(tag):list(map(float,n['pos'][i][:2])) for i,tag in enumerate(n['id'])}
moves=compile_builder_moves([a for a in g['accepted'] if a['loop']<13440],events,plan['tickets'],own,neutral)
assert len(moves)==9
plan['tickets']=sorted(plan['tickets']+moves,key=lambda t:(t['loop'],t['sequence']))
paths=[Path(__file__),parent,recpath,rawpath,recordpath,Path('src/learning/human_production_plan.py'),Path('src/learning/tournament_record.py')]
plan['bindings']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};plan['builder_movements']=9
plan['limitations'].append('Nine actual builder movements use future building commands only as label provenance, never observation features.')
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');snapshot=out/'source-snapshot';snapshot.mkdir()
for p in paths:
 if p.suffix=='.py':(snapshot/p.name).write_bytes(p.read_bytes())
print(json.dumps(dict(tickets=len(plan['tickets']),moves=moves),indent=2))
