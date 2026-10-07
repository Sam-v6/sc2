"""Fixed whole-game human target teaching; diagnostic opponents, no RL."""
import hashlib,json,time
from pathlib import Path
import numpy as np
from src.learning.imitation import FactorPolicy
from src.learning.target_selection import TargetPolicy,target_features
from src.learning.global_imitation import global_features
from src.learning.teacher_states import teacher_states,own_actors
root=Path('logs/roadmap');out=root/'target-listwise-human-02';out.mkdir(exist_ok=False)
train=[51574,51573,51958,51890,51891];held=[50925,51960,51482]
dirs={i:root/'issued-timing-masked-01'/f'issued-{i}' for i in train+held if i!=51482};dirs[51482]=root/'issued-51482-rom-masked-01';dirs[51960]=root/'issued-timing-masked-01/issued-51960-p1'
macro_path=root/'imitation-prefix-240-01/policy.npz';baseline_path=root/'target-human-fit-01/targets.npz'
macro=FactorPolicy.load(macro_path);baseline=FactorPolicy.load(baseline_path)
files=[Path(__file__),macro_path,baseline_path,root/'target-human-fit-01/report.json',*sorted(Path('src/learning').glob('*.py'))]
files += [p/name for p in dirs.values() for name in ('dataset.json','static.json','examples.jsonl.gz')]
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=hashes();contract={'train':train,'reused_diagnostics':held,'reserved_51886_unused':True,'epochs':150,'seed':5004,'batch_commands':16,'rate':.001,'objective':'softmax over all visible unit candidates per command, inverse replay command count weights, normalized within each minibatch','gate':'training >=90% exact and each diagnostic >=10 percentage points above frozen binary pointer, with no lower enemy-Attack exact rate; diagnostic only, no live promotion','scope':'teacher ability and group supplied, unit-target commands only; no autonomous strength claim','files_before':before}
(out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
def collect(replay):
    directory=dirs[replay];receipt=json.loads((directory/'dataset.json').read_text());assert receipt['status']=='completed'
    samples=[];missing=0
    for row,state in teacher_states(directory):
        actors={u['tag']:u for u in own_actors(state)}
        _,origin=global_features(state,macro.unit_types,macro.sizes['ability'],canonical=True,summarize=True)
        for command in row['commands']:
            if command['target_unit'] is None or command['autocast']:continue
            group=[actors[tag] for tag in command['units']]
            units,x=target_features(state,group,command['ability'],macro.unit_types,macro.sizes['ability'],origin)
            tags=[u['tag'] for u in units]
            if command['target_unit'] not in tags:missing+=1;continue
            truth=tags.index(command['target_unit']);positions=np.array([u['position'][:2] for u in units]);center=np.array([u['position'][:2] for u in group]).mean(axis=0)
            samples.append({'x':x,'target':truth,'loop':row['action_loop'],'tags':tags,'positions':positions,'nearest':int(np.linalg.norm(positions-center,axis=1).argmin()),'attack_enemy':command['ability']==23 and units[truth]['alliance']==4,'replay':replay,'ability':command['ability']})
    return samples,receipt['sha256'],missing
start=time.monotonic();data={i:collect(i) for i in dirs};assert not ({data[i][1] for i in train}&{data[i][1] for i in held})
samples=[s for i in train for s in data[i][0]];x=np.concatenate([s['x'] for s in samples])
policy=TargetPolicy(x.shape[1],2,[],seed=5004);policy.feature_mean=x.mean(axis=0);policy.feature_scale=np.maximum(x.std(axis=0),.1)
active=np.flatnonzero(np.any(x!=policy.feature_mean,axis=0));del x
for i in dirs:
    for s in data[i][0]:s['compressed']=s['x'][:,active]
rng=np.random.default_rng(5004)
for epoch in range(150):
    order=rng.permutation(len(samples))
    for begin in range(0,len(order),16):
        batch=[samples[j] for j in order[begin:begin+16]];lengths=[len(s['x']) for s in batch];ends=np.cumsum(lengths);starts=np.r_[0,ends[:-1]]
        labels={'ranges':list(zip(starts,ends)),'target':[s['target'] for s in batch]}
        weights=np.array([1/len(data[s['replay']][0]) for s in batch])
        policy.learn(np.concatenate([s['compressed'] for s in batch]),labels,None,weights=weights,feature_indices=active)
    if epoch%25==0:print(json.dumps({'epoch':epoch,'wall_seconds':time.monotonic()-start}),flush=True)
def audit(replay):
    records=[]
    for s in data[replay][0]:
        score=policy.predict(s['compressed'],feature_indices=active)['ability'];old=baseline.predict(s['x'])['ability']
        choices={'listwise':int((score[:,1]-score[:,0]).argmax()),'binary':int((old[:,1]-old[:,0]).argmax()),'nearest':s['nearest']}
        records.append({'loop':s['loop'],'ability':s['ability'],'target':s['tags'][s['target']],'attack_enemy':s['attack_enemy'],'choices':{name:{'tag':s['tags'][choice],'exact':choice==s['target'],'error_tiles':float(np.linalg.norm(s['positions'][choice]-s['positions'][s['target']]))} for name,choice in choices.items()}})
    metrics={}
    for stratum in ('all','attack_enemy'):
        selected=[r for r in records if stratum=='all' or r['attack_enemy']]
        metrics[stratum]={'commands':len(selected),'models':{name:{'exact':sum(r['choices'][name]['exact'] for r in selected),'accuracy':float(np.mean([r['choices'][name]['exact'] for r in selected])) if selected else None,'mean_error_tiles':float(np.mean([r['choices'][name]['error_tiles'] for r in selected])) if selected else None} for name in ('listwise','binary','nearest')}}
    return {'source_sha256':data[replay][1],'unavailable_targets':data[replay][2],'metrics':metrics,'records':records}
results={str(i):audit(i) for i in dirs};hits=sum(results[str(i)]['metrics']['all']['models']['listwise']['exact'] for i in train);count=len(samples)
gate=hits/count>=.9
for i in held:
    m=results[str(i)]['metrics'];a=m['all']['models'];gate &= a['listwise']['accuracy']>=a['binary']['accuracy']+.10
    if m['attack_enemy']['commands']:
        a=m['attack_enemy']['models'];gate &= a['listwise']['accuracy']>=a['binary']['accuracy']
assert hashes()==before
report=dict(contract,status='completed',training_commands=count,training_exact=hits,training_accuracy=hits/count,results=results,gate_passed=bool(gate),wall_seconds=time.monotonic()-start,files_after=hashes())
policy.save(out/'targets.npz',{'scope':contract['scope'],'training_objective':'command_candidate_softmax','train_sources':[data[i][1] for i in train],'unit_types':macro.unit_types,'ability_count':macro.sizes['ability'],'gate_passed':bool(gate)})
report['checkpoint_sha256']=hashlib.sha256((out/'targets.npz').read_bytes()).hexdigest();(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('results','files_before','files_after')},indent=2),flush=True)
print(json.dumps({i:r['metrics'] for i,r in results.items()},indent=2),flush=True)
