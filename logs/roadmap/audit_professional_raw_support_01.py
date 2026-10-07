"""Inspect retained human state coverage; never infer a new model prediction."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from sc2.ids.unit_typeid import UnitTypeId

from src.learning.entity_examples import state_inputs, decode_command

root = Path('logs/roadmap'); output = root/'professional-raw-support-01.json'
assert not output.exists()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
cfgpath = root/'joint-professional-fit-05/configuration.json'
cfg = json.loads(cfgpath.read_text())
reportpath = root/'professional-context-query-01/lbfgs/report.json'
report = json.loads(reportpath.read_text())
verified = json.loads((reportpath.parent.parent/'verification.json').read_text())
assert sha(reportpath) == verified['report_sha256']
predictions = {(r['game'],r['row']):r for r in report['commands']}
families = (524,560,319,318,1,3674)
chosen = {}
for ability in families:
    rows = [r for r in report['commands'] if r['game']=='774' and r['ability']==ability]
    chosen.update({(r['game'],r['row']):r for r in rows[:5]})
kinds = ('SCV','COMMANDCENTER','ORBITALCOMMAND','PLANETARYFORTRESS','BARRACKS','BARRACKSFLYING','SUPPLYDEPOT','SUPPLYDEPOTLOWERED','FACTORY','STARPORT','MARINE')
ids = [getattr(UnitTypeId,k).value for k in kinds]
features = ['time/13440','minerals/2000','vespene/2000','food_cap/200','food_army/200','food_workers/100',*[k+'/20' for k in kinds],'history_unknown_fraction','mean_own_order_count/4']
vectors, identities, samples, bindings = [], [], {}, {}
issued = retained = 0; unresolved = Counter(); history_unknown = history_slots = 0
for source in cfg['sources']:
    directory = Path(source['dataset']); game=directory.name
    assert game not in ('848','51483','51886')
    for path, digest in source['bindings'].items():
        assert sha(Path(path)) == digest
        bindings[path]=digest
    receipt=json.loads((directory/'dataset.json').read_text())
    if source['role']=='teaching':
        audit=receipt['issued_command_audit'];issued+=audit['issued_events'];retained+=audit['matched_issued_commands']
        for item in audit['unresolved_events']:
            event=item['event'];ability=event.get('m_abil') or {}
            unresolved[str((ability.get('m_abilLink'),ability.get('m_abilCmdIndex'),tuple(event['m_data'])))]+=1
    row_count=0
    with gzip.open(directory/'examples.jsonl.gz','rt') as stream:
        for index,line in enumerate(stream):
            row=json.loads(line);state=row['observation'];human=row['commands'][0];key=(game,index)
            recorded=predictions[key];assert recorded['ability']==human['ability']
            own=[u for u in state['units'] if u['alliance']==1 and u.get('display_type',1)==1]
            counts=Counter(u['unit_type'] for u in own);history=state['recent_commands'];unknown=sum(bool(c.get('unknown')) for c in history)
            player=state['player']
            vector=[state['game_loop']/13440,*[player.get(k,0)/scale for k,scale in (('minerals',2000),('vespene',2000),('food_cap',200),('food_army',200),('food_workers',100))],*[counts[k]/20 for k in ids],unknown/max(len(history),1),np.mean([len(u.get('orders',[])) for u in own])/4 if own else 0]
            if source['role']=='teaching':
                vectors.append(vector);identities.append(dict(game=game,row=index,ability=human['ability']))
                history_unknown+=unknown;history_slots+=len(history)
            if key in chosen:
                x=state_inputs(state,*cfg['vocabulary'],missing_fields=True)
                gold=tuple(x['tags'].index(tag) for tag in human['units'])
                assert list(gold)==recorded['gold_actors']
                actual=decode_command(recorded['prediction'],x).as_dict()
                types=x['encoder'][1]
                type_match=Counter(int(types[i]) for i in gold)==Counter(int(types[i]) for i in recorded['prediction']['actors'])
                point_error=float(np.linalg.norm(np.array(actual['target_point'])-human['target_point'])) if actual['target_point'] is not None and human['target_point'] is not None else None
                samples[key]=dict(game=game,row=index,ability=human['ability'],features=vector,human=human,predicted_command=actual,ability_correct=actual['ability']==human['ability'],actor_exact=set(actual['units'])==set(human['units']),actor_type_counts_match=type_match,target_point_error_tiles=point_error,unknown_fields=state['unknown_fields'],functional_equivalence='Uncertain: matching types/counts does not prove path, availability or functional equivalence.')
            row_count+=1
    assert row_count==sum(r['game']==game for r in report['commands'])
    print(json.dumps(dict(game=game,rows=row_count)),flush=True)
matrix=np.asarray(vectors)
for sample in samples.values():
    indices=[i for i,r in enumerate(identities) if r['ability']==sample['ability']]
    distances=np.linalg.norm(matrix[indices]-sample['features'],axis=1)
    best=int(np.argmin(distances));sample['nearest_same_ability_teaching']=dict(**identities[indices[best]],distance=float(distances[best]),features=matrix[indices[best]].tolist())
receipt=dict(parent_report_sha256=sha(reportpath),configuration_sha256=sha(cfgpath),helper_sha256=sha(Path(__file__)),source_bindings=bindings,feature_names=features,samples=list(samples.values()),teaching_issued_events=issued,teaching_retained_events=retained,unresolved_raw_ability_target_families=dict(unresolved),teaching_history_unknown_slots=history_unknown,teaching_history_slots=history_slots,scope='Fixed first five diagnostic examples per six families (27 rows); interpretable nearest teaching states conditional on human ability are diagnostics, not controller inputs. No coverage threshold or functional acceptance claim.',policy_updates=0,native_games=0,rl_updates=0)
assert sha(reportpath)==verified['report_sha256']
output.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(samples=len(samples),issued=issued,retained=retained,history_unknown_fraction=history_unknown/history_slots),indent=2))
