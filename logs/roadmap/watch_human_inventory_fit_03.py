import json,threading,time
from pathlib import Path
import psutil
from src.runtime import supervise
from fit_human_inventory_03 import main as fit

def main():
    out=Path('logs/roadmap/human-inventory-targets-03');stop=threading.Event();done=threading.Event();samples=[]
    baseline=psutil.cpu_percent(interval=1);assert baseline<70,baseline
    def watch():
        high=0
        while not done.is_set():
            cpu=psutil.cpu_percent(interval=1);samples.append(dict(time=time.time(),cpu=cpu));high=high+1 if cpu>80 else 0
            if high>=3:stop.set()
            done.wait(4)
    watcher=threading.Thread(target=watch,daemon=True);watcher.start()
    result=supervise(fit,(),600,stop_event=stop)
    done.set();watcher.join(5)
    report=dict(result=result,baseline_cpu=baseline,peak_cpu=max([baseline]+[s['cpu'] for s in samples]),samples=samples,rl=False)
    (out/'fit-supervision.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],error=result.get('error'),wall_seconds=result['wall_seconds'],peak_cpu=report['peak_cpu'])),flush=True)
if __name__=='__main__':main()
