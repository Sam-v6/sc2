"""One frozen mixed-source supervised fit, with offline gates before native play."""
import gzip,hashlib,json,os,time
from collections import Counter
from pathlib import Path
import numpy as np
import torch
from src.learning.actor_selection import construction_products
from src.learning.entity_examples import state_inputs
from src.learning.production_component import ProductionComponent
from src.learning.goal_first_policy import GoalFirstPolicy
ROOT=Path('logs/roadmap');NATIVE=ROOT/'native-production-timing-02';PRO=ROOT/'professional-production-choice-01';OUT=ROOT/'mixed-production-fit-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def lines(p):return map(json.loads,gzip.open(p,'rt'))
def main():
 assert os.environ['CUDA_VISIBLE_DEVICES']=='';torch.set_num_threads(2);torch.set_num_interop_threads(2);torch.use_deterministic_algorithms(True);assert not torch.cuda.is_initialized()
 OUT.mkdir(exist_ok=False);bindings={}
 for root,status in ((NATIVE,'verified_native_issuance_proofs_and_current_timing_labels'),(PRO,'verified_distinct_source_choices_and_current_observations')):
  verification=read(root/'verification.json');assert verification['status']==status
  for p,h in verification['bindings'].items():assert sha(p)==h,p
  report=read(root/'report.json')
  for p,h in report['bindings'].items():assert sha(p)==h,p
  bindings.update(report['bindings']);bindings.update(verification['bindings']);bindings[str(root/'verification.json')]=sha(root/'verification.json')
 catalog_path=ROOT/'dense-timing-cohort-01/51574/static.json';static=read(catalog_path);data=static['game_data'];counts=[max(v[k] for v in data[n])+1 for n,k in (('units','unit_id'),('abilities','ability_id'),('upgrades','upgrade_id'))];products=construction_products(data)
 production=[a['ability_id'] for a in data['abilities'] if a.get('friendly_name','').startswith(('Build ','Train ','Research ')) or a.get('friendly_name') in ('Morph OrbitalCommand','Morph PlanetaryFortress')];production=sorted(set(production));names={a['ability_id']:a.get('friendly_name','') for a in data['abilities']};worker=next(a for a in production if names[a]=='Train SCV')
 def inputs(observation,size):return state_inputs(dict(observation,map_size=observation.get('map_size',size),recent_commands=[]),*counts,products=products,missing_fields=True)
 native_manifest=read(ROOT/'dense-timing-cohort-01/manifest.json');native={};native_events={}
 for game in native_manifest['games']:
  source_static=read(Path(game['output'])/'static.json');size=[source_static['game_info']['start_raw']['map_size'][a] for a in ('x','y')];rows=[]
  for example in lines(NATIVE/game['game']/'examples.jsonl.gz'):rows.append((inputs(example['observation'],size),example['label']))
  native[game['game']]=rows;native_events[game['game']]=read(NATIVE/game['game']/'events.json');print(json.dumps(dict(stage='native_inputs',game=game['game'],rows=len(rows))),flush=True)
 pro_report=read(PRO/'report.json');professional={}
 for g in pro_report['games']:
  professional[g['game']]=[(inputs(e['observation'],None),e['label']['ability'],e['label']['source_key']) for e in lines(PRO/g['game']/'examples.jsonl.gz')];print(json.dumps(dict(stage='professional_inputs',game=g['game'],rows=len(professional[g['game']]))),flush=True)
 x=native['51574'][0][0];raw,_,_,scene,_,roles=x['encoder'];dimensions=(raw.shape[1],len(scene),roles.shape[1],*counts[:2],2)
 train_ids=[g['game'] for g in native_manifest['games'] if g['role']=='teaching'];calibration=[g['game'] for g in native_manifest['games'] if g['role']=='calibration_reused'];evaluation=[g['game'] for g in native_manifest['games'] if g['role']=='evaluation_reused'];assert calibration==['50925'] and evaluation==['51960','51482']
 train={g:[(x,bool(y['act'])) for x,y in native[g] if y['act'] is not None] for g in train_ids};per_game=min(map(len,train.values()));event_rate=float(np.mean([np.mean([y for _,y in rows]) for rows in train.values()]))
 pro_train=[g['game'] for g in pro_report['games'] if g['role']=='teaching'];pro_eval=[g['game'] for g in pro_report['games'] if g['role']=='diagnostic'];assert sum(len(professional[g]) for g in pro_train)==1267
 baseline_path=ROOT/'expanded-professional-imitation-01/policy.npz';baseline,_=GoalFirstPolicy.load(baseline_path)
 for p in [Path(__file__),Path(os.environ['SC2_FIT_WATCHDOG']),catalog_path,baseline_path,*sorted(Path('src/learning').glob('*.py'))]:bindings[str(p)]=sha(p)
 # Exact earlier source hashes inside extraction manifests are historical; their
 # original code was archived before the shared encoder refactor. Label bindings above are live.
 assert all(sha(p)==h for p,h in bindings.items())
 contract=dict(seed_timing=822101,seed_choice=822102,dimensions=dimensions,type_status=True,hidden=64,timing_epochs=30,choice_epochs=30,batch_size=16,learning_rate=.001,timing_samples_per_game=per_game,teaching_event_rate=event_rate,training_players=['Mez'],calibration_players=['Lyra'],evaluation_players=['Huski','Rom'],diagnostics_reused=True,reserved_untouched=True,choice_teaching_events=1267,source_definition='Masters original human SCmdEvent timing; professional verified production choice including provenance-backed manager repeats',presentations_bound=101940,planned_presentations=30*per_game*len(train_ids)+30*1267,timing_frequency='Predicted acts versus verified production event count, over resolved windows only; unknown-window predictions reported separately',gates=dict(brier='below equal-game teaching event-rate baseline on each evaluation game',event_precision=.5,event_recall=.5,event_frequency_relative_tolerance=.2,nonworker_margin=.10,production_building='at least one correct choice in every professional diagnostic game'),bindings=bindings,runtime=dict(torch=torch.__version__,numpy=np.__version__,threads=2,cuda_initialized=False),rl=False)
 assert contract['planned_presentations']<=101940;write(OUT/'contract.json',contract);start=time.monotonic();presentations=0
 def fit(model,epochs,sampler,weighted=False):
  nonlocal presentations
  optimizer=torch.optim.Adam(model.parameters(),lr=.001)
  for epoch in range(epochs):
   samples=sampler(epoch);total=0
   for offset in range(0,len(samples),16):
    assert time.monotonic()-start<900,'optimizer wall bound';batch=samples[offset:offset+16];optimizer.zero_grad();losses=[model.loss(x,y)*weight for x,y,weight in batch];loss=torch.stack(losses).mean();assert torch.isfinite(loss);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);optimizer.step();presentations+=len(batch);total+=float(loss.detach())*len(batch)
   print(json.dumps(dict(stage=model.kind,epoch=epoch+1,loss=total/len(samples),presentations=presentations,wall=time.monotonic()-start)),flush=True)
 timing=ProductionComponent(dimensions,'timing',hidden=64,seed=822101,type_status=True);rng=np.random.default_rng(822101)
 def timing_samples(epoch):
  samples=[]
  for game in train_ids:samples.extend((train[game][i][0],train[game][i][1],1.) for i in rng.choice(len(train[game]),per_game,replace=False))
  rng.shuffle(samples);return samples
 fit(timing,30,timing_samples);timing.requires_grad_(False).eval();timing.save(OUT/'timing.npz',dict(phase='mixed_source_timing',frozen=True))
 predictions={g:[timing.predict(x) for x,_ in native[g]] for g in calibration+evaluation}
 def timing_metrics(game,threshold):
  rows=native[game];p=np.asarray(predictions[game]);known=np.asarray([y['act'] is not None for _,y in rows]);gold=np.asarray([bool(y['act']) for _,y in rows]);acts=p>=threshold
  verified_events=sum(len(y['production_keys']) for _,y in rows);tp=int(np.sum(acts & known & gold));predicted=int(np.sum(acts & known));recall=tp/verified_events if verified_events else 0;precision=tp/predicted if predicted else 0
  brier=float(np.mean((p[known]-gold[known])**2));base=float(np.mean((event_rate-gold[known])**2));frequency=predicted/verified_events if verified_events else 0
  return dict(game=game,threshold=threshold,known=int(known.sum()),unknown=int((~known).sum()),brier=brier,baseline_brier=base,precision=precision,recall=recall,frequency_ratio=frequency,predicted=predicted,verified_events=verified_events,matched_events=tp,quiet_false_positive=int(np.sum(acts & known & ~gold)),quiet_windows=int(np.sum(known & ~gold)),unknown_predictions=int(np.sum(acts & ~known)),passes=brier<base and precision>=.5 and recall>=.5 and .8<=frequency<=1.2)
 candidates=[timing_metrics('50925',float(t)) for t in np.linspace(.05,.95,19)];eligible=[r for r in candidates if .8<=r['frequency_ratio']<=1.2]
 threshold=max(eligible or candidates,key=lambda r:(2*r['precision']*r['recall']/max(r['precision']+r['recall'],1e-12),-r['threshold']))['threshold'];timing_results=[timing_metrics(g,threshold) for g in evaluation];write(OUT/'timing-evaluation.json',dict(calibration_candidates=candidates,threshold=threshold,evaluation=timing_results,predictions=predictions,unknowns_not_guessed=True))
 timing_pass=all(r['passes'] for r in timing_results)
 if not timing_pass:
  assert all(sha(p)==h for p,h in bindings.items());write(OUT/'report.json',dict(status='failed_timing_gate',timing=timing_results,choice_fit=False,native=False,rl=False,presentations=presentations,wall=time.monotonic()-start,bindings=bindings));print('FAILED_TIMING_GATE',flush=True);return
 frozen={k:v.detach().numpy().copy() for k,v in timing.state_dict().items()};choice=ProductionComponent(dimensions,'choice',production,hidden=64,seed=822102,type_status=True);choice.encoder.load_state_dict(timing.encoder.state_dict());rng=np.random.default_rng(822102)
 def choice_samples(epoch):
  samples=[];total=sum(len(professional[g]) for g in pro_train)
  for g in pro_train:samples.extend((x,y,total/(len(pro_train)*len(professional[g]))) for x,y,_ in professional[g])
  rng.shuffle(samples);return samples
 fit(choice,30,choice_samples);assert all(np.array_equal(frozen[k],v.detach().numpy()) for k,v in timing.state_dict().items());choice.eval();choice.save(OUT/'choice.npz',dict(phase='professional_conditional_production',timing_unchanged=True))
 prior=Counter(y for g in pro_train for _,y,_ in professional[g] if y!=worker).most_common(1)[0][0];results=[];stored=[]
 for game in pro_eval:
  rows=professional[game];correct=old_correct=prior_correct=nonworker=building_correct=0
  for x,gold,key in rows:
   probabilities=choice.predict(x);predicted=max(probabilities,key=probabilities.get)
   with torch.no_grad():old_logits=baseline.ability(baseline.encode_context(x)[1]).numpy()
   old_predicted=max(production,key=lambda a:old_logits[a]);is_nonworker=gold!=worker
   nonworker+=is_nonworker;correct+=is_nonworker and predicted==gold;old_correct+=is_nonworker and old_predicted==gold;prior_correct+=is_nonworker and prior==gold;building_correct+=names[gold].startswith('Build ') and predicted==gold
   stored.append(dict(game=game,key=key,gold=gold,predicted=predicted,old_predicted=old_predicted,prior=prior))
  recall=correct/nonworker;old_recall=old_correct/nonworker;prior_recall=prior_correct/nonworker;results.append(dict(game=game,events=len(rows),nonworker=nonworker,correct=correct,recall=recall,old_correct=old_correct,old_recall=old_recall,prior_correct=prior_correct,prior_recall=prior_recall,building_correct=building_correct))
 total=sum(r['nonworker'] for r in results);recall=sum(r['correct'] for r in results)/total;old_recall=sum(r['old_correct'] for r in results)/total;prior_recall=sum(r['prior_correct'] for r in results)/total;choice_pass=recall>=max(old_recall,prior_recall)+.1 and all(r['building_correct']>0 for r in results)
 write(OUT/'choice-evaluation.json',dict(results=results,predictions=stored,recall=recall,old_recall=old_recall,prior_recall=prior_recall,passes=choice_pass,legality_masks=False,baseline='Old expanded GoalFirst ability logits, current state/no history, restricted to native production families'))
 assert presentations<=101940 and all(sha(p)==h for p,h in bindings.items());assert not torch.cuda.is_initialized()
 write(OUT/'report.json',dict(status='passed_supervised_gates' if choice_pass else 'failed_professional_choice_gate',timing=timing_results,choice=results,timing_pass=True,choice_pass=choice_pass,presentations=presentations,wall=time.monotonic()-start,bindings=bindings,native=False,rl=False));print(json.dumps(dict(status='passed_supervised_gates' if choice_pass else 'failed_professional_choice_gate',presentations=presentations)),flush=True)
if __name__=='__main__':main()
