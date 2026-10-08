import json,struct,pathlib,hashlib
P=pathlib.Path(__file__).parent
class Reader:
 def __init__(self,b):self.b=b;self.p=0
 def read(self,n):assert 0<=n<=len(self.b)-self.p;v=self.b[self.p:self.p+n];self.p+=n;return v
 def unpack(self,f):return struct.unpack(f,self.read(struct.calcsize(f)))
 def vector(self,size):n=self.unpack('<Q')[0];assert n<10000000;return n,self.read(n*size)
 def string(self):return self.vector(1)[1].decode()
 def image(self):h,w=self.unpack('<ii');n,b=self.vector(1);assert h==w==128 and n in (2048,16384);return h,w,n
for idx in (294,774,870):
 b=(P/f'fall-record-{idx}.bin').read_bytes();r=Reader(b);header={'hash':r.string(),'version':r.string()};header.update(zip(('player','duration'),r.unpack('<II')));header.update(zip(('race','result','mmr','apm','width','height'),r.unpack('<bbiiii')));header['heightmap']=r.image()
 n,v=r.vector(4);steps=struct.unpack(f'<{n}I',v); print(idx,header,n,steps[:8],flush=True)
 for k in ('minerals','gas','cap','army','workers'):
  count,v=r.vector(2);assert count==n
 count,v=r.vector(88);assert count==n
 for k in ('visibility','creep','relative','alerts','buildable','pathable'):
  count=r.unpack('<Q')[0];assert count==n
  for _ in range(count):r.image()
 count=r.unpack('<Q')[0];assert count==n
 actions=[]
 for loop in steps:
  row=[];k=r.unpack('<Q')[0];assert k<10000
  for _ in range(k):
   c,v=r.vector(8);tags=struct.unpack(f'<{c}Q',v);ability,target=r.unpack('<ii');u=r.read(8);assert target in (0,1,2)
   row.append({'ability':ability,'tags':tags,'target_type':target,'target':struct.unpack('<ii',u) if target==2 else struct.unpack('<Q',u)[0] if target==1 else None})
  actions.append({'loop':loop,'actions':row})
 out={'header':header,'record_sha256':hashlib.sha256(b).hexdigest(),'observation_count':n,'first_loop':steps[0],'last_loop':steps[-1],'actions':actions,'units_offset':r.p,'remaining_bytes':len(b)-r.p};(P/f'fall-actions-{idx}.json').write_text(json.dumps(out,indent=2)+'\n');print('decoded',idx,sum(len(x['actions']) for x in actions),'offset',r.p,flush=True)
