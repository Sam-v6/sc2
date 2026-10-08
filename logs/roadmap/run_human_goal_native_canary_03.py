"""One frozen-model native engineering canary, CPU guarded; no RL."""
import hashlib,json,threading,time
from pathlib import Path
import psutil
from src.learning.production_goal_play import play_production_goals
from src.runtime import supervise

ROOT=Path('logs/roadmap'); OUT=ROOT/'human-goal-native-03'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    OUT.mkdir(exist_ok=True)
    parity=json.loads((ROOT/'human-production-goals-02/feature-parity.json').read_text())
    verify=json.loads((ROOT/'human-production-goals-02/verification.json').read_text())
    assert parity['status']==verify['status']=='verified'
    for receipt in (parity,verify):
        for p,h in receipt['bindings'].items():assert sha(p)==h,p
    model=ROOT/'human-production-goals-02/model.pkl'
    assert sha(model)=='bba44d92c8bf2c5c62b5f529ca0078e1fa4daa7c3e2db2fc59697d4c0b423282'
    job=dict(model=str(model.resolve()),profile=str((ROOT/'professional-observation-profile-01.json').resolve()),
             vocabulary=json.loads((ROOT/'joint-professional-fit-05/configuration.json').read_text())['vocabulary'],
             map='AcropolisLE',race='Zerg',difficulty='VeryEasy',build='Macro',seed=816003,
             seconds=240,output=str((OUT/'canary').resolve()))
    assert not Path(job['output']).exists()
    bindings={str(p):sha(p) for p in [Path(__file__),Path('docs/superpowers/plans/2026-10-06-human-primitives-imitation.md'),Path(job['profile'])]+list(Path('src/learning').glob('production_*.py'))+[Path('src/bots/terran_primitives.py')]}
    stop=threading.Event();done=threading.Event();samples=[]
    def watch():
        high=0
        while not done.is_set():
            cpu=psutil.cpu_percent(interval=1);samples.append(dict(time=time.time(),cpu=cpu));high=high+1 if cpu>80 else 0
            if high>=3:stop.set()
            done.wait(4)
    baseline=psutil.cpu_percent(interval=1)
    assert baseline<70,('Insufficient CPU headroom',baseline)
    watcher=threading.Thread(target=watch,daemon=True);watcher.start()
    result=supervise(play_production_goals,(job,),180,stop_event=stop)
    done.set();watcher.join(5)
    for p,h in bindings.items():assert sha(p)==h,p
    report=dict(result=result,bindings=bindings,baseline_cpu=baseline,peak_cpu=max([baseline]+[s['cpu'] for s in samples]),samples=samples,rl=False)
    (OUT/'canary.supervision.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],result=result.get('result'),error=result.get('error'),wall_seconds=result['wall_seconds'],peak_cpu=report['peak_cpu'])),flush=True)
if __name__=='__main__':main()
