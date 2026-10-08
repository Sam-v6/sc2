from pathlib import Path
import hashlib,json
import numpy as np
from src.learning.tournament_record import decode_record
root=Path('logs/roadmap/human-producer-topology-01')
p=root/'audit.json'; report=json.loads(p.read_text())
r=decode_record(Path('logs/roadmap/pro-preconverted-probe-01/fall-record-870.bin').read_bytes())
f=r['units']['fields']; loops=r['steps']['game_loop']; steps=r['units']['step']
addon_types=[5,6,37,38,39,40,41,42]
checks=0; transfers={}
for row in report['transitions']+[
    dict(loop=c['loop'],producer=c['actor'],after=c['topology']) for c in report['commands']]:
    step=int(np.flatnonzero(loops==row['loop'])[0])
    own=(steps==step)&(f['alliance']==1)
    actor=np.flatnonzero(own&(f['id']==row['producer']))
    assert len(actor)==1
    i=actor[0]; state=row['after']
    assert state['flying']==bool(f['is_flying'][i])
    candidates=np.flatnonzero(own&np.isin(f['unitType'],addon_types))
    offset=f['pos'][i,:2]+np.array([2.5,-.5])
    candidates=[j for j in candidates if not f['is_flying'][i]
                and np.linalg.norm(f['pos'][j,:2]-offset)<.1]
    assert len(candidates)<=1
    expected=int(f['id'][candidates[0]]) if candidates else None
    assert expected==state['geometric_addon']
    if candidates:
        assert state['addon_complete']==bool(f['build_progress'][candidates[0]]>=1)
    checks+=1
for t in report['transitions']:
    addon=t['after']['geometric_addon']
    if addon: transfers.setdefault(addon,set()).add(t['producer'])
shared={str(a):sorted(tags) for a,tags in transfers.items() if len(tags)>1}
assert len(shared)==5
for source,sha in report['bindings'].items():
    source=Path(source)
    if source==Path('/tmp/sc2-audit-addon-topology.py'): source=root/'audit_source.py'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
result=dict(status='verified_observed_geometry_only',checked_rows=checks,
            shared_addons=shared,training=False,rl=False,
            audit_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            limitations=report['limitations'])
(root/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
(root/'verify_source.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(result,indent=2))
