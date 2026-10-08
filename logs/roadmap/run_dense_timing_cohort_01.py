"""Frozen existing human splits, sequential native reconstruction, CPU guard."""
import hashlib,json,os,signal,subprocess,time
from pathlib import Path
import psutil
ROOT=Path('logs/roadmap');OUT=ROOT/'dense-timing-cohort-01'
OUT.mkdir(exist_ok=False)
selected=[('51574','issued-51574','teaching'),('51573','issued-51573','teaching'),('51958','issued-51958','teaching'),('51890','issued-51890','teaching'),('51891','issued-51891','teaching'),('50925','issued-50925','calibration_reused'),('51960','issued-51960-p1','evaluation_reused'),('51482','issued-51482-rom-masked-01','evaluation_reused')]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
files=[Path(__file__),*sorted(Path('src/learning').glob('*.py'))];games=[]
for game,prior,role in selected:
 p=ROOT/prior/'dataset.json';r=json.loads(p.read_text());assert sha(r['replay'])==r['sha256'];files += [p,Path(r['replay'])]
 output=ROOT/'human-rom-dense-01' if game=='51482' else OUT/game
 games.append(dict(game=game,prior=str(p.parent),role=role,player_name=r['player']['player_info']['player_name'],player=r['player']['player_info']['player_id'],replay=r['replay'],sha256=r['sha256'],source=r['source'],output=str(output),human_result=r['player']['player_result']['result']))
before={str(p):sha(p) for p in files}
manifest=dict(games=games,bindings=before,training=False,rl=False,teacher='Masters human; not verified professional',reserved_games_untouched=True,roles_apply_to_both_player_views=True,calibration_player='Lyra',evaluation_players=['Huski','Rom'],teaching_player='Mez')
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');results=[]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',SC2PATH='/home/sam/repos/sc2-repos/game/SC2.4.10/StarCraftII',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONPATH='.')
for g in games:
 if g['game']=='51482':
  receipt=json.loads((Path(g['output'])/'dataset.json').read_text());assert receipt['status']=='completed' and receipt['sha256']==g['sha256'];results.append(dict(game=g['game'],status='reused_verified_pilot'));continue
 cmd=['.venv/bin/python','-W','ignore::DeprecationWarning','-m','src.learning.replay_extract',g['replay'],'--output',g['output'],'--player',str(g['player']),'--max-loops','50000','--wall-seconds','300','--observation-stride','44','--source',g['source']]
 child=subprocess.Popen(cmd,env=env,start_new_session=True,stdout=subprocess.DEVNULL);start=time.monotonic();samples=[];high=0;reason=None
 while child.poll() is None:
  cpu=psutil.cpu_percent(interval=1);samples.append(cpu);high=high+1 if cpu>80 else 0
  if high>=3 or time.monotonic()-start>320:
   reason='cpu' if high>=3 else 'wall';os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
  (OUT/'live.json').write_text(json.dumps(dict(game=g['game'],pid=child.pid,cpu=cpu,elapsed=time.monotonic()-start,stop_reason=reason))+'\n');time.sleep(.2)
 result=dict(game=g['game'],status='completed' if child.returncode==0 else 'failed',returncode=child.returncode,stop_reason=reason,peak_cpu=max(samples,default=0),wall_seconds=time.monotonic()-start,samples=samples)
 results.append(result);(OUT/'progress.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='samples'}),flush=True)
 if child.returncode:raise SystemExit(child.returncode)
 r=json.loads((Path(g['output'])/'dataset.json').read_text());assert r['status']=='completed' and r['sha256']==g['sha256'];assert r['disable_fog'] is False
assert all(sha(p)==h for p,h in before.items())
(OUT/'report.json').write_text(json.dumps(dict(status='completed_dense_native_cohort',manifest_sha256=sha(OUT/'manifest.json'),games=results,bindings=before,training=False,rl=False),indent=2)+'\n')
