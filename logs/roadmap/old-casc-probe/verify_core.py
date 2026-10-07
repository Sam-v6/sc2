import ctypes,hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent
lib=ctypes.CDLL(str(p/'casclib-build/libcasc.so'))
lib.CascOpenStorage.argtypes=[ctypes.c_char_p,ctypes.c_uint32,ctypes.POINTER(ctypes.c_void_p)];lib.CascOpenStorage.restype=ctypes.c_bool
lib.CascOpenFile.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.POINTER(ctypes.c_void_p)];lib.CascOpenFile.restype=ctypes.c_bool
lib.CascReadFile.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_uint32,ctypes.POINTER(ctypes.c_uint32)];lib.CascReadFile.restype=ctypes.c_bool
lib.CascCloseFile.argtypes=[ctypes.c_void_p];lib.CascCloseStorage.argtypes=[ctypes.c_void_p]
h=ctypes.c_void_p();assert lib.CascOpenStorage(str(p.parent/'runtime-4.9.3').encode(),2,ctypes.byref(h))
rows=[]
for s in (p/'mndx-query.tsv').read_text().splitlines():
 fields=s.split('\t')
 if fields[0]!='MATCH':continue
 _,name,ckey,ekey,size,available=fields
 if not (name.startswith('mods\\core.sc2mod\\base.sc2data') or name.startswith('mods\\core.sc2mod\\enus.sc2data')):continue
 size=int(size);assert available=='1' and size<1024**2
 f=ctypes.c_void_p();assert lib.CascOpenFile(h,name.encode(),2,0,ctypes.byref(f));buf=ctypes.create_string_buffer(size);got=ctypes.c_uint32();assert lib.CascReadFile(f,buf,size,ctypes.byref(got));assert got.value==size;lib.CascCloseFile(f)
 assert hashlib.md5(buf.raw).hexdigest()==ckey
 rows.append({'path':name,'ckey':ckey,'ekey':ekey,'bytes':size,'full_content_md5_verified':True})
lib.CascCloseStorage(h)
(p/'core-content-checks.json').write_text(json.dumps({'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'files':rows},indent=2)+'\n');print('verified',len(rows),'full core contents')
