"""Continue cached ZIP prefix: root validation and read-only old/new EKey census."""
import hashlib,json,struct,zipfile,zlib,sys,random
from pathlib import Path
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE.parents[2]))
from src.learning.zip_member import read_range
URL='https://blzdistsc2-a.akamaihd.net/Linux/SC2.4.9.3.zip'
NEW=Path('/home/sam/repos/sc2-repos/game/SC2.4.10/StarCraftII/SC2Data/data')
r={'source':URL,'additional_budget':16*1024**2,'additional_bytes':0,'ranges':[]}
def main():
 d=zipfile._ZipDecrypter(b'iagreetotheeula');z=zlib.decompressobj(-15);out=bytearray();count=0;end=55734868
 while len(out)<end:
  start=246300585+count;n=4*1024**2;p=BASE/f'range-{start}-{n}.bin';cached=p.exists()
  if cached:b=p.read_bytes()
  else:
   assert r['additional_bytes']+n<=r['additional_budget']
   b=read_range(URL,start,n);p.write_bytes(b);r['additional_bytes']+=n
  assert len(b)==n
  r['ranges'].append({'start':start,'bytes':n,'cached':cached,'sha256':hashlib.sha256(b).hexdigest()})
  (BASE/'root-receipt.json').write_text(json.dumps(r,indent=2)+'\n')
  b=d(b);out.extend(z.decompress(b[12:] if count==0 else b,end-len(out)));count+=n
  print('prefix',count,'decoded',len(out),flush=True)
 record=bytes(out[41839308:end]);blte=record[30:];hs=int.from_bytes(blte[4:8],'big')
 assert blte[:4]==b'BLTE' and hs>0 and hashlib.md5(blte[:hs]).hexdigest()=='f3c15824a2c697acbc1d585c69621591'
 chunks=int.from_bytes(blte[9:12],'big');assert hs==12+24*chunks
 decoded=bytearray();pos=hs
 for i in range(chunks):
  a,b=struct.unpack_from('>II',blte,12+24*i);q=blte[pos:pos+a]
  assert hashlib.md5(q).digest()==blte[20+24*i:36+24*i]
  assert q[:1] in (b'N',b'Z');v=q[1:] if q[:1]==b'N' else zlib.decompress(q[1:]);assert len(v)==b
  decoded.extend(v);pos+=a
 assert pos==len(blte) and len(decoded)==20216408
 assert hashlib.md5(decoded).hexdigest()=='c305368c63621480462f8f516fb64374'
 (BASE/'root.record').write_bytes(record);(BASE/'root.decoded').write_bytes(decoded)
 (BASE/'encoding.record').write_bytes(out[113493:41839308])
 r['root']={'ekey':'f3c15824a2c697acbc1d585c69621591','ckey':hashlib.md5(decoded).hexdigest(),'chunks_verified':chunks,'decoded_bytes':len(decoded),'sha256':hashlib.sha256(decoded).hexdigest()}
 index={};indexfiles=[]
 for bucket in range(16):
  p=max(NEW.glob(f'{bucket:02x}*.idx'));b=p.read_bytes()
  assert b[8:16]==bytes([7,0,bucket,0,4,5,9,30]);n=int.from_bytes(b[32:36],'little');assert n%18==0 and 40+n<=len(b)
  for i in range(40,40+n,18):index[b[i:i+9]]=b[i+9:i+18]
  indexfiles.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'entries':n//18})
 enc=(BASE/'encoding.decoded').read_bytes();pages=int.from_bytes(enc[9:13],'big');size=int.from_bytes(enc[5:7],'big')*1024;start=22+int.from_bytes(enc[18:22],'big')+pages*32
 keys=set()
 for i in range(pages):
  page=enc[start+i*size:start+(i+1)*size];p=0
  while p<len(page):
   n=int.from_bytes(page[p:p+2],'little')
   if not n:break
   assert p+22+16*n<=len(page)
   for j in range(n):keys.add(bytes(page[p+22+16*j:p+38+16*j]))
   p+=22+16*n
 present=sorted(k for k in keys if k[:9] in index);missing=len(keys)-len(present)
 sample=random.Random(75025).sample(present,min(256,len(present)));verified=0
 for key in sample:
  e=index[key[:9]];o=int.from_bytes(e[:5],'big');length=int.from_bytes(e[5:],'little');p=NEW/f'data.{o>>30:03x}';offset=o&((1<<30)-1)
  assert offset+length<=p.stat().st_size
  with p.open('rb') as f:
   f.seek(offset);head=f.read(38);assert head[30:34]==b'BLTE';hs=int.from_bytes(head[34:38],'big')
   assert head[:16][::-1]==key
   if hs:
    assert hs<=length-30;f.seek(offset+30);digest=hashlib.md5(f.read(hs)).digest()
   else:
    f.seek(offset+30);digest=hashlib.md5(f.read(length-30)).digest()
   assert digest==key;verified+=1
 r['coverage']={'old_unique_ekeys':len(keys),'current_prefix_matches':len(present),'missing':missing,'missing_fraction':missing/len(keys),'sample_rng':75025,'sample_full_ekey_verified':verified,'sample_count':len(sample),'interpretation':'Full encoding census, not root-required asset set; matches first9bytes, sampled256 verified full EKey and physical header.'}
 r['current_indices']=indexfiles;r['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();r['status']='root_integrity_verified_no_engine_no_overlay'
 (BASE/'root-receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['root'],indent=2));print(json.dumps(r['coverage'],indent=2))
if __name__=='__main__':main()
