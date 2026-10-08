"""Retrieve candidate records under the same total transfer reservation."""
import hashlib,json,struct,zlib
from pathlib import Path
from src.learning.zip_member import read_range
from src.learning.tournament_record import decode_record
P=Path(__file__).parent;old=Path('logs/roadmap/pro-preconverted-probe-01')
plan=json.loads((P/'contract.json').read_text()); raw=json.loads((P/'raw-metadata.json').read_text())
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==d for p,d in plan['bindings'].items())
blob=(old/'fall-full-offset-table.bin').read_bytes();offsets=struct.unpack(f'<{len(blob)//8}Q',blob)
excluded={294,870,955,839,991,523,887,920,851,774,848,51483,51886}
previous={json.loads(p.read_text())['sha256'] for p in [*Path('logs/roadmap/pro-demonstrations-07').glob('*/dataset.json')]}
records=[]
for r in raw:
    if len(r['candidates'])!=1:continue
    assert r['sha256'] not in previous
    c=r['candidates'][0];i=c['idx']
    assert i not in excluded and 0<=i<offsets[0]
    assert r['map_hash'] in {'30770d8ce03908498e085a7e8ccb6c2b09d0379fc06d5a2921b353689c19a0e9','fedc709fae1bbc0904c8b97f1f58efd8ab65636d4e6afd13e8b6e94e3219aca2'}
    start,end=offsets[i+1:i+3];assert start<end
    records.append(dict(idx=i,raw_name=r['entry']['name'],teacher=r['teacher'],metadata=c,map_hash=r['map_hash'],start=start,end=end,bytes=end-start,split='new_teaching_candidate'))
selection=dict(records=records,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P/'contract.json',P/'raw-metadata.json',Path(__file__)]},training_eligible=False)
selectionpath=P/'record-range-plan.json'
if selectionpath.exists(): assert json.loads(selectionpath.read_text())==selection
else:selectionpath.write_text(json.dumps(selection,indent=2)+'\n')
ledgerpath=P/'ledger.json'; results=[]
for item in records:
    i=item['idx'];cp=P/f'fall-record-{i}.zlib';dp=P/f'fall-record-{i}.bin'
    ledger=json.loads(ledgerpath.read_text())
    if not cp.exists():
        assert ledger['reserved_bytes']+item['bytes']<=plan['cap_bytes']
        request=dict(kind='converted',idx=i,reserved_bytes=item['bytes'],status='reserved')
        ledger['reserved_bytes']+=item['bytes'];ledger['requests'].append(request);ledgerpath.write_text(json.dumps(ledger,indent=2)+'\n')
        compressed=read_range(plan['converted_url'],item['start'],item['bytes']);cp.write_bytes(compressed)
        request.update(status='completed',actual_bytes=len(compressed),sha256=hashlib.sha256(compressed).hexdigest());ledgerpath.write_text(json.dumps(ledger,indent=2)+'\n')
    else:
        compressed=cp.read_bytes();completed=[r for r in ledger['requests'] if r.get('idx')==i and r['status']=='completed'];assert completed and hashlib.sha256(compressed).hexdigest()==completed[-1]['sha256']
    decoder=zlib.decompressobj();data=decoder.decompress(compressed,256*1024**2+1)
    assert len(data)<=256*1024**2 and decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data
    record=decode_record(data);h=record['header'];assert h['hash']==item['metadata']['replayHash'] and h['player']==item['teacher']['pid'] and h['race']==0 and h['version']=='4.10.2.76052'
    if not dp.exists():dp.write_bytes(data)
    assert hashlib.sha256(dp.read_bytes()).hexdigest()==hashlib.sha256(data).hexdigest()
    actions=[]
    for loop,commands in zip(record['steps']['game_loop'],record['actions'],strict=True):
        actions.append(dict(loop=int(loop),actions=[dict(ability=c['ability'],tags=c['units'],target_type=c['target_type'],target=c.get('target_unit',c.get('target_point'))) for c in commands]))
    actionreport=dict(idx=i,record_sha256=hashlib.sha256(data).hexdigest(),compressed_sha256=hashlib.sha256(compressed).hexdigest(),decoded_bytes=len(data),header={k:v for k,v in h.items() if k!='height_map'},observation_count=len(actions),actions=actions)
    (P/f'fall-actions-{i}.json').write_text(json.dumps(actionreport,indent=2)+'\n')
    results.append({k:v for k,v in actionreport.items() if k!='actions'});(P/'record-retrieval.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(dict(idx=i,decoded_bytes=len(data),observations=len(actions),reserved_bytes=ledger['reserved_bytes'])),flush=True)
    del record,data,actions
