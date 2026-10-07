"""Current-input coverage and representation-reflection sensitivity audit."""
import copy,gzip,hashlib,json,os
from collections import Counter
from pathlib import Path
import numpy as np
import torch
from src.learning.actor_selection import construction_products
from src.learning.entity_examples import state_inputs
from src.learning.entity_type_status import unit_type_status
from src.learning.production_execution import command_cost
from src.learning.production_component import ProductionComponent
ROOT=Path('logs/roadmap');OUT=ROOT/'professional-choice-input-audit-01';PRO=ROOT/'professional-production-choice-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def reflect(state,axes):
    result=copy.deepcopy(state);size=state['map_size']
    for key in ('units','owned_memory','memory'):
        for unit in result.get(key,[]):
            for axis in axes:unit['position'][axis]=size[axis]-unit['position'][axis]
            for order in unit.get('orders',[]):
                point=order.get('target_world_space_pos')
                if point:
                    for axis in axes:
                        k=('x','y')[axis];point[k]=size[axis]-point[k]
    return result
assert os.environ['CUDA_VISIBLE_DEVICES']==''
torch.set_num_threads(2);torch.set_num_interop_threads(2)
OUT.mkdir(exist_ok=False)
report=read(PRO/'report.json');catalog=ROOT/'dense-timing-cohort-01/51574/static.json';data=read(catalog)['game_data'];products=construction_products(data)
names={a['ability_id']:a.get('friendly_name','') for a in data['abilities']};types={u['unit_id']:u for u in data['units']}
counts=[max(r[k] for r in data[n])+1 for n,k in (('units','unit_id'),('abilities','ability_id'),('upgrades','upgrade_id'))]
model_path=ROOT/'professional-choice-fit-02/choice.npz';model,_=ProductionComponent.load(model_path)
coverage=Counter();unknown_player=Counter();unpriced=Counter();reflection=Counter();records=[];source_paths=[Path(__file__),catalog,model_path,PRO/'report.json',ROOT/'professional-choice-fit-02/verification.json']
for game in report['games']:
    path=PRO/game['game']/'examples.jsonl.gz';source_paths.append(path)
    for line in gzip.open(path,'rt'):
        e=json.loads(line);st=dict(e['observation'],recent_commands=[]);gold=e['label']['ability'];family='building' if names[gold].startswith('Build ') else 'other';prefix=game['role']+'_'+family
        coverage[prefix+'_events']+=1;unknown_player.update(st.get('unknown_fields',{}).get('player',[]))
        try:
            minerals,gas=command_cost(gold,data)
            coverage[prefix+'_priced']+=1
            coverage[prefix+'_below_single_product_cost']+=st['player'].get('minerals',0)<minerals or st['player'].get('vespene',0)<gas
        except ValueError:unpriced[names[gold]]+=1
        producers=[u for u in st['units'] if u['alliance']==1 and u['unit_type'] in (18,132,130,21,27,28)]
        coverage[prefix+'_producer_observations']+=len(producers)
        coverage[prefix+'_producer_orders_at_truncation_limit']+=sum(len(u.get('orders',[]))>=4 for u in producers)
        coverage[prefix+'_missing_producer_build_progress']+=sum('build_progress' not in u for u in producers)
        if game['role']!='diagnostic':continue
        x=state_inputs(st,*counts,products=products,missing_fields=True);p=model.predict(x);original=max(p,key=p.get);status=unit_type_status(x,counts[0]);variants=[]
        for axes in ((0,),(1,),(0,1)):
            mirror=reflect(st,axes);z=state_inputs(mirror,*counts,products=products,missing_fields=True)
            assert np.array_equal(status,unit_type_status(z,counts[0]))
            assert np.array_equal(x['encoder'][3],z['encoder'][3])
            assert np.array_equal(x['encoder'][1],z['encoder'][1]) and np.array_equal(x['encoder'][2],z['encoder'][2])
            q=model.predict(z);pred=max(q,key=q.get);axis_name=''.join(('x','y')[a] for a in axes)
            reflection[axis_name+'_events']+=1;reflection[axis_name+'_changed_choice']+=pred!=original
            reflection[axis_name+'_original_correct']+=original==gold;reflection[axis_name+'_reflected_correct']+=pred==gold
            if family=='building':
                reflection[axis_name+'_building_events']+=1
                reflection[axis_name+'_building_changed_choice']+=pred!=original
                reflection[axis_name+'_building_correct']+=pred==gold
            variants.append(dict(axes=axis_name,predicted=pred,changed=pred!=original))
        records.append(dict(game=game['game'],key=e['label']['source_key'],gold=gold,original=original,variants=variants))
bindings={str(p):sha(p) for p in source_paths}
for p in sorted(Path('src/learning').glob('*.py')):bindings[str(p)]=sha(p)
result=dict(status='completed_current_input_coverage_and_reflection_audit',coverage=dict(coverage),unknown_player_field_events=dict(unknown_player),unpriced_labels=dict(unpriced),reflection=dict(reflection),records=records,bindings=bindings,training=False,native=False,rl=False,
    limits=['Reflection is a representation sensitivity probe, not a native mirrored-map game or a label correction.',
            'Cost audit uses a single-product lower bound, not native castability or an actor-group total.',
            'No fields, examples or predictions are changed in the source corpora.'])
(OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','coverage','unknown_player_field_events','unpriced_labels','reflection')}))
