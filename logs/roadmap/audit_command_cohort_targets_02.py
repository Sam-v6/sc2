"""Audit causal next-production supervision; no model fit or simulation."""
import gzip,hashlib,json
from pathlib import Path
from collections import Counter
from src.learning.production_targets import production_targets
ROOT=Path('logs/roadmap/human-command-cohort-02')
manifest=json.loads((ROOT/'manifest.json').read_text())
verification=json.loads((ROOT/'verification.json').read_text())
assert verification['status']=='verified_existing_command_cohort_expansion'
results=[]
for game in manifest['games']:
 folder=ROOT/game['game'];rows=list(map(json.loads,gzip.open(folder/'corpus/examples.jsonl.gz','rt')))
 data=json.loads((folder/'corpus/static.json').read_text())['game_data']
 names={a['ability_id']:a.get('friendly_name','') for a in data['abilities']}
 abilities={a for a,n in names.items() if n.startswith(('Build ','Train ','Research ')) or n in ('Morph OrbitalCommand','Morph PlanetaryFortress')}
 keys=[(r['action_loop'],r['source_sequence']) for r in rows];retained=set(keys)
 audit=json.loads((folder/'reconciliation.json').read_text())['games'][0]['audit']
 unknowns={(e['event']['_gameloop'],e['event']['m_sequence']) for e in audit['unresolved_events']}-retained
 unknowns|={(e['event']['_gameloop'],e['event']['m_sequence']) for e in json.loads((folder/'unknown.json').read_text())}-retained
 targets=production_targets(rows,abilities,unknowns)
 # Independent backwards scan: first unknown before the next production censors.
 slots=sorted([(k,'retained',i) for i,k in enumerate(keys)]+[(k,'unknown',None) for k in unknowns])
 expected=[None]*len(rows);next_event=None
 for k,kind,i in reversed(slots):
  if kind=='unknown':next_event=None;continue
  ability=rows[i]['commands'][0]['ability']
  if ability in abilities:next_event=(k,ability)
  if next_event is not None:expected[i]=dict(ability=next_event[1],delay_loops=next_event[0][0]-k[0],target_key=list(next_event[0]))
 assert expected==targets
 immediate=sum(t is not None and t['target_key']==list(k) for t,k in zip(targets,keys))
 nonzero=sum(t is not None and t['delay_loops']>0 for t in targets)
 family=Counter(names[r['commands'][0]['ability']] for r in rows if r['commands'][0]['ability'] in abilities)
 item=dict(game=game['game'],role=game['role'],human_result_code=game['human_result_code'],rows=len(rows),unknown_slots=len(unknowns),production_events=immediate,labeled_windows=sum(t is not None for t in targets),positive_delay_windows=nonzero,censored_windows=sum(t is None for t in targets),production_counts=dict(family))
 results.append(item)
 (folder/'next-production-targets.json').write_text(json.dumps(dict(targets=targets,unknown_keys=sorted(unknowns)))+'\n')
 print(json.dumps(item),flush=True)
paths=[Path(__file__),ROOT/'manifest.json',ROOT/'verification.json',Path('src/learning/production_targets.py')]
paths.extend(ROOT/g['game']/'next-production-targets.json' for g in manifest['games'])
result=dict(status='verified_next_production_labels',games=results,training=False,rl=False,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},limits=['These are labels, never live instructions or observation fields.','Unknown commands censor windows; no future outcomes fill missing commands.','Nine reused games offer limited diversity; diagnostics are not untouched evaluation.','Losses remain explicitly identified; no automatic winners-only filtering.'])
(ROOT/'target-audit.json').write_text(json.dumps(result,indent=2)+'\n')
