import concurrent.futures,hashlib,json,urllib.request
from pathlib import Path
p=Path(__file__).resolve().parent;j=json.loads((p/'casclib-tree.json').read_text());files=[x for x in j['tree'] if x['type']=='blob' and (x['path'].startswith('src/') or x['path'] in ['CMakeLists.txt','Config.cmake.in','LICENSE'])]
assert sum(x['size'] for x in files)+len((p/'casclib-tree.json').read_bytes())+6544<3*1024**2
out=p/'casclib-src'
def fetch(x):
 url='https://raw.githubusercontent.com/ladislav-zezula/CascLib/'+j['sha']+'/'+x['path'];b=urllib.request.urlopen(url,timeout=20).read(x['size']+1);assert len(b)==x['size'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha'];q=out/x['path'];q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b);return {'path':x['path'],'url':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:r=list(pool.map(fetch,files))
(p/'casclib-source.json').write_text(json.dumps({'commit':j['sha'],'files':r,'download_bytes':sum(x['bytes'] for x in r)},indent=2)+'\n');print(len(r),sum(x['bytes'] for x in r))
