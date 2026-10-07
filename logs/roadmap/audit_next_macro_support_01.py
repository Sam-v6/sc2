"""Measure duplicate target exposure and future-actor mismatch without fitting."""
import gzip,hashlib,json
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
ROOT=Path('logs/roadmap/human-command-cohort-02');OUT=Path('logs/roadmap/next-macro-support-01');OUT.mkdir(exist_ok=False)
manifest=json.loads((ROOT/'manifest.json').read_text());audit=json.loads((ROOT/'target-audit.json').read_text())
for p,h in audit['bindings'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
results=[]
for game in manifest['games']:
 folder=ROOT/game['game'];rows=list(map(json.loads,gzip.open(folder/'corpus/examples.jsonl.gz','rt')));targets=json.loads((folder/'next-production-targets.json').read_text())['targets'];bykey={(r['action_loop'],r['source_sequence']):r for r in rows}
 names={a['ability_id']:a.get('friendly_name','') for a in json.loads((folder/'corpus/static.json').read_text())['game_data']['abilities']}
 windows=Counter();events=Counter();exposures=Counter();missing_actors=Counter();missing_targets=Counter();delays=[];per_family=defaultdict(list)
 for row,target in zip(rows,targets,strict=True):
  if target is None:continue
  key=tuple(target['target_key']);future=bykey[key];command=future['commands'][0];ability=command['ability'];assert ability==target['ability']
  name=names[ability];windows[name]+=1;exposures[key]+=1;per_family[name].append(target['delay_loops']);delays.append(target['delay_loops'])
  if key==(row['action_loop'],row['source_sequence']):events[name]+=1
  current={u['tag'] for u in row['observation']['units'] if u['alliance']==1 and u.get('observed',True)}
  known={u['tag'] for u in row['observation']['units']}|{u['tag'] for u in row['observation']['memory']}
  if not set(command['units'])<=current:missing_actors[name]+=1
  if command['target_unit'] is not None and command['target_unit'] not in known:missing_targets[name]+=1
 assert sum(events.values())==len(exposures)
 result=dict(game=game['game'],role=game['role'],windows=sum(windows.values()),distinct_target_events=len(exposures),max_windows_per_event=max(exposures.values()),future_actor_unavailable_windows=sum(missing_actors.values()),future_unit_target_unavailable_windows=sum(missing_targets.values()),loop_delay_quantiles=dict(zip(('median','p90','max'),map(float,np.quantile(delays,[.5,.9,1])))),families={n:dict(events=events[n],windows=windows[n],future_actor_unavailable=missing_actors[n],future_unit_target_unavailable=missing_targets[n],median_delay_loops=float(np.median(per_family[n]))) for n in sorted(windows)})
 results.append(result)
 print(json.dumps({k:v for k,v in result.items() if k!='families'}),flush=True)
paths=[Path(__file__),ROOT/'manifest.json',ROOT/'target-audit.json']
for g in manifest['games']:paths.extend(ROOT/g['game']/p for p in ('corpus/examples.jsonl.gz','corpus/static.json','next-production-targets.json'))
report=dict(status='completed_source_support_audit',games=results,training=False,rl=False,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},limits=['Duplicate windows are not independent command targets; weight exposure by source event if used.','Future actors/targets cannot be copied into current observations or current full-command labels.','Unavailability uses currently observed own actors and observed/remembered targets, not native ability legality.','No reserved replay or newly independent diagnostic source is accessed.'])
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
