import gzip,hashlib,json
from pathlib import Path
from src.learning.production_inventory_goals import HumanGoalLibrary
from src.learning.production_inventory import observation_stock
ROOT=Path('logs/roadmap');OUT=ROOT/'human-goal-retrieval-01'
lib=HumanGoalLibrary.load(OUT);audit=json.loads((OUT/'audit.json').read_text())
rows=json.loads((OUT/'native-retrievals.json').read_text());native=ROOT/'human-production-cadence-native-01/D'
static=json.loads((native/'static.json').read_text())
with gzip.open(native/'trace.jsonl.gz','rt') as f:trace=[r for r in map(json.loads,f) if r['phase']=='forecast']
for row,expected in zip(trace,rows,strict=True):
 state=row['observation'];target,source=lib.select(state['game_loop'],observation_stock(state,static),audit['native_public_selected_race'])
 assert target==expected['target'] and all(source[k]==expected['source'][k] for k in ['game','row','loop'])
 assert source['future_loop']==expected['future_loop'] and source['expires']==expected['goal_expires']
 assert source['distance']==expected['distance'] and source['supported']==expected['supported']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
receipt=dict(status='verified_runtime_library_parity',forecasts=len(trace),bindings={str(p):sha(p) for p in [Path(__file__),Path('src/learning/production_inventory_goals.py'),OUT/'audit.json',OUT/'verification.json',OUT/'native-retrievals.json']})
(OUT/'runtime-verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
