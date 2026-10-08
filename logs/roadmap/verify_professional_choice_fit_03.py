"""Independent saved-checkpoint predictions, source and frozen-gate audit."""
import gzip,hashlib,json,os
from collections import Counter
from pathlib import Path
import numpy as np
import torch
from src.learning.actor_selection import construction_products
from src.learning.entity_examples import state_inputs
from src.learning.production_component import ProductionComponent
from src.learning.goal_first_policy import GoalFirstPolicy
ROOT=Path('logs/roadmap');OUT=ROOT/'professional-choice-fit-03';PRO=ROOT/'professional-production-choice-01'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert os.environ['CUDA_VISIBLE_DEVICES']==''
torch.set_num_threads(2);torch.set_num_interop_threads(2)
contract=read(OUT/'contract.json');report=read(OUT/'report.json');evaluation=read(OUT/'evaluation.json')
assert contract['seed']==822103 and contract['epochs']==30 and contract['presentations']==38010
for p,h in contract['bindings'].items():
    path=OUT/'source-snapshot'/p if Path(p).suffix=='.py' else Path(p)
    assert sha(path)==h,p
assert read(ROOT/'broad-production-combat-02/verification.json')['status']=='verified_native_production_combat_execution'
assert report['presentations']==38010 and not report['native'] and not report['rl']
data=read(ROOT/'dense-timing-cohort-01/51574/static.json')['game_data']
counts=[max(r[k] for r in data[n])+1 for n,k in (('units','unit_id'),('abilities','ability_id'),('upgrades','upgrade_id'))]
names={a['ability_id']:a.get('friendly_name','') for a in data['abilities']};products=construction_products(data)
model,metadata=ProductionComponent.load(OUT/'choice.npz');baseline,_=GoalFirstPolicy.load(ROOT/'expanded-professional-imitation-01/policy.npz')
assert model.configuration['seed']==822103 and metadata['fresh_initialization'] and model.configuration['observation_memory']
production=model.abilities;worker=next(a for a in production if names[a]=='Train SCV')
pro_report=read(PRO/'report.json');teaching=Counter();teaching_keys=[]
for game in pro_report['games']:
    if game['role']=='teaching':
        for line in gzip.open(PRO/game['game']/'examples.jsonl.gz','rt'):
            e=json.loads(line);teaching[e['label']['ability']]+=1
            teaching_keys.append((game['game'],str(e['label']['source_key'])))
assert len(teaching_keys)==1267 and len(set(teaching_keys))==1267
majority=teaching.most_common(1)[0][0];assert majority==contract['majority_ability']
building_rates=[]
for game in pro_report['games']:
    if game['role']=='teaching':
        labels=[json.loads(l)['label']['ability'] for l in gzip.open(PRO/game['game']/'examples.jsonl.gz','rt')]
        building_rates.append(sum(names[a].startswith('Build ') for a in labels)/len(labels))
rate=float(np.mean(building_rates));normalizer=rate/np.sqrt(rate)+(1-rate)/np.sqrt(1-rate)
assert abs(rate-contract['teaching_building_rate'])<1e-12
assert abs(1/np.sqrt(rate)/normalizer-contract['building_weight'])<1e-12
assert abs(1/np.sqrt(1-rate)/normalizer-contract['other_weight'])<1e-12
stored={(p['game'],str(p['key'])):p for p in evaluation['predictions']};assert len(stored)==289
results=[];confusion=Counter();building_confusion=Counter()
for g in contract['evaluation_games']:
    count=Counter()
    source=[json.loads(line) for line in gzip.open(ROOT/'human-command-cohort-02'/g/'corpus/examples.jsonl.gz','rt')]
    pointers=read(ROOT/'professional-observation-memory-01'/(g+'.json'))
    pointer_by_key={str(row['source_key']):row for row in pointers}

    for line in gzip.open(PRO/g/'examples.jsonl.gz','rt'):
        e=json.loads(line);gold=e['label']['ability'];key=e['label']['source_key'];state=dict(e['observation'],recent_commands=[])
        x=state_inputs(state,*counts,products=products,missing_fields=True)
        assert not len(x['encoder'][4]) and not np.any(x['encoder'][0][:,30:94])
        pointer=pointer_by_key[str(key)];assert pointer['current_loop']==state['game_loop']
        prefix=[]
        for lag,slot in zip((45,112,336),pointer['slots']):
            candidates=[(row['observation']['game_loop'],index) for index,row in enumerate(source) if row['observation']['game_loop']<=state['game_loop']-lag]
            if not candidates:
                assert slot is None;prefix.append(None);continue
            loop,index=max(candidates);age=state['game_loop']-loop
            assert slot==dict(source_row=index,loop=loop,age_loops=age)
            past=state_inputs(dict(source[index]['observation'],recent_commands=[]),*counts,products=products,missing_fields=True)
            assert not len(past['encoder'][4]) and not np.any(past['encoder'][0][:,30:94])
            prefix.append((past,age))
        x['observation_prefix']=prefix
        probabilities=model.predict(x);pred=max(probabilities,key=probabilities.get)
        with torch.no_grad():logits=baseline.ability(baseline.encode_context(x)[1]).numpy()
        old_pred=max(production,key=lambda a:logits[a]);record=stored[(g,str(key))]
        assert record['gold']==gold and record['predicted']==pred and record['old_predicted']==old_pred
        assert all(abs(record['probabilities'][str(a)]-p)<1e-7 for a,p in probabilities.items())
        count['events']+=1;count['correct']+=pred==gold;count['majority_correct']+=majority==gold
        count['nonworker']+=gold!=worker;count['nonworker_correct']+=gold!=worker and pred==gold
        count['old_nonworker_correct']+=gold!=worker and old_pred==gold
        building=names[gold].startswith('Build ');count['buildings']+=building;count['building_correct']+=building and pred==gold
        count['predicted_buildings']+=names[pred].startswith('Build ')
        count['false_building_choices']+=not building and names[pred].startswith('Build ')
        confusion[names[gold],names[pred]]+=1
        if building:building_confusion[names[gold],names[pred]]+=1
    result=dict(game=g,**count);assert result==next(r for r in evaluation['games'] if r['game']==g);results.append(result)
totals=Counter()
for r in results:totals.update({k:v for k,v in r.items() if k!='game'})
metrics=dict(accuracy=totals['correct']/totals['events'],majority_accuracy=totals['majority_correct']/totals['events'],
             nonworker_recall=totals['nonworker_correct']/totals['nonworker'],old_nonworker_recall=totals['old_nonworker_correct']/totals['nonworker'],
             building_recall=totals['building_correct']/totals['buildings'],
             predicted_building_frequency=totals['predicted_buildings']/totals['events'],
             false_building_rate=totals['false_building_choices']/(totals['events']-totals['buildings']))
assert metrics==evaluation['metrics']==report['metrics']
passed=metrics['accuracy']>metrics['majority_accuracy'] and metrics['nonworker_recall']>=metrics['old_nonworker_recall']+.10 and metrics['building_recall']>=.40 and all(r['building_correct']>=1 for r in results) and metrics['false_building_rate']<=37/235
assert passed==evaluation['passes'] and report['status']==('passed_professional_choice_gates' if passed else 'failed_professional_choice_gates')
assert not torch.cuda.is_initialized()
guard=read(ROOT/'professional-choice-fit-03.guard.json');assert guard['returncode']==0 and guard['stop_reason'] is None and guard['peak_cpu']<=80
frame_exposure=30*sum(sum(slot is not None for slot in row['slots']) for game in pro_report['games'] if game['role']=='teaching' for row in read(ROOT/'professional-observation-memory-01'/(game['game']+'.json')))
assert frame_exposure==contract['past_frame_presentations']==report['past_frame_presentations']
prefit=read(OUT/'prefit-verification.json');assert prefit['predictions_checked']==1556
artifacts=[Path(__file__),OUT/'contract.json',OUT/'report.json',OUT/'evaluation.json',OUT/'choice.npz',ROOT/'professional-choice-fit-03.guard.json']
result=dict(status='verified_passed_professional_choice_fit' if passed else 'verified_failed_professional_choice_fit',metrics=metrics,games=results,
            building_confusions=[dict(gold=a,predicted=b,count=n) for (a,b),n in building_confusion.most_common()],
            teaching_counts={names[a]:n for a,n in teaching.items()},distinct_teaching_events=1267,
            predictions_recomputed=289,presentations=38010,past_frame_presentations=frame_exposure,peak_cpu=guard['peak_cpu'],native=False,rl=False,
            bindings={str(p):sha(p) for p in artifacts})
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({k:result[k] for k in ('status','metrics','building_confusions','peak_cpu')}))
