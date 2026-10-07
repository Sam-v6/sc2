from pathlib import Path
import hashlib,json,mpyq
from src.learning.replay_extract import load_protocol,replay_metadata
root=Path('logs/roadmap/producer-binding-fixture-03');report=json.loads((root/'report.json').read_text())
assert report['status']=='completed' and report['peak_cpu']<=80
receipt=report['results'][0];job=receipt['job'];assert receipt['status']=='completed'
rows=[json.loads(l) for l in Path(job['trace']).read_text().splitlines()]
issued=[r for r in rows if r['commands']]
assert [r['commands'][0]['ability'] for r in issued]==[3683,452,520]
assert all(r['results']==[1] for r in issued)
assert not any(r['observation']['action_errors'] for r in rows)
bindings=rows[-1]['bindings'];b=bindings['4355784706'];f=bindings['4360503299'];a=bindings['4362600450']
assert b!=f and f!=a and b!=a
assert all(r['bindings'].get('4355784706')==b and r['bindings'].get('4360503299')==f for r in rows if r['bindings'])
lift=issued[1];actor=next(u for u in lift['observation']['units'] if u['tag']==b)
assert actor['add_on_tag']==a and not actor.get('orders')
assert any(next(u for u in r['observation']['units'] if u['tag']==b).get('is_flying') for r in rows if r['bindings'])
verified=[r for r in rows if r['phase']=='verified'];assert verified
for r in verified:
 actor=next(u for u in r['observation']['units'] if u['tag']==f)
 assert not actor.get('is_flying') and actor['add_on_tag']==a
 assert next(u for u in r['observation']['units'] if u['tag']==a)['build_progress']==1
replay=Path(job['replay']);meta,_=replay_metadata(replay);proto=load_protocol(int(meta['BaseBuild'].removeprefix('Base')))
init=proto.decode_replay_initdata(mpyq.MPQArchive(str(replay)).read_file('replay.initData'))
assert init['m_syncLobbyState']['m_userInitialData'][0]['m_randomSeed']==job['seed']
snapshot=root/'source-snapshot';snapshot.mkdir()
for p,sha in report['bindings'].items():
 source=Path(p);assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
 target=snapshot/source.name;target.write_bytes(source.read_bytes())
result=dict(status='verified_native_producer_addon_transfer',seed=job['seed'],frames=len(rows),
 accepted_commands=3,errors=0,bindings=bindings,first_verified_loop=verified[0]['loop'],
 peak_cpu=report['peak_cpu'],engineering_only=True,training=False,rl=False,
 trace_sha256=hashlib.sha256(Path(job['trace']).read_bytes()).hexdigest(),
 replay_sha256=hashlib.sha256(replay.read_bytes()).hexdigest())
(root/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
(snapshot/'verifier.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(result))
