"""Recompute frozen timing predictions, cutoff diagnostics and failed gates."""
import gzip,hashlib,json
from pathlib import Path
import numpy as np
import torch
from src.learning.entity_examples import state_inputs
from src.learning.actor_selection import construction_products
from src.learning.production_component import ProductionComponent
ROOT=Path('logs/roadmap');OUT=ROOT/'mixed-production-fit-01';SOURCE=ROOT/'native-production-timing-02'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
 torch.set_num_threads(2);torch.set_num_interop_threads(2)
 contract=read(OUT/'contract.json');report=read(OUT/'report.json');evaluation=read(OUT/'timing-evaluation.json');guard=read(ROOT/'mixed-production-fit-01.guard.json')
 assert report['status']=='failed_timing_gate' and guard['status']=='completed';assert not report['choice_fit'] and not (OUT/'choice.npz').exists()
 for p,h in contract['bindings'].items():assert sha(p)==h,p
 policy,metadata=ProductionComponent.load(OUT/'timing.npz');assert metadata['frozen'] is True and policy.kind=='timing'
 counts=list(policy.encoder.engine_vocabulary);manifest=read(ROOT/'dense-timing-cohort-01/manifest.json');checks=[];training_rates=[];training_lengths=[]
 for g in manifest['games']:
  rows=list(map(json.loads,gzip.open(SOURCE/g['game']/'examples.jsonl.gz','rt')))
  if g['role']=='teaching':
   known=[e['label']['act'] for e in rows if e['label']['act'] is not None];training_rates.append(sum(known)/len(known));training_lengths.append(len(known));continue
  static=read(Path(g['output'])/'static.json');size=[static['game_info']['start_raw']['map_size'][axis] for axis in ('x','y')];products=construction_products(static['game_data']);probabilities=[]
  for e in rows:
   state=dict(e['observation'],map_size=size,recent_commands=[]);inputs=state_inputs(state,*counts,products=products,missing_fields=True);assert len(inputs['encoder'][4])==0 and np.all(inputs['encoder'][0][:,30:94]==0);probabilities.append(policy.predict(inputs))
  np.testing.assert_array_equal(probabilities,evaluation['predictions'][g['game']]);gold=np.array([bool(e['label']['act']) for e in rows]);known=np.array([e['label']['act'] is not None for e in rows]);events=sum(len(e['label']['production_keys']) for e in rows);p=np.asarray(probabilities)
  def metrics(threshold):
   prediction=p>=threshold;tp=int((prediction & known & gold).sum());pred=int((prediction & known).sum());precision=tp/pred if pred else 0;recall=tp/events
   return dict(threshold=float(threshold),predicted=pred,matched=tp,precision=precision,recall=recall,frequency_ratio=pred/events)
  threshold=evaluation['threshold'];m=metrics(threshold);saved=next((r for r in report['timing'] if r['game']==g['game']),None)
  if saved:
   for a,b in (('predicted','predicted'),('matched','matched_events'),('precision','precision'),('recall','recall'),('frequency_ratio','frequency_ratio')):assert m[a]==saved[b]
   brier=float(np.mean((p[known]-gold[known])**2));assert brier==saved['brier'];assert not saved['passes'];assert m['precision']<.5 and m['frequency_ratio']>1.2
  else:
   for saved in evaluation['calibration_candidates']:
    m_grid=metrics(saved['threshold'])
    for a,b in (('predicted','predicted'),('precision','precision'),('recall','recall'),('frequency_ratio','frequency_ratio')):assert m_grid[a]==saved[b]
  # Exhaustive cutoff diagnostic only: no refit, threshold replacement or deployment.
  rankings=[metrics(t) for t in np.unique(p[known])];feasible=[m for m in rankings if m['precision']>=.5 and m['recall']>=.5 and .8<=m['frequency_ratio']<=1.2]
  checks.append(dict(game=g['game'],role=g['role'],verified_predictions=len(rows),exhaustive_feasible_cutoffs=len(feasible),maximum_precision_at_recall_half=max((m['precision'] for m in rankings if m['recall']>=.5),default=0)))
 assert np.mean(training_rates)==contract['teaching_event_rate'];assert min(training_lengths)==contract['timing_samples_per_game'];assert report['presentations']==30*min(training_lengths)*len(training_lengths)==26100
 assert not any(.8<=r['frequency_ratio']<=1.2 for r in evaluation['calibration_candidates'])
 result=dict(status='verified_failed_timing_fit',checks=checks,calibration_threshold_qualified=False,selected_cutoff='Unqualified fallback diagnostic only; no valid grid calibration cutoff existed',choice_training=False,native=False,rl=False,bindings={str(p):sha(p) for p in [Path(__file__),OUT/'contract.json',OUT/'report.json',OUT/'timing.npz',OUT/'timing-evaluation.json',ROOT/'mixed-production-fit-01.guard.json']})
 (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');snapshot=OUT/'source-snapshot';snapshot.mkdir()
 for p in [Path(__file__),Path('logs/roadmap/run_mixed_production_fit_01.py'),Path('logs/roadmap/watch_mixed_production_fit_01.py'),*sorted(Path('src/learning').glob('*.py'))]:
  dest=snapshot/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 print(json.dumps(checks),flush=True)
if __name__=='__main__':main()
