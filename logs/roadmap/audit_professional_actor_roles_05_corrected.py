from pathlib import Path
from collections import Counter
import json
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_train import collect

policy,_=JointEntityPolicy.load(Path('logs/roadmap/joint-professional-fit-05/policy.npz'))
counts=Counter();categories={}
examples,_=collect([Path('logs/roadmap/pro-demonstrations-07/774')],(1970,3801,296),spatial=True,missing_fields=True)
for inputs,label,command,reason in examples:
    prediction=policy.predict(inputs)
    human=Counter(int(inputs['encoder'][1][inputs['tags'].index(t)]) for t in command.units)
    actual=Counter(int(inputs['encoder'][1][i]) for i in prediction['actors'])
    category='worker_only' if set(human)=={45} else 'townhall_only' if set(human)<={18,130,132} else 'other'
    current=categories.setdefault(category,Counter())
    current['commands']+=1
    current['ability_correct']+=prediction['ability']==command.ability
    current['exact_type_counts']+=human==actual
    current['type_set_equal']+=set(human)==set(actual)
    current['exact_actor_tags']+=set(inputs['tags'][i] for i in prediction['actors'])==set(command.units)
    counts['commands']+=1
result=dict(categories={k:dict(v) for k,v in categories.items()},scope='Corrected trainer.collect inputs including construction products; supersedes omitted-feature helper05. Diagnostic human actor types/counts; no legality or strength claim',rl_updates=0)
Path('logs/roadmap/joint-professional-actor-roles-05-corrected.json').write_text(json.dumps(result,indent=2)+'\n')
print(result)
