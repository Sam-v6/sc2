"""One fixed human-only macro fit; no actor/argument mixing or native play."""
import gzip,hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path.cwd();BASE=ROOT/'logs/roadmap';OUT=BASE/'expanded-human-macro-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    OUT.mkdir(exist_ok=False)
    datasets=[BASE/'issued-timing-masked-01'/f'issued-{n}' for n in (51574,51573,51958,51890,51891)]
    datasets += [BASE/f'issued-{n}-expansion-0{2 if n==51754 else 1}' for n in (51572,51685,51885,51754)]
    validation=BASE/'issued-timing-masked-01/issued-50925'
    files=[Path(__file__),ROOT/'src/runner.py',ROOT/'src/path.py',ROOT/'src/runtime.py',*[ROOT/f'src/learning/{name}.py' for name in ('imitation_train','imitation','global_imitation','teacher_states','gameplay')],*[d/name for d in datasets+[validation] for name in ('dataset.json','static.json','examples.jsonl.gz')],BASE/'human-corpus-expansion-01/integrity-audit-completed4-01.json',BASE/'human-replays/51483.SC2Replay',BASE/'consistent-fullgame-02/macro/report.json']
    before={str(p):sha(p) for p in files};inventory=[]
    for d in datasets:
        receipt=json.loads((d/'dataset.json').read_text());assert receipt['status']=='completed'
        with gzip.open(d/'examples.jsonl.gz','rt') as f:commands=sum(len(r['commands']) for r in map(json.loads,f))
        inventory.append({'dataset':str(d),'sha256':receipt['sha256'],'commands':commands,'role':'teaching','professional':False})
    assert sum(i['commands'] for i in inventory)==3543
    assert len({i['sha256'] for i in inventory})==9
    fresh_sha=sha(BASE/'human-replays/51483.SC2Replay');assert fresh_sha not in {i['sha256'] for i in inventory}
    args=[str((ROOT/'.venv/bin/python').absolute()),'-m','src.learning.imitation_train','--train',*map(str,datasets),'--validation',str(validation),'--output',str(OUT/'macro'),'--epochs','600','--seed','4000','--decision-level','global','--balance-abilities','--prefix-seconds','10000']
    contract={'scope':'One expanded whole-game supervised macro fit, same settings as consistent-fullgame-02; no RL, native play, complete-policy or professional claim',
              'train_inventory':inventory,'validation_role':'Reused Lyra diagnostic; not fresh or unbiased final acceptance',
              'role_change_before_fit':{'51483':{'previous':'candidate_teaching','new':'reserved_fresh_expansion_validation','sha256':fresh_sha,'reason':'Last pending full game reserved before any fit or model predictions; not a randomized benchmark'}},
              'reserved51886_not_used':True,'fresh51483_states_not_loaded':True,'epochs':600,'seed':4000,'wall_bound_seconds':900,'cpu':'CPU-only, two BLAS threads','command':args,'files_before':before}
    (OUT/'contract.json').write_text(json.dumps(contract,indent=2)+'\n');print(json.dumps({'status':'starting','commands':3543,'games':9,'limit':900}),flush=True)
    start=time.monotonic()
    with (OUT/'console.log').open('w') as f:run=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,OPENBLAS_NUM_THREADS='2',PYTHONPATH='.'),timeout=900)
    after={str(p):sha(p) for p in files};report={'exit_code':run.returncode,'files_after':after,'sources_unchanged':before==after,'wall_seconds':time.monotonic()-start}
    if run.returncode==0:
        trained=json.loads((OUT/'macro/report.json').read_text());report['training_report']=trained;report['checkpoint_sha256']=sha(OUT/'macro/policy.npz')
        assert {s['replay_sha256'] for s in trained['train_sources']}=={i['sha256'] for i in inventory}
        assert all(s['replay_sha256']!=fresh_sha for role in ('train_sources','validation_sources') for s in trained[role])
    report['status']='completed' if run.returncode==0 and before==after else 'incomplete'
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('files_after','training_report')}),flush=True)
if __name__=='__main__':main()
