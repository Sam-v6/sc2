"""Bounded candidate intake; no source is admitted to training here."""
import hashlib,json,sqlite3
from pathlib import Path
import mpyq,sc2reader
from src.learning.zip_member import fetch_member
P=Path(__file__).parent; old=Path('logs/roadmap/pro-preconverted-probe-01')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=P/'contract.json'
if not manifest.exists():
    mapping=json.loads((old/'processed_mapping.json').read_text())
    catalog=json.loads((old/'fall-raw-zip-catalog.json').read_text())
    available={e['name']:e for e in catalog}
    acquired={p.name for p in Path('logs/roadmap').rglob('*.SC2Replay')}
    selected=[]
    for teacher in ('Clem','HeroMarine','uThermal','TIME','SpeCial','Clem'):
        candidates=[]
        for name,path in mapping.items():
            matchup=path.split('/')[-2].split(' vs. ')
            # The pack marks rematches with a suffix on the second player's name.
            matchup=[s.removesuffix(' 2').removesuffix(' 3') for s in matchup]
            if teacher not in matchup or path.split('/')[-1] not in ('Acropolis.SC2Replay','Disco Bloodbath.SC2Replay') or name in acquired or name not in available:
                continue
            candidates.append(dict(available[name],original_path=path,requested_teacher=teacher))
        if candidates:
            entry=min(candidates,key=lambda e:(e['compressed'],e['name']))
            selected.append(entry); acquired.add(entry['name'])
    paths=[old/'processed_mapping.json',old/'fall-raw-zip-catalog.json',old/'gamedata.db',old/'fall-full-offset-table.bin',Path(__file__),Path('docs/superpowers/plans/2026-10-06-professional-source-expansion-02.md')]
    contract=dict(cap_bytes=16*1024**2,raw_url='https://zenodo.org/api/records/14963356/files/2019_WCS_Fall.zip/content',converted_url='https://ndownloader.figshare.com/files/46449298',records=selected,bindings={str(p):sha(p) for p in paths},rl=False,training_eligible=False)
    manifest.write_text(json.dumps(contract,indent=2)+'\n')
plan=json.loads(manifest.read_text())
assert all(sha(Path(p))==d for p,d in plan['bindings'].items())
ledgerpath=P/'ledger.json'
ledger=json.loads(ledgerpath.read_text()) if ledgerpath.exists() else dict(cap_bytes=plan['cap_bytes'],reserved_bytes=0,requests=[])
db=sqlite3.connect(f'file:{old}/gamedata.db?mode=ro',uri=True); db.row_factory=sqlite3.Row
results=[]
for entry in plan['records']:
    output=P/entry['name']
    if not output.exists():
        reserve=entry['compressed']+4126
        assert ledger['reserved_bytes']+reserve<=plan['cap_bytes']
        request=dict(kind='raw',name=entry['name'],reserved_bytes=reserve,status='reserved')
        ledger['requests'].append(request);ledger['reserved_bytes']+=reserve
        ledgerpath.write_text(json.dumps(ledger,indent=2)+'\n')
        receipt=fetch_member(plan['raw_url'],entry['header_offset'],entry['name'],output,entry['compressed'],entry['crc'])
        request.update(status='completed',actual_bytes=receipt['download_bytes']);ledgerpath.write_text(json.dumps(ledger,indent=2)+'\n')
    else:
        receipt=json.loads(output.with_suffix('.SC2Replay.source.json').read_text());assert sha(output)==receipt['sha256']
    replay=sc2reader.load_replay(str(output),load_level=2,load_map=False)
    metadata=json.loads(mpyq.MPQArchive(str(output)).read_file('replay.gamemetadata.json'))
    players=[dict(name=p.name,race=p.play_race,pid=p.pid,result=p.result) for p in replay.players]
    aliases={'HeroMarine':'HeRoMaRinE'}
    teachers=[p for p in players if p['race']=='Terran' and p['name'].casefold()==aliases.get(entry['requested_teacher'],entry['requested_teacher']).casefold()]
    candidates=[]
    if len(teachers)==1 and metadata['GameVersion']=='4.10.2.76052':
        teacher=teachers[0]
        original=next(p for p in metadata['Players'] if p['PlayerID']==teacher['pid'])
        candidates=[dict(r) for r in db.execute("SELECT idx,replayHash,playerId,playerAPM,game_length,number_game_step FROM game_data WHERE partition=? AND playerRace='0' AND playerId=? AND playerAPM=? AND abs(game_length-?)<=32 AND read_success=1 AND parse_success=1",('2019_WCS_Fall.SC2Replays',teacher['pid'],original['APM'],replay.frames))]
    row=dict(entry=entry,sha256=sha(output),players=players,teacher=teachers[0] if len(teachers)==1 else None,map_hash=replay.map_hash,frames=replay.frames,metadata=metadata,candidates=candidates,training_eligible=False)
    results.append(row);(P/'raw-metadata.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(dict(name=entry['name'],players=players,candidate_ids=[c['idx'] for c in candidates],reserved_bytes=ledger['reserved_bytes'])),flush=True)
