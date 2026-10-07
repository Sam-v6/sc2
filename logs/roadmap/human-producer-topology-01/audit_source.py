from pathlib import Path
import json, hashlib, math
from collections import Counter
from src.learning.tournament_record import decode_record
root=Path('logs/roadmap')
record_path=root/'pro-preconverted-probe-01/fall-record-870.bin'
static_path=root/'joint-frozen-native-wait-02/static.json'
commands_path=root/'human-refinery-snapshot-reimport-01/reconciliation.json'
out=root/'human-producer-topology-01'
out.mkdir(exist_ok=False)
record=decode_record(record_path.read_bytes())
f=record['units']['fields']; loops=record['steps']['game_loop']
data=json.loads(static_path.read_text())['game_data']
names={u['unit_id']:u['name'] for u in data['units']}
abilities={a['ability_id']:a for a in data['abilities']}
frames=[{} for _ in loops]
for i,step in enumerate(record['units']['step']):
    if f['alliance'][i]==1:
        frames[int(step)][int(f['id'][i])]=i
producers={'Barracks','Factory','Starport','BarracksFlying','FactoryFlying','StarportFlying'}
addons={'TechLab','Reactor','BarracksTechLab','BarracksReactor','FactoryTechLab','FactoryReactor','StarportTechLab','StarportReactor'}
previous={}; transitions=[]; topology={}; ambiguous=[]
for step,frame in enumerate(frames):
    loop=int(loops[step])
    if loop>=13440: break
    current={}
    for tag,i in frame.items():
        name=names.get(int(f['unitType'][i]))
        if name not in producers: continue
        candidates=[]
        if not f['is_flying'][i]:
            expected=[float(f['pos'][i][0])+2.5,float(f['pos'][i][1])-.5]
            candidates=[other for other,j in frame.items()
                        if names.get(int(f['unitType'][j])) in addons
                        and math.dist(expected,f['pos'][j][:2])<.1]
        attachment=candidates[0] if len(candidates)==1 else None
        state=dict(producer_type=name,flying=bool(f['is_flying'][i]),
                   position=[float(v) for v in f['pos'][i][:2]],
                   geometric_addon=attachment,
                   addon_type=names[int(f['unitType'][frame[attachment]])] if attachment else None,
                   addon_complete=bool(f['build_progress'][frame[attachment]]>=1) if attachment else None)
        current[tag]=state
        if len(candidates)>1: ambiguous.append(dict(loop=loop,producer=tag,candidates=candidates))
        old=previous.get(tag)
        # Position changes in flight are not attachment transitions.
        signature=lambda s:(s['producer_type'],s['flying'],s['geometric_addon'],s['addon_complete'])
        if old is None or signature(old)!=signature(state):
            transitions.append(dict(loop=loop,producer=tag,before=old,after=state))
    topology[loop]=current
    previous=current
commands=[]
g=json.loads(commands_path.read_text())['games'][0]
for row in g['accepted']:
    loop=row['loop']
    if loop>=13440: continue
    command=row['command']; friendly=abilities.get(command['ability'],{}).get('friendly_name','')
    for actor in command['units']:
        state=topology.get(loop,{}).get(actor)
        if state is not None and friendly.startswith(('Train','Research','Build','Lift','Land')):
            commands.append(dict(loop=loop,sequence=row['sequence'] if 'sequence' in row else None,
                                 actor=actor,ability=command['ability'],name=friendly,topology=state))
paths=[Path(__file__),record_path,static_path,commands_path,Path('src/learning/tournament_record.py')]
report=dict(status='descriptive_observed_producer_topology',seconds=600,
            training=False,rl=False,transitions=transitions,commands=commands,
            ambiguous=ambiguous,command_names=dict(Counter(r['name'] for r in commands)),
            bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            limitations=['Geometry is observed proximity, not a reliable native addon-tag field.',
                         'Source addon types can change on attachment; retain full addon identity.',
                         'No production payment, command acceptance or future completion is inferred.',
                         'This is source label analysis, never model observation input.'])
(out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'audit_source.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(dict(transitions=len(transitions),commands=len(commands),ambiguous=len(ambiguous),
                     addon_transitions=[t for t in transitions if (t['before'] or {}).get('geometric_addon')!=t['after']['geometric_addon']] ),indent=2))
