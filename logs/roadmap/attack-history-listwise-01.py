"""Fixed actor-linked prior-destination supervised experiment."""
import ast
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from src.learning.imitation import FactorPolicy

root = Path('logs/roadmap')
out = root/'attack-history-listwise-01'
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
files += [root/'spatial-prefix-240-01/report.json',root/'attack-point-scorer-01/report.json',
 root/'attack-history-persistence-01.json',root/'attack-history-persistence-01.py',
 root/'attack-listwise-corpus-01/report.json',root/'attack-listwise-corpus-01/points.npz']
files += [Path('src/learning')/(n+'.py') for n in ('global_imitation','imitation','actor_selection','teacher_states','gameplay')]
files += [d/n for d in train+validation for n in ('dataset.json','static.json','examples.jsonl.gz')]
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
bindings=hashes()
contract={'scope':'Attack point component, human ability/group/mode supplied; all validation games reused diagnostic, no live policy',
    'selection':'all Attack point commands in the same six teaching games as the binary baseline',
    'commands':365,'epochs':100,'seed':5010,'hidden':32,'rate':.001,
    'objective':'categorical cross entropy over every two-tile map candidate for each command',
    'gate':'each diagnostic game changed-destination within-two accuracy at least 10pp higher than frozen no-history scorer AND all-command accuracy exceeds both no-history and persistence by at least 10pp',
    'stop':'one fixed fit, no sweep or live promotion; component results never establish full-command competence',
    'comparability':'same commands, grid,32hidden,seed,epochs,command weighting as categorical baseline; new six history features change normalization and initialization; no isolated causal claim',
    'history':'latest strictly earlier-loop Attack point sharing any selected actor, teacher-forced; six features: candidate-relative x/y,distance,availability,log age,actor overlap; categories used only for evaluation',
    'deployment_limit':'future live history must come from own issued commands; teacher-forced diagnostic is not closed-loop competence',
    'weighting':'one update per command per epoch, uniform commands',
    'files_before':bindings}
(out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')

history_report=json.loads((root/'attack-history-persistence-01.json').read_text())
history_by_game={g['dataset']:g['predictions'] for g in history_report['games']}
def history_rows(directory):
    records=history_by_game[str(directory)]
    count=0
    for values in namespace['rows'](directory):
        state,group,origin,context,terrain,truth,command=values
        record=records[count];count+=1
        assert record['loop']>state['game_loop']
        assert record['units']==command['units'] and np.array_equal(record['teacher_point'],truth)
        previous=record['previous']
        if previous is not None:assert previous['loop']<=state['game_loop']
        yield values,record
    assert count==len(records)
def history_features(state,group,origin,context,points,terrain,record):
    raw=namespace['features'](state,group,origin,context,points,terrain)
    extra=np.zeros((len(points),6),dtype=np.float32)
    previous=record['previous']
    if previous is not None:
        delta=(points-np.asarray(previous['teacher_point']))*namespace['coordinate_signs'](state,origin)/128
        extra[:,:2]=delta;extra[:,2]=np.linalg.norm(delta,axis=1)
        extra[:,3]=1;extra[:,4]=np.log1p((state['game_loop']-previous['loop'])/22.4)/5
        extra[:,5]=len(set(previous['units']) & {u['tag'] for u in group})/len(group)
    return np.concatenate((raw,extra),axis=1)

start=time.monotonic();examples=[]
for i,d in enumerate(train):
    for (state,group,origin,context,terrain,truth,command),record in history_rows(d):
        points=namespace['spatial_candidates'](state['map_size'],0,spacing=2)
        fx=history_features(state,group,origin,context,points,terrain,record)
        positive=int(np.linalg.norm(points-truth,axis=1).argmin())
        examples.append({'x':fx,'points':points,'truth':truth,'positive':positive,'dataset':str(d),'loop':state['game_loop'],'history_record':record})
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
baseline=np.load(root/'attack-listwise-corpus-01/points.npz')
def frozen_logits(raw):
    return np.tanh(((raw[:,:-6]-baseline['mean'])/baseline['scale'])@baseline['input']+baseline['bias'])@baseline['output']
results=[]
for e in examples:
    index=int((np.tanh(e['x']@w+b)@v).argmax())
    old=int(frozen_logits(e['x']*scale+mean).argmax())
    results.append({'dataset':e['dataset'],'loop':e['loop'],
        'teacher_point':e['truth'].tolist(),'chosen_point':e['points'][index].tolist(),
        'error_tiles':float(np.linalg.norm(e['points'][index]-e['truth'])),
        'baseline_error_tiles':float(np.linalg.norm(e['points'][old]-e['truth']))})
assert hashes()==bindings
count=sum(r['error_tiles']<=2 for r in results)
diagnostics=[]
for d in validation:
    predictions=[]
    for (state,group,origin,context,terrain,truth,command),record in history_rows(d):
        points=namespace['spatial_candidates'](state['map_size'],0,spacing=2)
        raw=history_features(state,group,origin,context,points,terrain,record)
        logits=np.tanh(((raw-mean)/scale)@w+b)@v
        old_logits=frozen_logits(raw)
        index=int(logits.argmax());old=int(old_logits.argmax())
        predictions.append({'loop':state['game_loop'],'teacher_point':truth.tolist(),
          'chosen_point':points[index].tolist(),'error_tiles':float(np.linalg.norm(points[index]-truth)),
          'baseline_error_tiles':float(np.linalg.norm(points[old]-truth)),
          'category':record['category'],'persistence_error_tiles':record['error_tiles'],
          'history_record':record})
    def stats(key,category=None):
        chosen=[r for r in predictions if category is None or r['category']==category]
        errors=np.asarray([r[key] if r[key] is not None else float('inf') for r in chosen])
        return {'commands':len(errors),'within_2_accuracy':float(np.mean(errors<=2)),
                'within_2_tiles':int((errors<=2).sum()),'mean_error_tiles':float(errors.mean())}
    diagnostics.append({'dataset':str(d),'new':stats('error_tiles'),'baseline':stats('baseline_error_tiles'),'predictions':predictions,
      'persistence':stats('persistence_error_tiles'),
      'categories':{c:{'new':stats('error_tiles',c),'baseline':stats('baseline_error_tiles',c),'persistence':stats('persistence_error_tiles',c)} for c in ('same','changed','first')}})
assert hashes()==bindings
passed=all(r['categories']['changed']['new']['within_2_accuracy']>=r['categories']['changed']['baseline']['within_2_accuracy']+.1 and r['new']['within_2_accuracy']>=max(r['baseline']['within_2_accuracy'],r['persistence']['within_2_accuracy'])+.1 for r in diagnostics)
report=dict(contract,status='completed',within_2_tiles=count,gate_passed=passed,diagnostics=diagnostics,
    mean_error_tiles=float(np.mean([r['error_tiles'] for r in results])),
    baseline_within_2_tiles=sum(r['baseline_error_tiles']<=2 for r in results),
    baseline_mean_error_tiles=float(np.mean([r['baseline_error_tiles'] for r in results])),
    predictions=results,files_after=hashes(),wall_seconds=time.monotonic()-start)
np.savez_compressed(out/'points.npz',input=w,bias=b,output=v,mean=mean,scale=scale)
report['checkpoint_sha256']=hashlib.sha256((out/'points.npz').read_bytes()).hexdigest()
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('predictions','files_before','files_after','diagnostics')}),flush=True)
