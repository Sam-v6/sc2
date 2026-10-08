import hashlib,json
from pathlib import Path
import mpyq
from src.learning.replay_extract import load_protocol
ROOT=Path('logs/roadmap');OUT=ROOT/'human-demonstration-outcomes-01';audit=json.loads((OUT/'audit.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,h in audit['bindings'].items():assert sha(p)==h,p
names=[]
for game in audit['games']:
 archive=mpyq.MPQArchive(game['source_replay']);meta=json.loads(archive.read_file('replay.gamemetadata.json'));protocol=load_protocol(int(meta['BaseBuild'][4:]));details=protocol.decode_replay_details(archive.read_file('replay.details'))
 teacher=details['m_playerList'][game['player']-1]
 assert {1:'Win',2:'Loss'}[teacher['m_result']]==game['result']
 assert next(p['SelectedRace'] for p in meta['Players'] if p['PlayerID']==game['player'])=='Terr'
 # Detail race names are localized (one replay labels Terran in Chinese).
 names.append(dict(game=game['game'],player=game['player'],name=teacher['m_name'].decode(),result=game['result'],role=game['role']))
summary={role:{race:{result:sum(g['role']==role and g['opponent_selected_race']==race and g['result']==result for g in audit['games']) for result in ['Win','Loss']} for race in ['Terr','Zerg','Prot']} for role in ['teaching','development']}
assert summary==audit['summary']
receipt=dict(status='verified_demonstration_outcomes',games=names,summary=summary,bindings={str(p):sha(p) for p in [Path(__file__),OUT/'audit.json']})
(OUT/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
