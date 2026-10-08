"""Bounded replay screening; metadata only, no native extraction or fitting."""
import hashlib
import json
from pathlib import Path
import urllib.request
from src.learning.replay_extract import replay_metadata

root=Path('logs/roadmap')
source=json.loads((root/'stronger-source-narrow-01.json').read_text())
ids=[int(i) for i,title in source[1]['links'] if 'A.I.' not in title] + [50996,50986,51312,51282]
ids=list(dict.fromkeys(ids))[:24]
folder=root/'human-replays';results=[];new_bytes=0
for number in ids:
    path=folder/f'{number}.SC2Replay';url=f'https://lotv.spawningtool.com/{number}/download/'
    cached=path.exists()
    if not cached:
        with urllib.request.urlopen(url,timeout=20) as response:data=response.read(min(2*1024**2,10*1024**2-new_bytes)+1)
        if len(data)>2*1024**2:raise ValueError('Replay exceeds 2 MiB cap')
        new_bytes+=len(data)
        if new_bytes>10*1024**2:raise ValueError('Screen exceeds 10 MiB cumulative cap')
        path.write_bytes(data)
    metadata,details=replay_metadata(path)
    names=[p['m_name'].decode('utf8') for p in details['m_playerList']]
    terrans=[{'name':names[p['PlayerID']-1],**p} for p in metadata['Players'] if p['AssignedRace']=='Terr']
    result={'source':f'https://lotv.spawningtool.com/{number}/','download_source':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes':path.stat().st_size,'metadata':metadata,'names':names,'professional_terran_verified':False}
    meta_path=folder/f'{number}.source.json'
    if not meta_path.exists():meta_path.write_text(json.dumps(result,indent=2)+'\n')
    results.append({'id':number,'cached':cached,'metadata':metadata,'terran_players':terrans,'sha256':result['sha256']})
    print(json.dumps({'id':number,'base':metadata['BaseBuild'],'terran_players':terrans}),flush=True)
report={'status':'completed','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'new_replay_bytes':new_bytes,'per_replay_cap':2*1024**2,'cumulative_cap':10*1024**2,'results':results,
        'selection':'Narrow date window Master+Terran candidates plus four independent-player candidates; tags can refer to either player; native metadata only, no professional claim'}
(root/'stronger-corpus-screen-02.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'completed','new_replay_bytes':new_bytes}),flush=True)
