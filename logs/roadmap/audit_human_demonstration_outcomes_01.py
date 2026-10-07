"""Teacher outcome/stock coverage audit from existing verified raw replays."""
import hashlib,json
from pathlib import Path
import numpy as np
from src.learning.replay_extract import replay_metadata
ROOT=Path('logs/roadmap');SOURCE=ROOT/'human-inventory-targets-03';OUT=ROOT/'human-demonstration-outcomes-01'
OUT.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
intake=json.loads((ROOT/'human-visibility-reimport-01/verification.json').read_text());paths={Path(s['new']).name:Path(s['new']) for s in intake['sources']}
race_audit=json.loads((SOURCE/'opponent-race-audit.json').read_text());known={g['game']:g for g in race_audit['games']}
names=json.loads((SOURCE/'preparation.json').read_text())['names'];indices={n:i for i,n in enumerate(names)}
games=[];bindings={}
for role in ['teaching','development']:
 refs=json.loads((SOURCE/f'{role}-rows.json').read_text());current=np.load(SOURCE/f'{role}-current.npy')
 for game in dict.fromkeys(r['game'] for r in refs):
  directory=paths[game];receipt=json.loads((directory/'dataset.json').read_text());p=Path(receipt['source_replay']);assert sha(p)==known[game]['source_sha256']
  metadata,_=replay_metadata(p);player=receipt['player']['player_info']['player_id'];teacher=next(x for x in metadata['Players'] if x['PlayerID']==player)
  assert teacher['SelectedRace']=='Terr'
  opponent=next(x for x in metadata['Players'] if x['PlayerID']!=player);assert opponent['SelectedRace']==known[game]['opponent_selected_race']
  selected=[i for i,r in enumerate(refs) if r['game']==game];coverage=[]
  for seconds in [150,300,450,600]:
   i=min(selected,key=lambda i:abs(refs[i]['loop']/22.4-seconds));row=refs[i];distance=abs(row['loop']/22.4-seconds)
   coverage.append(dict(requested_seconds=seconds,observed_seconds=row['loop']/22.4,row=row['row'],within45seconds=distance<=45,workers=int(current[i,indices['unit:SCV']]),depots=int(current[i,indices['unit:SupplyDepot']]),capacity=int(sum(current[i,indices['unit:'+n]] for n in ['Barracks','Factory','Starport']))))
  games.append(dict(game=game,role=role,player=player,result=teacher['Result'],opponent_selected_race=opponent['SelectedRace'],source_replay=str(p),source_sha256=sha(p),coverage=coverage))
  bindings[str(directory/'dataset.json')]=sha(directory/'dataset.json');bindings[str(p)]=sha(p)
 for suffix in ['rows.json','current.npy']:bindings[str(SOURCE/f'{role}-{suffix}')]=sha(SOURCE/f'{role}-{suffix}')
summary={role:{race:{result:sum(g['role']==role and g['opponent_selected_race']==race and g['result']==result for g in games) for result in ['Win','Loss']} for race in ['Terr','Zerg','Prot']} for role in ['teaching','development']}
bindings.update({str(p):sha(p) for p in [Path(__file__),SOURCE/'opponent-race-audit.json',SOURCE/'preparation.json']})
report=dict(status='audited_demonstration_outcomes',games=games,summary=summary,training=False,rl=False,bindings=bindings)
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(summary=summary,dominant_native_teacher=next(g for g in games if g['game']=='523'))))
