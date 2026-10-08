"""Independent re-import accounting: labels, own state, fog and target availability."""
import base64,gzip,hashlib,json,math
from collections import Counter
from pathlib import Path
from itertools import zip_longest

OUT=Path('logs/roadmap/human-visibility-reimport-01')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(bindings):
 for p,h in bindings.items():assert sha(p)==h,p
def main():
 report=json.loads((OUT/'report.json').read_text());assert report['status']=='completed' and len(report['results'])==14
 check(report['bindings']);assert not report['training'] and not report['rl']
 jobs=json.loads((OUT/'jobs.json').read_text());bindings={str(p):sha(p) for p in(OUT/'report.json',OUT/'contract.json',Path(__file__))};results=[]
 for entry in jobs:
  old,new=Path(entry['old']),Path(entry['job']['output']);receipt=json.loads((new/'dataset.json').read_text())
  assert receipt['disable_fog'] is False and receipt['alignment']=='state_at_issue_loop_before_effect'
  check(receipt['source_bindings']);check(receipt['code_bindings'])
  check({str(new/n):h for n,h in receipt['corpus_bindings'].items()})
  assert (old/'static.json').read_bytes()==(new/'static.json').read_bytes()
  counts=Counter();missing=Counter()
  with gzip.open(old/'examples.jsonl.gz','rt') as before,gzip.open(new/'examples.jsonl.gz','rt') as after:
   for a,b in zip_longest(before,after):
    assert a is not None and b is not None
    a,b=json.loads(a),json.loads(b);counts['states']+=1
    assert {k:v for k,v in a.items() if k!='observation'}=={k:v for k,v in b.items() if k!='observation'}
    st,prior=b['observation'],a['observation'];assert st['game_loop']==prior['game_loop']
    assert st['player']==prior['player'] and st['map']==prior['map']
    assert [u for u in st['units'] if u['alliance']!=4]==[u for u in prior['units'] if u['alliance']!=4]
    assert st['owned_memory']==prior['owned_memory']
    image=st['map']['visibility'];pixels=base64.b64decode(image['data']);w=image['width'];h=image['height'];sx,sy=image['world_size'];scale=w/max(sx,sy)
    assert image['coordinate_system']=='feature_minimap' and image['transform']=='world_y_flip_then_uniform_max_dimension_scale'
    for u in st['units']:
     if u['alliance']!=4:continue
     x,y=u['position'][:2];ix,iy=math.floor(x*scale),math.floor((sy-y)*scale)
     assert 0<=ix<w and 0<=iy<h and pixels[iy*w+ix]==2
     assert u['display_type']==1;counts['current_enemy']+=1
    for u in st['memory']:
     assert not any(k in u for k in ('health','shield','energy','orders','weapon_cooldown'))
    old_tags={u['tag'] for u in prior['units']}|{u['tag'] for u in prior['memory']}
    current_tags={u['tag'] for u in st['units']}|{u['tag'] for u in st['memory']}
    for c in b['commands']:
     tag=c['target_unit']
     if tag is not None and tag not in current_tags:
      counts['target_unavailable']+=1
      if tag in old_tags:counts['newly_unavailable']+=1;missing[c['ability']]+=1
  item=dict(role=entry['role'],old=str(old),new=str(new),counts=dict(counts),newly_unavailable_by_ability=dict(missing))
  results.append(item);print(json.dumps(item),flush=True)
  bindings.update({str(p):sha(p) for p in(old/'examples.jsonl.gz',new/'examples.jsonl.gz',new/'dataset.json',new/'static.json')})
 result=dict(status='verified_reimport',sources=results,bindings=bindings,training=False,rl=False,
 limits=['Fog check uses supplied coarse feature cells, not reconstructed native visibility.',
 'Labels are preserved even when targets become unavailable; fitting must explicitly reject unsupported command arguments.',
 'Historical corpora and reserved games are untouched.'])
 (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
