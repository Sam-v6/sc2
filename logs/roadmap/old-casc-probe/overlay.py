"""Create only the isolated runtime CASC overlay from verified cached records."""
import hashlib,json,shutil,struct
from pathlib import Path
from index_checks import lookup
BASE=Path(__file__).resolve().parent
RUNTIME=BASE.parent/'runtime-4.9.3'
ORIGINAL=Path('/home/sam/repos/sc2-repos/game/SC2.4.10/StarCraftII/SC2Data/data')
TARGET=RUNTIME/'SC2Data/data'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert TARGET.is_symlink() and TARGET.resolve()==ORIGINAL
 before={p.name:sha(p) for p in ORIGINAL.glob('*.idx')}
 oldlink=str(TARGET.readlink());TARGET.unlink();TARGET.mkdir()
 for p in ORIGINAL.iterdir():
  if p.name.startswith('data.'):
   assert p.is_file();(TARGET/p.name).symlink_to(p)
  elif p.suffix=='.idx':shutil.copyfile(p,TARGET/p.name)
 additions=[]
 with (TARGET/'data.004').open('xb') as f:
  for name,offset,key in [('encoding.record',113493,'6a86cafee4bf07124a004b29d635717b'),('root.record',41839308,'f3c15824a2c697acbc1d585c69621591')]:
   record=(BASE/name).read_bytes();assert record[:16][::-1].hex()==key
   assert int.from_bytes(record[16:20],'little')==len(record)
   # Keep original within-archive offsets; data.004 differs by 2**32 in packed addresses.
   f.seek(offset);f.write(record)
   h=0
   for x in bytes.fromhex(key)[:9]:h^=x
   bucket=(h^(h>>4))&15
   entry=bytes.fromhex(key)[:9]+((4<<30)+offset).to_bytes(5,'big')+len(record).to_bytes(4,'little')
   additions.append((bucket,entry))
 changed=[]
 for bucket,entry in additions:
  old=max(TARGET.glob(f'{bucket:02x}*.idx'));b=old.read_bytes();count=int.from_bytes(b[32:36],'little');entries=[b[i:i+18] for i in range(40,40+count,18)]
  assert entry[:9] not in {e[:9] for e in entries};entries.append(entry);entries.sort(key=lambda e:e[:9]);newentries=b''.join(entries)
  hi=lo=0
  for e in entries:hi,lo=lookup(e,hi,lo)
  header=b[:32];assert lookup(header[8:24])[0]==int.from_bytes(header[4:8],'little')
  new=header+struct.pack('<II',len(newentries),hi)+newentries
  new+=bytes((-len(new))%65536)
  generation=int(old.stem[2:],16)+1;path=TARGET/f'{bucket:02x}{generation:08x}.idx'
  assert not path.exists();path.write_bytes(new)
  assert set(entries[:-1]) or entries
  assert set(b[i:i+18] for i in range(40,40+count,18)).issubset(set(entries))
  changed.append({'bucket':bucket,'old':old.name,'new':path.name,'before_sha256':sha(old),'after_sha256':sha(path),'old_entries':count//18,'new_entries':len(entries),'entry':entry.hex(),'checksum':hi})
 after={p.name:sha(p) for p in ORIGINAL.glob('*.idx')};assert before==after
 receipt={'old_directory_symlink':oldlink,'target':str(TARGET),'original_indices_unchanged':True,'original_indices_before':before,'original_indices_after':after,'changed_buckets':changed,'data004_bytes':(TARGET/'data.004').stat().st_size,'data004_sha256':sha(TARGET/'data.004'),'all_original_entries_preserved':True,'offset_strategy':'Preserve original record offsets; data004 packed offset differs by 2**32, preserving low32 header-offset checksums.','source_sha256':sha(Path(__file__))}
 (BASE/'overlay-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt['changed_buckets'],indent=2))
if __name__=='__main__':main()
