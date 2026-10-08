"""Measure observed SCV mineral/gas switches and short return trips."""
import gzip,hashlib,json
from pathlib import Path
root=Path('logs/roadmap');out=root/'gas-reassignment-25';out.mkdir(exist_ok=False);trace=root/'fixed-human-plan-native-25/episode/trace.jsonl.gz';rows=[json.loads(line) for line in gzip.open(trace,'rt')];kind={};last={};switches=[];samples=[]
for row in rows:
 loop=row['loop'];obs=row['observation'];kind.update({u['tag']:'gas' if u['unit_type']==20 else 'mineral' for u in obs['units'] if u['unit_type']==20 or u.get('mineral_contents',0)>0})
 for c in row.get('commands',[]):
  if c['ability']!=295 or c.get('target_unit') not in kind:continue
  target=kind[c['target_unit']]
  for tag in c['units']:
   previous=last.get(tag)
   if previous and previous['kind']!=target:switches.append(dict(loop=loop,worker=tag,before=previous['kind'],after=target,previous_loop=previous['loop'],gap_loops=loop-previous['loop']))
   last[tag]=dict(loop=loop,kind=target)
 if 9000<=loop<=10552 and loop%24==0:
  samples.append(dict(loop=loop,minerals=obs['player']['minerals'],gas=obs['player']['vespene'],gas_quota=0 if obs['player']['vespene']>400 and obs['player']['minerals']<200 else 3*sum(u['alliance']==1 and u['unit_type']==20 and u['build_progress']==1 for u in obs['units']),assigned_gas=sum(u.get('assigned_harvesters',0) for u in obs['units'] if u['alliance']==1 and u['unit_type']==20)))
late=[x for x in switches if 9000<=x['loop']<=10552];fast=[x for x in late if x['gap_loops']<=224];quota_changes=[dict(before=a,after=b) for a,b in zip(samples,samples[1:]) if a['gas_quota']!=b['gas_quota']]
result=dict(status='measured_resource_reassignment',late_switches=len(late),late_fast_switches=len(fast),late_fast_unique_workers=len({x['worker'] for x in fast}),late_quota_changes=len(quota_changes),switches=switches,samples=samples,quota_changes=quota_changes,limitations=['Observed command-category changes are not proof of lost income; resource stock changes can legitimately change assignment. Gap measures previous mining command, not time inside a refinery.'],training=False,rl=False,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),trace)})
(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');(out/'auditor.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({k:v for k,v in result.items() if k not in ('bindings','switches','samples','quota_changes')}));print('quota changes',[(x['after']['loop'],x['after']['gas_quota']) for x in quota_changes])
