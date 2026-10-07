from pathlib import Path
import hashlib,json,zlib
from src.learning.zip_member import read_range
from src.learning.tournament_record import decode_record
P=Path(__file__).parent;plan=json.loads((P/'contract.json').read_text());selection=json.loads((P/'record-range-plan.json').read_text());ledger_path=P/'ledger.json';results=[]
for item in selection['records']:
 index=item['idx'];compressed_path=P/f'fall-record-{index}.zlib';decoded_path=P/f'fall-record-{index}.bin';ledger=json.loads(ledger_path.read_text())
 if not compressed_path.exists():
  assert ledger['reserved_bytes']+item['bytes']<=ledger['cap_bytes']
  ledger['reserved_bytes']+=item['bytes'];request={'kind':'converted_record','idx':index,'reserved_bytes':item['bytes'],'status':'reserved'};ledger['requests'].append(request);ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
  compressed=read_range(plan['converted_url'],item['start'],item['bytes']);compressed_path.write_bytes(compressed)
  request.update(status='completed',actual_bytes=len(compressed),sha256=hashlib.sha256(compressed).hexdigest());ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
 else:
  compressed=compressed_path.read_bytes();completed=[r for r in ledger['requests'] if r.get('idx')==index and r.get('status')=='completed'];assert completed and hashlib.sha256(compressed).hexdigest()==completed[-1]['sha256']
 decoder=zlib.decompressobj();data=decoder.decompress(compressed,256*1024**2+1)
 assert len(data)<=256*1024**2 and decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data
 record=decode_record(data);header=record['header'];assert header['hash']==item['metadata']['replayHash'] and header['player']==item['metadata']['playerId'] and header['race']==0 and header['version']=='4.10.2.76052'
 if not decoded_path.exists():decoded_path.write_bytes(data)
 assert hashlib.sha256(decoded_path.read_bytes()).hexdigest()==hashlib.sha256(data).hexdigest()
 actions=[]
 for loop,commands in zip(record['steps']['game_loop'],record['actions'],strict=True):
  row=[]
  for command in commands:
   row.append({'ability':command['ability'],'tags':command['units'],'target_type':command['target_type'],'target':command.get('target_unit',command.get('target_point'))})
  actions.append({'loop':int(loop),'actions':row})
 result={'idx':index,'record_sha256':hashlib.sha256(data).hexdigest(),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'decoded_bytes':len(data),'header':{k:v for k,v in header.items() if k!='height_map'},'observation_count':len(actions),'actions':actions}
 (P/f'fall-actions-{index}.json').write_text(json.dumps(result,indent=2)+'\n');results.append({k:v for k,v in result.items() if k!='actions'});(P/'record-retrieval.json').write_text(json.dumps(results,indent=2)+'\n')
 print(index,len(data),len(actions),sum(len(c['actions']) for c in actions),item['split'],flush=True)
 del data,record,actions
