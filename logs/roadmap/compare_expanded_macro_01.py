"""Frozen same-cohort macro comparison; no fit, native game or fresh holdout."""
import hashlib,json,time
from pathlib import Path
import numpy as np
from src.learning.imitation import FactorPolicy
from src.learning.imitation_train import dataset,metrics
ROOT=Path('logs/roadmap');OUT=ROOT/'expanded-macro-comparison-01';OUT.mkdir(exist_ok=False)
oldpath=ROOT/'consistent-fullgame-02/macro/policy.npz';newpath=ROOT/'expanded-human-macro-01/macro/policy.npz'
old=FactorPolicy.load(oldpath);new=FactorPolicy.load(newpath)
assert old.unit_types==new.unit_types and old.sizes==new.sizes
paths=[ROOT/'issued-timing-masked-01'/f'issued-{n}' for n in (51574,51573,51958,51890,51891)]
paths += [ROOT/f'issued-{n}-expansion-0{2 if n==51754 else 1}' for n in (51572,51685,51885,51754)]
files=[Path(__file__),oldpath,newpath,*[Path('src/learning')/(name+'.py') for name in ('imitation','imitation_train','global_imitation','teacher_states','gameplay')],*[d/name for d in paths for name in ('dataset.json','static.json','examples.jsonl.gz')]]
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=hashes();start=time.monotonic()
x,y,points,weights,sources,audit=dataset(paths,new.unit_types,4000,'global',new.sizes['ability'],10000,False,0)
assert len(x)==3543 and audit['replay_ranges'][4][1]==1999
result={}
for label,sl in (('old_five',slice(0,1999)),('added_four',slice(1999,None)),('all_nine',slice(None))):
    result[label]={name:metrics(policy,x[sl],{k:v[sl] for k,v in y.items()},points[sl]) for name,policy in (('baseline',old),('expanded',new))}
assert abs(result['old_five']['baseline']['commanded_ability_accuracy']-0.9684842421210605)<1e-9
assert abs(result['all_nine']['expanded']['commanded_ability_accuracy']-0.9356477561388654)<1e-9
assert hashes()==before
report={'status':'completed','scope':'same-cohort conditional macro heads only; prior human command history and event times; not full commanded actor/target fidelity or native gameplay',
        'files_before':before,'files_after':hashes(),'results':result,'no_fit':True,'no_native':True,'fresh51483_states_not_loaded':True,'reserved51886_not_used':True,'wall_seconds':time.monotonic()-start}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'completed','ability':{label:{name:row['commanded_ability_accuracy'] for name,row in data.items()} for label,data in result.items()},'wall_seconds':report['wall_seconds']}))
