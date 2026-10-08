from pathlib import Path
import hashlib,json,sqlite3
import mpyq,sc2reader
from src.learning.zip_member import fetch_member
P=Path(__file__).parent;source=Path('logs/roadmap/pro-preconverted-probe-01');plan=json.loads((P/'contract.json').read_text())
for path,expected in plan['input_bindings'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected
ledger_path=P/'ledger.json';ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {'cap_bytes':plan['cap_bytes'],'reserved_bytes':0,'requests':[]}
rows=[];db=sqlite3.connect(f'file:{source}/gamedata.db?mode=ro',uri=True);db.row_factory=sqlite3.Row
for entry in plan['records']:
 output=P/entry['name']
 if not output.exists():
  reserve=entry['compressed']+4126
  assert ledger['reserved_bytes']+reserve<=ledger['cap_bytes']
  ledger['reserved_bytes']+=reserve;request={'kind':'raw_replay','name':entry['name'],'reserved_bytes':reserve,'status':'reserved'};ledger['requests'].append(request);ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
  receipt=fetch_member(plan['raw_url'],entry['header_offset'],entry['name'],output,entry['compressed'],entry['crc'])
  request.update(status='completed',actual_bytes=receipt['download_bytes']);ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
 else:
  receipt=json.loads(output.with_suffix(output.suffix+'.source.json').read_text());assert hashlib.sha256(output.read_bytes()).hexdigest()==receipt['sha256']
 replay=sc2reader.load_replay(str(output),load_level=4,load_map=False)
 metadata=json.loads(mpyq.MPQArchive(str(output)).read_file('replay.gamemetadata.json'))
 players=[{'name':p.name,'race':p.play_race,'pid':p.pid,'result':p.result} for p in replay.players]
 terrans=[]
 for player in metadata['Players']:
  if player['AssignedRace']!='Terr':continue
  candidates=[dict(r) for r in db.execute("SELECT idx,replayHash,playerId,playerRace,playerResult,playerAPM,game_length,number_game_step,gameVersion FROM game_data WHERE partition=? AND playerRace='0' AND playerId=? AND abs(playerAPM-?)<=1 AND abs(game_length-?)<=32 AND read_success=1 AND parse_success=1",('2019_WCS_Fall.SC2Replays',player['PlayerID'],player['APM'],replay.frames))]
  terrans.append({'original_player':player,'candidates':candidates})
 row={'entry':entry,'sha256':receipt['sha256'],'metadata':metadata,'players':players,'frames':replay.frames,'map_hash':replay.map_hash,'terran_candidates':terrans};rows.append(row)
 (P/'raw-metadata.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(entry['name'],players,[(p['original_player']['PlayerID'],[r['idx'] for r in p['candidates']]) for p in terrans],flush=True)
