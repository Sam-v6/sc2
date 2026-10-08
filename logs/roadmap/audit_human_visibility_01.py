"""Offline visibility geometry audit; teaching/development only, no fitting."""
import base64,gzip,hashlib,json,math
from pathlib import Path
from collections import Counter

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest=Path('logs/roadmap/pro-source-expansion-02/final-verification.json')
out=Path('logs/roadmap/human-visibility-audit-01');out.mkdir(exist_ok=False)
results=[]
for source in json.loads(manifest.read_text())['sources']:
 assert source['role'] in ('teaching','development')
 p=Path(source['path'])/'examples.jsonl.gz';counts=Counter();examples=[]
 for line in gzip.open(p,'rt'):
  state=json.loads(line)['observation'];counts['states']+=1
  image=state['map']['visibility'];assert image['bits_per_pixel']==8
  pixels=base64.b64decode(image['data']);w,h=image['width'],image['height']
  assert len(pixels)==w*h
  feature=image.get('coordinate_system')=='feature_minimap'
  if feature:assert image['transform']=='world_y_flip_then_uniform_max_dimension_scale'
  for unit in state['units']:
   if unit['alliance']!=4:continue
   counts['enemy_current']+=1;x,y=unit['position'][:2]
   native_x,native_y=round(x),round(y)
   native_ok=0<=native_x<w and 0<=native_y<h and pixels[native_y*w+native_x]==2
   if not native_ok:counts['native_assumption_rejects']+=1
   if feature:
    sx,sy=image['world_size'];scale=w/max(sx,sy)
    ix,iy=math.floor(x*scale),math.floor((sy-y)*scale)
   else:ix,iy=native_x,native_y
   value=pixels[iy*w+ix] if 0<=ix<w and 0<=iy<h else None
   counts['mapped_visible' if value==2 else 'mapped_nonvisible']+=1
   # Coarse cells near a vision boundary cannot establish actual invisibility.
   neighborhood=[pixels[b*w+a] for a in range(max(0,ix-1),min(w,ix+2)) for b in range(max(0,iy-1),min(h,iy+2))]
   if value!=2 and 2 not in neighborhood:
    counts['no_visible_neighbor']+=1
    if len(examples)<3:examples.append(dict(loop=state['game_loop'],unit=unit['unit_type'],position=[x,y],mapped_cell=[ix,iy],pixel=value))
 result=dict(path=str(p),role=source['role'],counts=dict(counts),examples=examples,sha256=sha(p))
 results.append(result);print(json.dumps(result),flush=True)
receipt=dict(status='diagnostic',sources=results,bindings={str(manifest):sha(manifest),__file__:sha(__file__)},
 limits=['Coarse feature-grid cells and neighboring cells are diagnostics, not native visibility proof.',
 'No source data is edited; no fitting or reserved source reads.',
 'Native grid coordinates cannot be applied directly to feature-minimap sources.'])
(out/'report.json').write_text(json.dumps(receipt,indent=2)+'\n')
