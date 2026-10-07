"""Verify dense cadence, source ownership, action preservation and current fog."""
import base64,gzip,hashlib,json
from pathlib import Path
ROOT=Path('logs/roadmap');OUT=ROOT/'human-rom-dense-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return list(map(json.loads,gzip.open(p,'rt')))
def visible(s,u):
 g=s['map']['visibility'];x=round(u['position'][0]);y=round(u['position'][1]);data=base64.b64decode(g['data']);assert g['bits_per_pixel']==8
 return 0<=x<g['width'] and 0<=y<g['height'] and data[y*g['width']+x]==2

def main():
 guard=json.loads((ROOT/'human-rom-dense-01.guard.json').read_text());receipt=json.loads((OUT/'dataset.json').read_text());assert guard['status']==receipt['status']=='completed'
 for p,h in guard['bindings'].items():assert sha(p)==h,p
 assert sha(receipt['replay'])==receipt['sha256'];assert receipt['disable_fog'] is False
 new=read(OUT/'examples.jsonl.gz');old=read(ROOT/'human-51482-rom-01/examples.jsonl.gz');states=read(OUT/'observations.jsonl.gz')
 assert len(new)==len(old)==299;removed=0
 for a,b in zip(new,old,strict=True):
  for key in ('action_loop','received_loop','commands','next_action_delay'):assert a[key]==b[key]
  x=a['observation'];y=b['observation'];assert x['player']==y['player']
  own=lambda s:{u['tag']:u for u in s['units'] if u['alliance']==1}
  assert own(x)==own(y)
  current={u['tag']:u for u in x['units']};previous={u['tag']:u for u in y['units']}
  assert not current.keys()-previous.keys()
  for tag,u in current.items():assert u==previous[tag]
  for tag in previous.keys()-current.keys():assert previous[tag]['alliance']==4 and not visible(x,previous[tag]);removed+=1
 for s in states:
  for command in s['recent_commands']:
   assert command['game_loop'] < s['game_loop']
   assert any(command['game_loop']==r['action_loop'] and {k:v for k,v in command.items() if k!='game_loop'} in r['commands'] for r in new)
  for u in s['units']:
   if u['alliance']==4:assert visible(s,u)
 assert [s['game_loop'] for s in states]==list(range(0,receipt['last_loop']+1,44))
 assert receipt['counts']['observations']==receipt['last_loop']+1==5244
 assert receipt['recorded_observations']==len(states)==120
 for p,h in guard['bindings'].items():assert sha(p)==h,p
 bindings={str(p):sha(p) for p in [Path(__file__),OUT/'dataset.json',OUT/'examples.jsonl.gz',OUT/'observations.jsonl.gz',OUT/'static.json',ROOT/'human-rom-dense-01.guard.json',ROOT/'human-51482-rom-01/examples.jsonl.gz']}
 result=dict(status='verified_dense_cadence_native_action_preservation_and_current_fog',bindings=bindings,consecutive_native_observations=5244,retained_current_states=120,maximum_retained_gap=44,covered_elapsed_loops=5236,total_elapsed_loops=5243,unsupported_tail_loops=7,old_current_enemy_removals=removed,commands_preserved=299,player_and_owned_command_states_preserved=299,role='reused_diagnostic',teacher='Masters; not verified professional',limitations=['Cadence audit does not establish professional transfer or cross-game timing calibration.','Original issued-command matcher uses target/queue alignment; production-specific labels require stronger independent ability identity proof.','Quiet-state fog check verifies current enemies against their native grid, not every historical memory update.'])
 (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');snapshot=OUT/'source-snapshot';snapshot.mkdir()
 for p in [Path(__file__),Path('logs/roadmap/run_dense_rom_01.py'),Path('src/learning/replay_extract.py'),Path('src/learning/demonstrations.py'),Path('src/learning/gameplay.py')]:
  dest=snapshot/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 print(json.dumps({k:v for k,v in result.items() if k!='bindings'}),flush=True)
if __name__=='__main__':main()
