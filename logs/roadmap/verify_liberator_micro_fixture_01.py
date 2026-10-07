"""Verify real deployment, ground kills and return to flight in saved replay."""
import hashlib,json,math
from pathlib import Path
import mpyq
from src.learning.replay_extract import replay_metadata,load_protocol
ROOT=Path('logs/roadmap/liberator-micro-fixture-01')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 report=json.loads((ROOT/'report.json').read_text());assert report['status']=='completed'
 for p,h in report['bindings'].items():
  source=Path(p);assert sha(source)==h
  rel=source.relative_to(Path.cwd()) if source.is_absolute() else source;dest=ROOT/'source-snapshot'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes())
 rows=[json.loads(s) for s in (ROOT/'trace.jsonl').read_text().splitlines()];modes=[];issued=[];tank_health={};lib_tags=set()
 for row in rows:
  s=row['observation'];assert not s['action_errors'] and all(code==1 for code in row['results'])
  for u in s['units']:
   if u['alliance']==4 and u['unit_type'] in (32,33):tank_health.setdefault(u['tag'],[]).append(u['health'])
   if u['alliance']==1 and u['unit_type'] in (689,734):
    lib_tags.add(u['tag'])
    if not modes or modes[-1]!=u['unit_type']:modes.append(u['unit_type'])
  for command in row['commands']:
   if command['ability']==2558:
    unit=next(u for u in s['units'] if u['tag']==command['units'][0]);assert math.dist(unit['position'][:2],command['target_point'])<=5.001
   issued.append(command['ability'])
 assert len(lib_tags)==1 and modes==[689,734,689] and issued.count(2558)==1 and issued.count(2560)==1
 assert len(tank_health)==3 and sum(min(v)<max(v) for v in tank_health.values())==2
 metadata,_=replay_metadata(ROOT/'game.SC2Replay');assert metadata['BaseBuild']=='Base75689'
 events=list(load_protocol(75689).decode_replay_tracker_events(mpyq.MPQArchive(str(ROOT/'game.SC2Replay')).read_file('replay.tracker.events')))
 lib=next(iter(lib_tags));lib_index=(lib&((1<<32)-1))>>18;lib_recycle=lib&((1<<18)-1)
 deaths=[e for e in events if e['_event'].endswith('.SUnitDiedEvent') and ((1<<32)|(e['m_unitTagIndex']<<18)|e['m_unitTagRecycle']) in tank_health]
 assert len(deaths)==2 and all(e.get('m_killerPlayerId')==1 and e.get('m_killerUnitTagIndex')==lib_index and e.get('m_killerUnitTagRecycle')==lib_recycle for e in deaths),deaths
 out=dict(status='verified_native_liberator_ground_zone_kills_and_undeploy',modes=modes,deployment_commands=1,undeployment_commands=1,enemy_tank_kills_attributed_to_liberator=2,action_errors=0,normal_cutoff=True,replay_saved=True,wall_seconds=report['results'][0]['wall_seconds'],peak_cpu=report['peak_cpu'],training=False,rl=False,limits=['One debug-created Liberator against three debug-created initially sieged ground tanks with no anti-air; opponent AI unsieges tanks, and one leaves the zone; not a learned micro model or full-game strength test.','Other geometries, moving targets, danger and ability upgrades need separate transfer evidence.'],bindings={str(p):sha(p) for p in [Path(__file__),ROOT/'report.json',ROOT/'trace.jsonl',ROOT/'static.json',ROOT/'game.SC2Replay']})
 (ROOT/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
