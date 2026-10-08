"""Compare live-policy feature path to every saved human development row."""
import gzip,hashlib,json
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz,vstack
from src.learning.actor_selection import construction_products
from src.learning.production_goal_policy import current_features
OUT=Path('logs/roadmap/human-production-goals-01')
prep=json.loads((OUT/'preparation.json').read_text())
vocab=json.loads(Path('logs/roadmap/joint-professional-fit-05/configuration.json').read_text())['vocabulary']
rows=json.loads((OUT/'development-rows.json').read_text()); source={}; products={}
for g in {r['game'] for r in rows}:
    d=Path('logs/roadmap/pro-demonstrations-07')/g
    with gzip.open(d/'examples.jsonl.gz','rt') as f:source[g]=list(map(json.loads,f))
    products[g]=construction_products(json.loads((d/'static.json').read_text())['game_data'])
profile=json.loads(Path('logs/roadmap/professional-observation-profile-01.json').read_text())
features=vstack([current_features(source[r['game']][r['row']]['observation'],vocab,products[r['game']],profile) for r in rows]).tocsr()
expected=load_npz(OUT/'development-state.npz')
difference=features-expected
assert difference.nnz==0, (difference.nnz, np.abs(difference.data).max())
report=dict(status='verified',rows=len(rows),exact_equal=True,history_removed=True,
            bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/learning/production_goal_policy.py'),OUT/'development-state.npz']})
(OUT/'feature-parity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
