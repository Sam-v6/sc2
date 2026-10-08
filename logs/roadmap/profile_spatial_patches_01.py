import json
from pathlib import Path
import time
import numpy as np
from src.learning.entity_examples import state_inputs
from src.learning.entity_spatial import spatial_features
from src.learning.teacher_states import teacher_states
from src.learning.entity_train import digest
root=Path.cwd();c=json.loads((root/'logs/roadmap/joint-entity-fit-04/configuration.json').read_text())
results=[];estimate=0
for source in c['sources']:
 if source['role']!='teaching': continue
 directory=Path(source['dataset']); static=json.loads((directory/'static.json').read_text())
 row,state=next(teacher_states(directory));inputs=state_inputs(state,*c['vocabulary'][:2],upgrade_count=c['vocabulary'][2])
 start=time.perf_counter();features=spatial_features(state,static['terrain'],inputs['world_points'],inputs['point_radii']); conversion=time.perf_counter()-start
 receipt=json.loads((directory/'dataset.json').read_text());commands=receipt['issued_command_audit']['matched_issued_commands'];estimate+=features.nbytes*commands
 rng=np.random.default_rng(1);weights=rng.normal(size=(features.shape[1],32)).astype(np.float32);gradient=rng.normal(size=(len(features),32)).astype(np.float32)
 start=time.perf_counter()
 for _ in range(100):
  encoded=np.tanh(features@weights)
  backward=features.T@(gradient*(1-encoded**2))
 elapsed=time.perf_counter()-start
 results.append(dict(dataset=str(directory),cells=len(features),shape=list(features.shape),feature_bytes=features.nbytes,commands=commands,conversion_seconds=conversion,embedding_forward_and_weight_gradient_seconds_per_call=elapsed/100))
 for p,sha in source['bindings'].items():assert digest(Path(p))==sha
report=dict(status='profiled',results=results,estimated_all_teaching_spatial_feature_bytes=estimate,scope='First observation per game; static map dimensions give command-scaled feature-payload estimate, not RSS. Isolated float32 32-wide spatial matrix/tanh and weight-gradient timing, not complete policy or native throughput. CPU-only two BLAS threads; no training changes.')
(root/'logs/roadmap/spatial-patch-profile-01.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
