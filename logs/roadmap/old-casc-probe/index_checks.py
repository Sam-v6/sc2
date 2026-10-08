"""Read-only verification of installed CASC v7 index checksums."""
import hashlib,json,struct
from pathlib import Path
MASK=0xffffffff
def rot(x,k):return ((x<<k)|(x>>(32-k)))&MASK
def lookup(data,pc=0,pb=0):
 a=b=c=(0xdeadbeef+len(data)+pc)&MASK;c=(c+pb)&MASK;p=0
 while len(data)-p>12:
  x,y,z=struct.unpack_from('<III',data,p);a=(a+x)&MASK;b=(b+y)&MASK;c=(c+z)&MASK
  a=((a-c)^rot(c,4))&MASK;c=(c+b)&MASK;b=((b-a)^rot(a,6))&MASK;a=(a+c)&MASK;c=((c-b)^rot(b,8))&MASK;b=(b+a)&MASK
  a=((a-c)^rot(c,16))&MASK;c=(c+b)&MASK;b=((b-a)^rot(a,19))&MASK;a=(a+c)&MASK;c=((c-b)^rot(b,4))&MASK;b=(b+a)&MASK;p+=12
 tail=data[p:]
 if not tail:return c,b
 a=(a+int.from_bytes(tail[:4],'little'))&MASK;b=(b+int.from_bytes(tail[4:8],'little'))&MASK;c=(c+int.from_bytes(tail[8:12],'little'))&MASK
 c=((c^b)-rot(b,14))&MASK;a=((a^c)-rot(c,11))&MASK;b=((b^a)-rot(a,25))&MASK;c=((c^b)-rot(b,16))&MASK;a=((a^c)-rot(c,4))&MASK;b=((b^a)-rot(a,14))&MASK;c=((c^b)-rot(b,24))&MASK
 return c,b
p=Path('/home/sam/repos/sc2-repos/game/SC2.4.10/StarCraftII/SC2Data/data');out=[]
for bucket in range(16):
 f=max(p.glob(f'{bucket:02x}*.idx'));b=f.read_bytes();length,expected=struct.unpack_from('<II',b);assert length==16 and lookup(b[8:24])[0]==expected
 length,expected=struct.unpack_from('<II',b,32);hi=lo=0;single=0
 for i in range(40,40+length,18):
  e=b[i:i+18];hi,lo=lookup(e,hi,lo);single=lookup(e,single)[0]
 assert expected in (hi,single)
 out.append({'path':str(f),'header_hash_verified':True,'entries':length//18,'entry_hash_verified':True,'entry_hash_mode':'hashlittle2' if expected==hi else 'hashlittle','sha256':hashlib.sha256(b).hexdigest()})
q=Path(__file__).parent/'index-checks.json';q.write_text(json.dumps({'indices':out,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'reference':'https://github.com/ladislav-zezula/CascLib/blob/master/src/CascIndexFiles.cpp'},indent=2)+'\n');print('verified',len(out),'indices',sum(x['entries'] for x in out),'entries')
