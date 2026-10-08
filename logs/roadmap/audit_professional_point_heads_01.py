import argparse,json,hashlib
from pathlib import Path
import numpy as np
from src.learning.entity_policy import JointEntityPolicy
from src.learning.entity_examples import replay_examples
from src.learning.entity_train import DELAYS
parser=argparse.ArgumentParser();parser.add_argument('checkpoint',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
policy,_=JointEntityPolicy.load(args.checkpoint)
errors={'ordinary':[],'ability_actor_oracle':[]};mode_correct={k:0 for k in errors}
for inputs,label,command,reason in replay_examples(Path('logs/roadmap/pro-demonstrations-05/774'),1970,3801,296,DELAYS,spatial=True,missing_fields=True):
    if label is None or label['mode']!=2: continue
    for name in errors:
        conditioning={} if name=='ordinary' else dict(ability=label['ability'],actors=label['actors'])
        scores,cache=policy._forward(inputs,**conditioning)
        index=int(np.argmax(scores['point']))
        point=inputs['world_points'][index]+scores['offset']*inputs['point_radii'][index]
        errors[name].append(float(np.linalg.norm(point-np.asarray(command.target_point))))
        mode_correct[name]+=int(np.argmax(scores['mode'])==2)
result={'scope':'All gold point-command rows, including mode failures; point head read independently of predicted mode. Reused diagnostic, no games/learning.',
        'checkpoint_sha256':hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),
        'diagnostic_corpus_sha256':hashlib.sha256(Path('logs/roadmap/pro-demonstrations-05/774/examples.jsonl.gz').read_bytes()).hexdigest(),
        'helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'errors':{k:{'commands':len(v),'mean_tiles':float(np.mean(v)),'p95_tiles':float(np.percentile(v,95)),
                     'within_two_tiles':sum(e<=2 for e in v),'mode_correct':mode_correct[k]} for k,v in errors.items()}}
args.output.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
