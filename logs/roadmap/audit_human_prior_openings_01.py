"""Opening proposal/prior diagnostic; no fit or native competence claim."""
import gzip,hashlib,json
from pathlib import Path
from collections import defaultdict
import numpy as np
ROOT=Path('logs/roadmap');DATA=ROOT/'human-production-goals-02';OUT=ROOT/'human-production-utility-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
receipt=json.loads((OUT/'verification.json').read_text());assert receipt['status']=='verified_labels_predictions_metrics_gates'
for p,h in receipt['bindings'].items():assert sha(p)==h,p
report=json.loads((OUT/'report.json').read_text());names=report['names'];baseline=report['baseline'];pairs=json.loads((OUT/'teaching-pairs.json').read_text());rebuilt=defaultdict(lambda:[0.,0.])
for p in pairs:rebuilt[f"{p['left']},{p['right']}"][p['target']]+=p['weight']
assert dict(rebuilt)==baseline
np.save(OUT/'human-prior-source-counts.npy',np.array([sum(v) for v in baseline.values()]))
def probability(a,b):
 i,j=names.index(a),names.index(b);v=baseline.get(f'{min(i,j)},{max(i,j)}',[0,0]);s=sum(v)
 p=v[1]/s if s else .5
 return p if i<j else 1-p
prepared=json.loads((DATA/'preparation.json').read_text());diagnostics=[]
for role in ('teaching','development'):
 anchors=json.loads((DATA/f'{role}-rows.json').read_text());pred=np.load(DATA/f'model-{role}-predictions.npy')
 for g in sorted({a['game'] for a in anchors}):
  i=next(i for i,a in enumerate(anchors) if a['game']==g);anchor=anchors[i];candidates=[n for n,v in zip(names,pred[i]) if np.rint(v)>0]
  scores={n:sum(probability(n,m) for m in candidates if m!=n)/max(len(candidates)-1,1) for n in candidates}
  directory=next(Path(p).parent for p in prepared['bindings'] if p.endswith(f'/{g}/dataset.json'))
  with gzip.open(directory/'examples.jsonl.gz','rt') as f:first=json.loads(next(f))
  diagnostics.append(dict(game=g,role=role,loop=anchor['loop'],first_human_ability=first['original_command']['ability'],candidates=candidates,priority=sorted(candidates,key=lambda n:(-scores[n],n)),scores=scores,depot_before_refinery=probability('unit:SupplyDepot','unit:Refinery'),scv_before_depot=probability('unit:SCV','unit:SupplyDepot')))
paths=[Path(__file__),OUT/'verification.json',OUT/'report.json',OUT/'teaching-pairs.json']
r=dict(status='verified_opening_prior_diagnostic',rl=False,teacher_prior=baseline,names=names,openings=diagnostics,limits=['Opening rankings are unconditioned human-derived family probabilities, not native castability or competence.'],bindings={str(p):sha(p) for p in paths})
(ROOT/'human-prior-openings-01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(diagnostics),flush=True)
