"""Check real blocked-pad withholding, Marine clearance and Reactor attachment."""
import hashlib,json,math
from pathlib import Path
import mpyq
from src.learning.replay_extract import replay_metadata,load_protocol
ROOT=Path('logs/roadmap/occupied-addon-fixture-01')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 report=json.loads((ROOT/'report.json').read_text());assert report['status']=='completed'
 for p,h in report['bindings'].items():
  source=Path(p);assert sha(source)==h;rel=source.relative_to(Path.cwd()) if source.is_absolute() else source;dest=ROOT/'source-snapshot'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes())
 rows=[json.loads(s) for s in (ROOT/'trace.jsonl').read_text().splitlines()];blocked=0;issued=0;moves=0;completed=None
 for row in rows:
  s=row['observation'];assert not s['action_errors'] and all(c==1 for c in row['results']+row['assistance_results'])
  for t in row['placement']:
   if t.get('rejected')=='occupied_addon_pad':
    blocked+=1;assert not row['commands'];assert all(next(u for u in s['units'] if u['tag']==tag)['unit_type']==48 for tag in t['blocking_units'])
  for c in row['commands']:
   issued+=1;assert c['ability']==3683
  moves+=sum(c['ability']==16 for c in row['assistance'])
  if row['completed']:
   addon=next(u for u in s['units'] if u['unit_type']==38 and u['alliance']==1 and u.get('build_progress',1)>=1)
   assert any(u.get('add_on_tag')==addon['tag'] for u in s['units'] if u['alliance']==1 and u['unit_type']==21);completed=addon
 assert blocked>0 and moves>0 and issued==1 and completed
 metadata,_=replay_metadata(ROOT/'game.SC2Replay');assert metadata['BaseBuild']=='Base75689'
 events=list(load_protocol(75689).decode_replay_tracker_events(mpyq.MPQArchive(str(ROOT/'game.SC2Replay')).read_file('replay.tracker.events')))
 starts={(e['m_unitTagIndex'],e['m_unitTagRecycle']) for e in events if e['_event'].endswith('.SUnitInitEvent') and e.get('m_unitTypeName')==b'BarracksReactor' and e.get('m_controlPlayerId')==1};done={(e['m_unitTagIndex'],e['m_unitTagRecycle']) for e in events if e['_event'].endswith('.SUnitDoneEvent')};assert len(starts)==1 and starts<=done
 out=dict(status='verified_native_occupied_addon_pad_clearance_and_completion',withheld_frames=blocked,clearance_moves=moves,reactors_started_and_completed=1,attached=True,action_errors=0,normal_cutoff=True,replay_saved=True,wall_seconds=report['results'][0]['wall_seconds'],peak_cpu=report['peak_cpu'],training=False,rl=False,limits=['Debug completed Barracks and Marine on pad plus resources; native addon construction and unit movement.','Not learned macro strength or full-game transfer.'],bindings={str(p):sha(p) for p in [Path(__file__),ROOT/'report.json',ROOT/'trace.jsonl',ROOT/'static.json',ROOT/'game.SC2Replay']})
 (ROOT/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
