"""Frozen six-game assisted human-imitation development panel; no RL."""
import hashlib,json,threading,time
from pathlib import Path
import psutil
from src.learning.production_goal_play import play_production_goals
from src.runtime import supervise
ROOT=Path('logs/roadmap');OUT=ROOT/'human-goal-native-01/panel'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    proof=json.loads((ROOT/'human-goal-native-01/canary-verification.json').read_text());assert proof['status']=='verified_engineering'
    for p,h in proof['bindings'].items():assert sha(p)==h,p
    verify=json.loads((ROOT/'human-production-goals-01/verification.json').read_text())
    for p,h in verify['bindings'].items():assert sha(p)==h,p
    OUT.mkdir(exist_ok=False)
    vocab=json.loads((ROOT/'joint-professional-fit-05/configuration.json').read_text())['vocabulary']
    jobs=[dict(model=str((ROOT/'human-production-goals-01/model.pkl').resolve()),profile=str((ROOT/'professional-observation-profile-01.json').resolve()),vocabulary=vocab,map='AcropolisLE',race=race,difficulty='Hard',build=build,seed=816001+i,seconds=600,output=str((OUT/f'{i+1}-{race}-{build}').resolve())) for i,(race,build) in enumerate([(r,b) for r in ('Terran','Zerg','Protoss') for b in ('Rush','Macro')])]
    paths=[Path(__file__),Path('docs/superpowers/plans/2026-10-06-human-production-goals-native.md'),ROOT/'professional-observation-profile-01.json',ROOT/'human-production-goals-01/model.pkl']+list(Path('src/learning').glob('production_*.py'))
    bindings={str(p):sha(p) for p in paths}
    (OUT/'contract.json').write_text(json.dumps(dict(jobs=jobs,bindings=bindings,rl=False,wall_per_game=240,whole_host_cpu_limit=80),indent=2)+'\n')
    stop=threading.Event();done=threading.Event();samples=[]
    def watch():
        high=0
        while not done.is_set():
            cpu=psutil.cpu_percent(interval=1);samples.append(dict(time=time.time(),cpu=cpu));high=high+1 if cpu>80 else 0
            if high>=3:stop.set()
            done.wait(4)
    baseline=psutil.cpu_percent(interval=1);assert baseline<70,('No CPU headroom',baseline)
    watcher=threading.Thread(target=watch,daemon=True);watcher.start();results=[]
    try:
        for job in jobs:
            if stop.is_set():break
            result=supervise(play_production_goals,(job,),240,stop_event=stop);results.append(result)
            (OUT/'progress.json').write_text(json.dumps(dict(results=results,samples=samples,rl=False),indent=2)+'\n')
            print(json.dumps(dict(game=len(results),race=job['race'],build=job['build'],status=result['status'],result=result.get('result'),error=result.get('error'),wall_seconds=result['wall_seconds'],acknowledged=result.get('acknowledged',{}))),flush=True)
            if result['status'] not in ('completed','truncated'):break
    finally:
        done.set();watcher.join(5)
    for p,h in bindings.items():assert sha(p)==h,p
    report=dict(status='completed' if len(results)==6 and all(r['status'] in ('completed','truncated') for r in results) else 'stopped',results=results,samples=samples,peak_cpu=max([baseline]+[s['cpu'] for s in samples]),rl=False,bindings=bindings)
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(panel_status=report['status'],games=len(results),peak_cpu=report['peak_cpu'])),flush=True)
if __name__=='__main__':main()
