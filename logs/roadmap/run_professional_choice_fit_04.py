"""Fresh professional current-state choice fit after native primitive gates."""
import gzip,hashlib,json,os,time
from collections import Counter
from pathlib import Path
import numpy as np
import torch
from src.learning.actor_selection import construction_products
from src.learning.entity_examples import state_inputs
from src.learning.production_component import ProductionComponent
from src.learning.goal_first_policy import GoalFirstPolicy
ROOT=Path('logs/roadmap');PRO=ROOT/'professional-production-choice-02';OUT=ROOT/'professional-choice-fit-04'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def main():
 assert os.environ['CUDA_VISIBLE_DEVICES']==''
 torch.set_num_threads(2);torch.set_num_interop_threads(2);torch.use_deterministic_algorithms(True)
 assert not torch.cuda.is_initialized()
 execution=ROOT/'broad-production-combat-02/verification.json'
 assert read(execution)['status']=='verified_native_production_combat_execution'
 OUT.mkdir(exist_ok=False);bindings={str(execution):sha(execution)}
 verification=read(PRO/'verification.json');assert verification['status']=='verified_distinct_source_choices_and_current_observations'
 report=read(PRO/'report.json')
 for manifest in (verification,report):
  for p,h in manifest['bindings'].items():assert sha(p)==h,p
  bindings.update(manifest['bindings'])
 bindings[str(PRO/'verification.json')]=sha(PRO/'verification.json')
 catalog=ROOT/'dense-timing-cohort-01/51574/static.json';data=read(catalog)['game_data']
 counts=[max(r[k] for r in data[n])+1 for n,k in (('units','unit_id'),('abilities','ability_id'),('upgrades','upgrade_id'))]
 products=construction_products(data);names={a['ability_id']:a.get('friendly_name','') for a in data['abilities']}
 production=sorted(a for a,name in names.items() if name.startswith(('Build ','Train ','Research ')) or name in ('Morph OrbitalCommand','Morph PlanetaryFortress'))
 worker=next(a for a in production if names[a]=='Train SCV');games={}
 for game in report['games']:
  rows=[]
  for line in gzip.open(PRO/game['game']/'examples.jsonl.gz','rt'):
   e=json.loads(line);state=dict(e['observation'],recent_commands=[])
   x=state_inputs(state,*counts,products=products,missing_fields=True)
   assert not np.any(x['encoder'][0][:,30:94])
   rows.append((x,e['label']['ability'],e['label']['source_key']))
  games[game['game']]=rows
 train=[g['game'] for g in report['games'] if g['role']=='teaching'];evaluation=[g['game'] for g in report['games'] if g['role']=='diagnostic']
 assert sum(len(games[g]) for g in train)==2173
 raw,_,_,scene,_,roles=games[train[0]][0][0]['encoder'];dimensions=(raw.shape[1],len(scene),roles.shape[1],*counts[:2],2)
 baseline_path=ROOT/'expanded-professional-imitation-01/policy.npz';baseline,_=GoalFirstPolicy.load(baseline_path)
 for p in [Path(__file__),Path(os.environ['SC2_FIT_WATCHDOG']),catalog,baseline_path,*sorted(Path('src/learning').glob('*.py'))]:bindings[str(p)]=sha(p)
 counts_train=Counter(y for g in train for _,y,_ in games[g]);majority=counts_train.most_common(1)[0][0]
 building_rate=float(np.mean([np.mean([names[y].startswith('Build ') for _,y,_ in games[g]]) for g in train]))
 normalizer=building_rate/np.sqrt(building_rate)+(1-building_rate)/np.sqrt(1-building_rate)
 control_path=ROOT/'professional-choice-fit-02/contract.json';control=read(control_path)
 assert control['seed']==822103 and control['epochs']==30
 family_weights={True:control['building_weight'],False:control['other_weight']}
 bindings[str(control_path)]=sha(control_path)

 contract=dict(seed=822103,epochs=30,batch_size=16,learning_rate=.001,hidden=64,type_status=True,
  dimensions=dimensions,presentations=65190,game_balanced_loss=True,
  family_loss='Frozen fit02 building/other weights; not recomputed on expanded teaching data',
  teaching_building_rate=building_rate,building_weight=family_weights[True],other_weight=family_weights[False],
  paired_control='professional-choice-fit-02; same fresh seed, architecture, fixed weights, epochs and optimizer; five previously used human teaching games added, original diagnostics unchanged',
  initialization='Fresh; failed timing weights are not loaded',teacher_events=2173,
  evaluation_games=evaluation,diagnostics_reused=True,reserved_untouched=True,majority_ability=majority,
  gates=dict(overall_accuracy='strictly above teaching majority baseline',nonworker_margin=.10,
             production_building_recall=.40,correct_building_per_game=1,false_building_rate_max=37/235),
  scheduler='Future native test only: fixed 44-loop scheduling, one outstanding request, save resources for selected ability; explicit assistance',
  timing_model=False,legality_masks=False,rl=False,native=False,bindings=bindings)
 write(OUT/'contract.json',contract)
 model=ProductionComponent(dimensions,'choice',production,hidden=64,seed=822103,type_status=True)
 optimizer=torch.optim.Adam(model.parameters(),lr=.001);rng=np.random.default_rng(822103);start=time.monotonic();presentations=0
 for epoch in range(30):
  samples=[(x,y,2173/(len(train)*len(games[g]))*family_weights[names[y].startswith('Build ')]) for g in train for x,y,_ in games[g]]
  rng.shuffle(samples);total=0
  for offset in range(0,len(samples),16):
   assert time.monotonic()-start<900
   batch=samples[offset:offset+16];optimizer.zero_grad();loss=torch.stack([model.loss(x,y)*w for x,y,w in batch]).mean()
   assert torch.isfinite(loss);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);optimizer.step()
   presentations+=len(batch);total+=float(loss.detach())*len(batch)
  print(json.dumps(dict(epoch=epoch+1,loss=total/len(samples),presentations=presentations,wall=time.monotonic()-start)),flush=True)
 model.eval();model.save(OUT/'choice.npz',dict(phase='professional_current_state_production_choice',fresh_initialization=True))
 predictions=[];results=[]
 for g in evaluation:
  counter=Counter()
  for x,gold,key in games[g]:
   probabilities=model.predict(x);pred=max(probabilities,key=probabilities.get)
   with torch.no_grad():old=baseline.ability(baseline.encode_context(x)[1]).numpy()
   old_pred=max(production,key=lambda a:old[a]);building=names[gold].startswith('Build ')
   counter['events']+=1;counter['correct']+=pred==gold;counter['majority_correct']+=majority==gold
   counter['nonworker']+=gold!=worker;counter['nonworker_correct']+=gold!=worker and pred==gold
   counter['old_nonworker_correct']+=gold!=worker and old_pred==gold
   counter['buildings']+=building;counter['building_correct']+=building and pred==gold
   counter['predicted_buildings']+=names[pred].startswith('Build ')
   counter['false_building_choices']+=not building and names[pred].startswith('Build ')
   predictions.append(dict(game=g,key=key,gold=gold,predicted=pred,old_predicted=old_pred,
                           probability=float(probabilities[pred]),probabilities={str(a):float(p) for a,p in probabilities.items()}))
  results.append(dict(game=g,**counter));print(json.dumps(results[-1]),flush=True)
 totals=Counter()
 for r in results:totals.update({k:v for k,v in r.items() if k!='game'})
 metrics=dict(accuracy=totals['correct']/totals['events'],majority_accuracy=totals['majority_correct']/totals['events'],
  nonworker_recall=totals['nonworker_correct']/totals['nonworker'],old_nonworker_recall=totals['old_nonworker_correct']/totals['nonworker'],
  building_recall=totals['building_correct']/totals['buildings'],
  predicted_building_frequency=totals['predicted_buildings']/totals['events'],
  false_building_rate=totals['false_building_choices']/(totals['events']-totals['buildings']))
 passed=metrics['accuracy']>metrics['majority_accuracy'] and metrics['nonworker_recall']>=metrics['old_nonworker_recall']+.10 and metrics['building_recall']>=.40 and all(r['building_correct']>=1 for r in results) and metrics['false_building_rate']<=37/235
 write(OUT/'evaluation.json',dict(games=results,metrics=metrics,predictions=predictions,passes=passed))
 assert presentations==65190 and all(sha(p)==h for p,h in bindings.items()) and not torch.cuda.is_initialized()
 for p in bindings:
  source=Path(p)
  if source.suffix=='.py':
   dest=OUT/'source-snapshot'/source;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes())
 write(OUT/'report.json',dict(status='passed_professional_choice_gates' if passed else 'failed_professional_choice_gates',
  metrics=metrics,presentations=presentations,wall=time.monotonic()-start,bindings=bindings,native=False,rl=False))
 print(json.dumps(dict(passed=passed,metrics=metrics,presentations=presentations)),flush=True)
if __name__=='__main__':main()
