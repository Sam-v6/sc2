"""Reconstruct scout execution effects from native player observations."""
import gzip
import hashlib
import json
from pathlib import Path
ROOT=Path('logs/roadmap/broad-scout-canary-01')
contract=json.loads((ROOT/'contract.json').read_text())
report=json.loads((ROOT/'report.json').read_text())
assert report['supervision'].get('result') == 'Tie',report
assert report['supervision']['wall_seconds'] < contract['wall_seconds']
assert report['peak_cpu'] <= 80,report['peak_cpu']
for p,h in contract['bindings'].items():
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
rows=[json.loads(line) for line in gzip.open(ROOT/'fixture.jsonl.gz','rt')]
selected=[(r,e) for r in rows for e in r['scout_events'] if e['event']=='selected']
assert len(selected)==1,len(selected)
selected_row,event=selected[0]
tag=event['tag']
accepted=[]
for row in rows:
    assert len(row['assistance'])==len(row['results'])
    assert not row['delayed_errors'],row['delayed_errors']
    assert all(code==1 for code in row['results']),row['results']
    scout_cmds=[c for c in row['assistance'] if tag in c['units']]
    assert len(scout_cmds)<=1,(row['loop'],scout_cmds)
    for c,code in zip(row['assistance'],row['results']):
        if tag in c['units'] and code==1:
            accepted.append((row['loop'],c))
returns=[(r,e) for r in rows for e in r['scout_events'] if e['event']=='return']
assert len(returns)==1,returns
return_row,returned=returns[0]
assert any(c['ability']==16 for loop,c in accepted)
assert any(loop==return_row['loop'] and c['ability']==295 for loop,c in accepted)
active=[r for r in rows if selected_row['loop'] <= r['loop'] <= return_row['loop']]
assert all(tag in r['scout_protected'] for r in active)
mining=[r for r in rows if r['loop']>return_row['loop'] and any(
    u['tag']==tag and any(o['ability_id'] in (295,3666,296,3667) for o in u['orders'])
    for u in r['observation']['units'] if u['alliance']==1)]
assert mining,'No observed scout mining after return'
assert rows[-1]['collected_minerals']>selected_row['collected_minerals']
replay=ROOT/'game.SC2Replay'
assert replay.stat().st_size>0
result=dict(status='verified_native_scout_adapter_execution',tag=tag,
    selected_loop=selected_row['loop'],return_loop=return_row['loop'],
    return_reason=returned['reason'],observed_mining_loop=mining[0]['loop'],
    protected_observations=len(active),accepted_scout_commands=len(accepted),
    collected_minerals=rows[-1]['collected_minerals'],peak_cpu=report['peak_cpu'],
    replay_sha256=hashlib.sha256(replay.read_bytes()).hexdigest(),
    scripted_production_fixture=True,learned_competence=False,training=False,rl=False)
(ROOT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
