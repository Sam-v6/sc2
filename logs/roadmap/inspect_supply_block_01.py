"""Inspect frozen learned scores at a real supply-block boundary; no rollout."""
import gzip,json,hashlib
from pathlib import Path
import torch
from src.learning.entity_play import load_policy
from src.learning.entity_examples import state_inputs,decode_command
from src.learning.entity_execution import project_observation
from src.learning.actor_selection import construction_products
root=Path('logs/roadmap/professional-profile-native-01/baseline')
torch.set_num_threads(2)
episode=json.loads((root/'episode.json').read_text())
policy_path=Path(episode['policy'])
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(policy_path)==episode['policy_sha256']
static=json.loads((root/'static.json').read_text());catalog={a['ability_id']:a for a in static['game_data']['abilities']}
rows=[json.loads(line) for line in gzip.open(root/'trace.jsonl.gz','rt')]
selected=[('first_block',next(r for r in rows if not r['issued'])),('last_block',rows[-1])]
result=dict(scope='Fixed frozen-score diagnostic only, no fit/selection/live game/RL',bindings={str(p):sha(p) for p in (policy_path,root/'trace.jsonl.gz',root/'episode.json',root/'static.json',Path(__file__))},states={})
for label,row in selected:
 policy,_=load_policy(policy_path,'goal-first')
 state=project_observation(row['observation'],episode['observation_profile'])
 x=state_inputs(state,*policy.engine_vocabulary,products=construction_products(static['game_data']),terrain=static['terrain'],missing_fields=True)
 with torch.no_grad():
  logits,pred=policy._forward(x)
  probabilities=torch.softmax(logits['ability'],0)
  values,indices=torch.topk(probabilities,15)
 depot=policy.predict(x,ability=319)
 result['states'][label]=dict(loop=state['game_loop'],player=row['observation']['player'],top_abilities=[dict(ability=int(i),name=catalog.get(int(i),{}).get('friendly_name'),probability=float(v)) for v,i in zip(values,indices)],depot_probability=float(probabilities[319]),depot_arguments_if_forced=decode_command(depot,x).as_dict(),observed_unavailable_command=row['command'])
assert all(sha(p)==h for p,h in result['bindings'].items())
(root.parent/'supply-score-diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result['states'],indent=2))
