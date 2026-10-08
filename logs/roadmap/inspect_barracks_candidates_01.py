"""Frozen score inspection at actual engine-eligible barracks states."""
import gzip,json,hashlib
from pathlib import Path
import torch
from google.protobuf.json_format import ParseDict
from s2clientprotocol import query_pb2
from src.learning.entity_execution import command_candidates,project_observation
from src.learning.entity_examples import state_inputs
from src.learning.entity_play import load_policy
from src.learning.actor_selection import construction_products
root=Path('logs/roadmap/unit-placement-human-native-01/baseline')
e=json.loads((root/'episode.json').read_text());static=json.loads((root/'static.json').read_text());catalog={a['ability_id']:a for a in static['game_data']['abilities']}
rows=[json.loads(x) for x in gzip.open(root/'trace.jsonl.gz','rt')]
found=[]
for r in rows:
 q=r['candidate_queries'];c=command_candidates(ParseDict(q['normal'],query_pb2.ResponseQuery()),ParseDict(q['autocast'],query_pb2.ResponseQuery()),catalog)
 if 321 in c and c[321]['normal']: found.append((r,c))
torch.set_num_threads(2);p,_=load_policy(e['policy'],'goal-first');sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
result=dict(scope='Read-only frozen probability diagnostic, no fit/selection/rollout/RL',eligible_rows=len(found),total_rows=len(rows),states=[],bindings={str(x):sha(x) for x in (root/'trace.jsonl.gz',root/'episode.json',root/'static.json',Path(e['policy']),Path(__file__))})
indices=sorted(set([0,len(found)//2,len(found)-1])) if found else []
for i in indices:
 r,c=found[i];s=project_observation(r['observation'],e['observation_profile']);x=state_inputs(s,*p.engine_vocabulary,products=construction_products(static['game_data']),terrain=static['terrain'],missing_fields=True)
 tags={t:j for j,t in enumerate(x['tags']) if x['actor_mask'][j]}
 x['command_candidates']={a:{m:[tags[t] for t in ts if t in tags] for m,ts in modes.items()} for a,modes in c.items()}
 x['command_candidates']={a:ms for a,ms in x['command_candidates'].items() if any(ms.values())}
 with torch.no_grad():
  scores,_=p._forward(x);pr=torch.softmax(scores['ability'].double(),0);v,k=torch.topk(pr,5)
 result['states'].append(dict(loop=s['game_loop'],player=r['observation']['player'],barracks_probability=float(pr[321]),barracks_casters=len(c[321]['normal']),top=[dict(ability=int(a),name=catalog[int(a)].get('friendly_name'),probability=float(b)) for a,b in zip(k,v)]))
assert all(sha(x)==h for x,h in result['bindings'].items())
(root.parent/'barracks-score-diagnostic.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2))
