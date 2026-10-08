"""Check recovered labels directly against protocol events, source selections and wire."""
import json,hashlib,mpyq
from pathlib import Path
from collections import Counter
from src.learning.replay_extract import load_protocol,replay_metadata
from src.learning.tournament_record import decode_record
root=Path('logs/roadmap');out=root/'human-command-repeats-01';audit=json.loads((out/'audit.json').read_text());new=json.loads((out/'reconciliation.json').read_text())['games'][0];old=json.loads((root/'human-refinery-snapshot-reimport-01/reconciliation.json').read_text())['games'][0]
oldrows={(a['loop'],a['sequence']):a for a in old['accepted']};newrows={(a['loop'],a['sequence']):a for a in new['accepted']};assert len(newrows)==1156 and all(newrows[k]==a for k,a in oldrows.items())
replay=root/'pro-preconverted-probe-01/2cda222081e80d9a1c188698ce9bcda6.SC2Replay';meta,_=replay_metadata(replay);protocol=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));original=[e for e in protocol.decode_replay_game_events(mpyq.MPQArchive(str(replay)).read_file('replay.game.events')) if e.get('_userid',{}).get('m_userId')==0]
expanded={(e['_gameloop'],e['m_sequence']):e for e in json.loads((out/'events.json').read_text())};selected={(s['loop'],s['sequence']):s['tags'] for s in old['selections']};wire=json.loads((root/'pro-preconverted-probe-01/fall-actions-870.json').read_text())['actions'];r=decode_record((root/'pro-preconverted-probe-01/fall-record-870.bin').read_bytes());f=r['units']['fields'];own={}
for i,s in enumerate(r['units']['step']):
 if f['alliance'][i]==1:own[int(r['steps']['game_loop'][s]),int(f['id'][i])]=int(f['unitType'][i])
data=json.loads((root/'joint-frozen-native-wait-02/static.json').read_text())['game_data'];abilities={a['ability_id']:a for a in data['abilities']};names={(n['link'],n['index']):n['name'] for n in old['verified_candidate_names']};positions=set();used={tuple(a['converted_position']) for a in oldrows.values()}
for key in sorted(set(newrows)-set(oldrows)):
    row=newrows[key];e=expanded[key];command=row['command'];source=e['source_command']
    start=next(i for i,x in enumerate(original) if x['_event'].endswith('.SCmdEvent') and x['_gameloop']==source['loop'] and x['m_sequence']==source['sequence'])
    finish=next(i for i,x in enumerate(original) if x['_event'].endswith('.SCommandManagerStateEvent') and (x['_gameloop'],x['m_sequence'])==key)
    segment=original[start+1:finish]
    assert not any(x['_event'].endswith(('.SCmdEvent','.SSelectionDeltaEvent','.SControlGroupUpdateEvent')) for x in segment)
    manager=original[finish];assert manager['m_state']==1 and e['source_manager']==manager
    base=original[start];assert e['m_abil']==base['m_abil'] and e['m_cmdFlags']==base['m_cmdFlags']
    updates=[x for x in segment if x['_event'].endswith(('.SCmdUpdateTargetPointEvent','.SCmdUpdateTargetUnitEvent'))]
    target=base['m_data']
    if updates:
        last=updates[-1];kind='TargetPoint' if last['_event'].endswith('PointEvent') else 'TargetUnit';target={kind:last['m_target']}
    assert e['m_data']==target and command['queue']==bool(base['m_cmdFlags']&2)
    assert all(tag&0xffffffff in selected[source['loop'],source['sequence']] and (key[0],tag) in own for tag in command['units'])
    i,j=row['converted_position'];action=wire[i]['actions'][j];assert wire[i]['loop']==key[0] and action['tags']==command['units'] and action['ability']==command['ability']
    assert (i,j) not in positions|used;positions.add((i,j))
    friendly=abilities[action['ability']]['friendly_name'].replace(' ','').lower()
    source_name=names[base['m_abil']['m_abilLink'],base['m_abil']['m_abilCmdIndex']].replace(' ','').lower() if base['m_abil'] else 'smart'
    assert friendly==source_name
    if 'TargetPoint' in target:
        point=[target['TargetPoint'][axis]/4096 for axis in ('x','y')];assert command['target_point']==point and action['target']==[int(v) for v in point]
    elif 'TargetUnit' in target:
        assert command['target_unit']==action['target'] and action['target']&0xffffffff==target['TargetUnit']['m_tag']
    else:assert command.get('target_point') is None and command.get('target_unit') is None
for p,sha in audit['bindings'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha,p
planpath=root/'fixed-human-production-plan-04/plan.json';plan=json.loads(planpath.read_text());parent=json.loads((root/'fixed-human-production-plan-03/plan.json').read_text());keys={(t['loop'],t['sequence']):t for t in plan['tickets']}
assert len(keys)==241 and not plan['unresolved']
assert all(keys[t['loop'],t['sequence']]==t for t in parent['tickets'])
result=dict(status='verified_original_command_manager_labels',old_preserved=851,new_labels=305,total=1156,added_counts=dict(Counter(a['command']['ability'] for k,a in newrows.items() if k not in oldrows)),fixed_plan_instructions=241,old_plan_preserved=212,training=False,rl=False,corpus_reimport=False,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),out/'audit.json',out/'reconciliation.json',out/'events.json',planpath)})
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(out/'source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(result))
