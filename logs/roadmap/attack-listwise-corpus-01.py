"""Fixed all-teaching-command categorical location experiment."""
import ast
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from src.learning.imitation import FactorPolicy

root = Path('logs/roadmap')
out = root/'attack-listwise-corpus-01'
out.mkdir(exist_ok=False)
original = root/'attack-point-scorer-01.py'
# Reuse exactly the completed experiment's fog-safe feature and row functions.
tree = ast.parse(original.read_text())
selected = [n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))]
namespace = {'root':root}
exec(compile(ast.Module(body=selected,type_ignores=[]),str(original),'exec'),namespace)
namespace.update(macro=FactorPolicy.load(root/'imitation-prefix-240-01/policy.npz'),
    structures=json.loads((root/'spatial-prefix-240-01/report.json').read_text())['structure_types'],
    vocab=json.loads((root/'attack-point-scorer-01/report.json').read_text())['selected_type_vocabulary'])
train=[root/f'issued-{i}' for i in (51574,51573,51958,51890,51891)]+[root/'issued-51957-p1']
files=[Path(__file__),original,Path('src/learning/spatial_construction.py'),root/'imitation-prefix-240-01/policy.npz',root/'attack-point-scorer-01/points.npz']
validation=[root/'issued-50925',root/'issued-51960-p1',root/'issued-51959-held-01']
files += [root/'spatial-prefix-240-01/report.json',root/'attack-point-scorer-01/report.json']
files += [Path('src/learning')/(n+'.py') for n in ('global_imitation','imitation','actor_selection','teacher_states','gameplay')]
files += [d/n for d in train+validation for n in ('dataset.json','static.json','examples.jsonl.gz')]
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
bindings=hashes()
contract={'scope':'Attack point component, human ability/group/mode supplied; all validation games reused diagnostic, no live policy',
    'selection':'all Attack point commands in the same six teaching games as the binary baseline',
    'commands':365,'epochs':100,'seed':5010,'hidden':32,'rate':.001,
    'objective':'categorical cross entropy over every two-tile map candidate for each command',
    'gate':'training within-two accuracy at least 90 percent AND each diagnostic game at least 30 percent accuracy, at least 10pp higher than binary baseline and at least 10 percent lower mean error',
    'stop':'one fixed fit, no sweep or live promotion; component results never establish full-command competence',
    'comparability':'same teaching commands and hidden width; normalization, objective, update count and replay weighting differ; no objective-only causal claim',
    'weighting':'one update per command per epoch, uniform commands, unlike equal-replay binary baseline',
    'files_before':bindings}
(out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
start=time.monotonic();examples=[]
for i,d in enumerate(train):
    for j,(state,group,origin,context,terrain,truth,command) in enumerate(namespace['rows'](d)):
        points=namespace['spatial_candidates'](state['map_size'],0,spacing=2)
        fx=namespace['features'](state,group,origin,context,points,terrain)
        positive=int(np.linalg.norm(points-truth,axis=1).argmin())
        examples.append({'x':fx,'points':points,'truth':truth,'positive':positive,'dataset':str(d),'loop':state['game_loop']})
assert len(examples)==365
allx=np.concatenate([e['x'] for e in examples]);mean=allx.mean(0);scale=np.maximum(allx.std(0),.1)
for e in examples:e['x']=(e['x']-mean)/scale
rng=np.random.default_rng(5010)
w=rng.normal(0,1/np.sqrt(allx.shape[1]),(allx.shape[1],32)).astype('f')
b=np.zeros(32,dtype='f');v=rng.normal(0,.01,32).astype('f')
params=[w,b,v];m=[np.zeros_like(p) for p in params];variance=[np.zeros_like(p) for p in params];step=0
del allx
for epoch in range(100):
    loss=0
    for index in rng.permutation(len(examples)):
        e=examples[index];x=e['x'];hidden=np.tanh(x@w+b);logits=hidden@v
        probability=np.exp(logits-logits.max());probability/=probability.sum()
        loss-=np.log(max(float(probability[e['positive']]),1e-30))
        probability[e['positive']]-=1
        back=(probability[:,None]*v)*(1-hidden*hidden)
        gradients=[x.T@back,back.sum(0),hidden.T@probability];step+=1
        for k,(p,g) in enumerate(zip(params,gradients)):
            m[k]*=.9;m[k]+=.1*g;variance[k]*=.999;variance[k]+=.001*g*g
            p-=.001*(m[k]/(1-.9**step))/(np.sqrt(variance[k]/(1-.999**step))+1e-8)
    if epoch%20==0:print(json.dumps({'epoch':epoch,'mean_loss':loss/len(examples),'wall_seconds':time.monotonic()-start}),flush=True)
baseline=FactorPolicy.load(root/'attack-point-scorer-01/points.npz')
results=[]
for e in examples:
    index=int((np.tanh(e['x']@w+b)@v).argmax())
    logits=baseline.predict(e['x']*scale+mean)['ability'];old=int((logits[:,1]-logits[:,0]).argmax())
    results.append({'dataset':e['dataset'],'loop':e['loop'],
        'teacher_point':e['truth'].tolist(),'chosen_point':e['points'][index].tolist(),
        'error_tiles':float(np.linalg.norm(e['points'][index]-e['truth'])),
        'baseline_error_tiles':float(np.linalg.norm(e['points'][old]-e['truth']))})
assert hashes()==bindings
count=sum(r['error_tiles']<=2 for r in results)
diagnostics=[]
for d in validation:
    predictions=[]
    for state,group,origin,context,terrain,truth,command in namespace['rows'](d):
        points=namespace['spatial_candidates'](state['map_size'],0,spacing=2)
        raw=namespace['features'](state,group,origin,context,points,terrain)
        logits=np.tanh(((raw-mean)/scale)@w+b)@v
        old_logits=baseline.predict(raw)['ability']
        index=int(logits.argmax());old=int((old_logits[:,1]-old_logits[:,0]).argmax())
        predictions.append({'loop':state['game_loop'],'teacher_point':truth.tolist(),
          'chosen_point':points[index].tolist(),'error_tiles':float(np.linalg.norm(points[index]-truth)),
          'baseline_error_tiles':float(np.linalg.norm(points[old]-truth))})
    def stats(key):
        errors=np.asarray([r[key] for r in predictions])
        return {'commands':len(errors),'within_2_accuracy':float(np.mean(errors<=2)),
                'within_2_tiles':int((errors<=2).sum()),'mean_error_tiles':float(errors.mean())}
    diagnostics.append({'dataset':str(d),'new':stats('error_tiles'),'baseline':stats('baseline_error_tiles'),'predictions':predictions})
assert hashes()==bindings
passed=count/len(examples)>=.9 and all(r['new']['within_2_accuracy']>=max(.3,r['baseline']['within_2_accuracy']+.1) and r['new']['mean_error_tiles']<=.9*r['baseline']['mean_error_tiles'] for r in diagnostics)
report=dict(contract,status='completed',within_2_tiles=count,gate_passed=passed,diagnostics=diagnostics,
    mean_error_tiles=float(np.mean([r['error_tiles'] for r in results])),
    baseline_within_2_tiles=sum(r['baseline_error_tiles']<=2 for r in results),
    baseline_mean_error_tiles=float(np.mean([r['baseline_error_tiles'] for r in results])),
    predictions=results,files_after=hashes(),wall_seconds=time.monotonic()-start)
np.savez_compressed(out/'points.npz',input=w,bias=b,output=v,mean=mean,scale=scale)
report['checkpoint_sha256']=hashlib.sha256((out/'points.npz').read_bytes()).hexdigest()
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('predictions','files_before','files_after','diagnostics')}),flush=True)
