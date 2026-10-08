"""Bounded descriptive source audit; no paid-start or executable-plan claims."""
from pathlib import Path
from collections import Counter
import gzip, hashlib, json
import numpy as np
from src.learning.tournament_record import decode_record
from src.learning.production_execution import canonical, goal_catalog, order_goals
OUT=Path('logs/roadmap/human-queue-transitions-01'); OUT.mkdir(exist_ok=True)
record_path=Path('logs/roadmap/pro-preconverted-probe-01/fall-record-870.bin')
corpus=Path('logs/roadmap/human-visibility-reimport-01/corpus/870')
prep_path=Path('logs/roadmap/human-production-goals-02/preparation.json')
record=decode_record(record_path.read_bytes()); loops=record['steps']['game_loop']; fields=record['units']['fields']
static=json.loads((corpus/'static.json').read_text())['game_data']; catalog={a['ability_id']:a for a in static['abilities']}; names={u['unit_id']:u['name'] for u in static['units']}
goals=goal_catalog(static,json.loads(prep_path.read_text())['names'])
with gzip.open(corpus/'examples.jsonl.gz','rt') as f: rows=list(map(json.loads,f))
receipt=json.loads((corpus/'dataset.json').read_text())
unresolved=receipt['issued_command_audit']['unresolved_events']
reconcile_path=Path('logs/roadmap/pro-preconverted-probe-01/command-reconciliation-03.json')
reconciliation=next(g for g in json.loads(reconcile_path.read_text())['games'] if g['idx']==870)
selections={(r['loop'],r['sequence']):r['tags'] for r in reconciliation['selections']}
frames=[{} for _ in loops]
for i,frame in enumerate(record['units']['step']):
 if fields['alliance'][i]==1: frames[int(frame)][int(fields['id'][i])]=i
entries=[]
for row in rows:
 cmd=row['original_command']; own={u['tag']:u for u in row['observation']['units'] if u['alliance']==1}
 for actor in cmd['units']:
  if actor not in own: continue
  matches=order_goals(dict(own[actor],orders=[{'ability_id':cmd['ability']}]),goals,catalog,names)
  if len(matches)!=1: continue
  goal=matches[0][0]; frame=int(np.searchsorted(loops,row['action_loop'])); assert int(loops[frame])==row['action_loop']
  def queue(i):
   return [dict(ability=int(fields[f'order{k}']['ability'][i]),progress=float(fields[f'order{k}']['progress'][i]),target=int(fields[f'order{k}']['target_unit'][i]),point=[int(fields[f'order{k}'][axis][i]) for axis in ('x','y')]) for k in range(4) if fields[f'order{k}']['ability'][i]]
  before=queue(frames[frame][actor]); after=queue(frames[frame+1][actor]) if frame+1<len(loops) and actor in frames[frame+1] else None
  wanted=canonical(cmd['ability'],catalog)
  count=lambda q: sum(canonical(o['ability'],catalog)==wanted for o in q)
  competing=[r for r in rows if row['action_loop']<r['action_loop']<int(loops[frame+1]) and actor in r['original_command']['units']] if frame+1<len(loops) else []
  same_loop=[r for r in rows if r['action_loop']==row['action_loop'] and r['source_sequence']!=row['source_sequence'] and actor in r['original_command']['units']]
  hazards=[]
  if frame+1<len(loops):
   for item in unresolved:
    event=item['event']; key=(event['_gameloop'],event['m_sequence']); selected=selections.get(key)
    if row['action_loop']<=key[0]<int(loops[frame+1]) and (selected is None or actor & 0xFFFFFFFF in selected): hazards.append(key[1])
  if hazards: status='unresolved_actor_command_in_interval'
  elif after is None: status='next_actor_observation_missing'
  elif competing or same_loop: status='intervening_or_same_loop_command'
  elif count(after)>count(before): status='observed_queue_count_increase'
  elif count(before)>0 and count(after)>0: status='already_present_no_count_increase'
  else: status='no_observed_count_increase'
  entries.append(dict(loop=row['action_loop'],sequence=row['source_sequence'],actor=actor,actor_type=own[actor]['unit_type'],goal=goal,command=cmd,before=before,after=after,next_loop=int(loops[frame+1]) if frame+1<len(loops) else None,intervening_sequences=[r['source_sequence'] for r in competing+same_loop],unresolved_sequences=hazards,status=status))
paths=[reconcile_path,record_path,corpus/'dataset.json',corpus/'examples.jsonl.gz',corpus/'static.json',prep_path,Path(__file__),Path('src/learning/tournament_record.py'),Path('src/learning/production_execution.py')]
report=dict(status='descriptive_queue_transition_audit',game='870',training=False,rl=False,frames=len(loops),gap_quantiles=np.quantile(np.diff(loops.astype('int64')),[0,.5,.95,1]).tolist(),counts=dict(Counter(e['status'] for e in entries)),matched_addon_commands=sum('TechLab' in catalog.get(r['original_command']['ability'],{}).get('friendly_name','') or 'Reactor' in catalog.get(r['original_command']['ability'],{}).get('friendly_name','') for r in rows),matched_cancel_commands=sum(catalog.get(r['original_command']['ability'],{}).get('friendly_name','').startswith('Cancel') for r in rows),by_goal={g:dict(Counter(e['status'] for e in entries if e['goal']==g)) for g in sorted({e['goal'] for e in entries})},entries=entries,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},limitations=['Scope is matched issued production commands with observed own actors, not all raw commands.','Queue count increase is observational evidence; exact acceptance, payment, cancellation and completion attribution are not reconstructed.','Four-order truncation, observation gaps and missing reliable addon IDs prevent an executable full-plan claim.','No arbitrary build-duration subtraction or future inventory target is used.'])
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','frames','gap_quantiles','counts','by_goal']}))
