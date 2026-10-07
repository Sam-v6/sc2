"""Independent original-command pair labels and reloaded classifier metrics."""
import gzip,hashlib,json,pickle
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix,hstack,load_npz
ROOT=Path('logs/roadmap');DATA=ROOT/'human-production-goals-02';OUT=ROOT/'human-production-precedence-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((DATA/'preparation.json').read_text());r={'names':prep['names']}
for p,h in prep['bindings'].items():assert sha(p)==h,p
names=r['names'];events={}
for item in prep['coverage']:
 g=item['game'];d=next(Path(p).parent for p in prep['bindings'] if p.endswith(f'/{g}/dataset.json'));s=json.loads((d/'static.json').read_text())['game_data']
 abilities={a['ability_id']:a for a in s['abilities']};types={u['unit_id']:u['name'] for u in s['units']};products={u['name']:u for u in s['units']};upgrades={u['name']:u for u in s['upgrades']}
 def canonical(a):return abilities.get(a,{}).get('remaps_to_ability_id') or a
 mapping=defaultdict(list)
 for name in names:
  kind,n=name.split(':',1);native=(products if kind=='unit' else upgrades)[n];mapping[canonical(native['ability_id'])].append(name)
 events[g]=[]
 with gzip.open(d/'examples.jsonl.gz','rt') as f:
  for line in f:
   row=json.loads(line);c=row['original_command'];matches=mapping[canonical(c['ability'])]
   if len(matches)>1:
    own={u['tag']:types[u['unit_type']] for u in row['observation']['units'] if u['alliance']==1}
    parents={own[t] for t in c['units'] if t in own}
    matches=[n for n in matches if any(abilities[products[n[5:]]['ability_id']].get('friendly_name','').endswith(' '+p) for p in parents)]
   if len(matches)==1:events[g].append((row['action_loop'],row['source_sequence'],matches[0]))
baseline=defaultdict(lambda:[0.,0.]);checked=0
for role in ('teaching','development'):
 rows=json.loads((OUT/f'{role}-pairs.json').read_text());anchors=json.loads((DATA/f'{role}-rows.json').read_text());x=load_npz(DATA/f'{role}-state.npz').astype(np.float32);count_predictions=np.load(DATA/f'model-{role}-predictions.npy')
 frequencies=Counter((v['game'],tuple(v['source_pair'][0] or (-1,-1)),tuple(v['source_pair'][1] or (-1,-1)),v['left'],v['right']) for v in rows);totals=Counter()
 for v in rows:
  key=(v['game'],tuple(v['source_pair'][0] or (-1,-1)),tuple(v['source_pair'][1] or (-1,-1)),v['left'],v['right']);totals[v['game']]+=1/frequencies[key]
 for v in rows:
  anchor=anchors[v['row']];assert anchor['game']==v['game'] and anchor['loop']==v['loop'];first={}
  for t,seq,n in events[v['game']]:
   if v['loop']<=t<v['loop']+1008:first[n]=min(first.get(n,(t,seq)),(t,seq))
  a=first.get(names[v['left']]);b=first.get(names[v['right']]);assert [list(a) if a else None,list(b) if b else None]==v['source_pair']
  ta=a[0] if a else v['loop']+1008;tb=b[0] if b else v['loop']+1008;assert ta!=tb and int(ta<tb)==v['target']
  assert v['proposal_only']==bool(np.rint(count_predictions[v['row'],v['left']])>0 and np.rint(count_predictions[v['row'],v['right']])>0)
  key=(v['game'],tuple(v['source_pair'][0] or (-1,-1)),tuple(v['source_pair'][1] or (-1,-1)),v['left'],v['right']);assert abs(v['weight']-1/frequencies[key]/totals[v['game']])<1e-12
  if role=='teaching':baseline[(v['left'],v['right'])][v['target']]+=v['weight']
 checked+=len(rows)
paths=[Path(__file__),DATA/'preparation.json',OUT/'teaching-pairs.json',OUT/'development-pairs.json']
receipt=dict(status='verified_original_command_labels_weights',pairs=checked,rl=False,bindings={str(p):sha(p) for p in paths})
(OUT/'label-verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
