"""Independently check depleted-home recovery against raw native observations."""
import hashlib,json,math
from pathlib import Path
from src.learning.replay_extract import replay_metadata
ROOT=Path('logs/roadmap/depleted-mining-fixture-01')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 report=json.loads((ROOT/'report.json').read_text());assert report['status']=='completed'
 for p,h in report['bindings'].items():
  source=Path(p);assert sha(source)==h
  rel=source.relative_to(Path.cwd()) if source.is_absolute() else source
  dest=ROOT/'source-snapshot'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes())
 rows=[json.loads(s) for s in (ROOT/'trace.jsonl').read_text().splitlines()];home=json.loads((ROOT/'static.json').read_text())['home'];remote_orders=0;depleted=None
 for row in rows:
  state=row['observation'];assert not state['action_errors'] and all(code==1 for code in row['results'])
  home_remaining=any(u['alliance']==3 and u.get('mineral_contents',0)>0 and math.dist(u['position'][:2],home)<10 for u in state['units'])
  if home_remaining:
   assert depleted is None and state['game_loop']<=8
   continue
  if depleted is None:depleted=row
  own=[u for u in state['units'] if u['alliance']==1];assert sum(u['unit_type'] in (18,130,132) for u in own)==1
  targets={u['tag']:u for u in state['units'] if u['alliance']==3 and u.get('mineral_contents',0)>0 and math.dist(u['position'][:2],home)>10}
  for cmd in row['commands']:
   assert cmd['ability']==295 and cmd['target_unit'] in targets
  remote_orders+=sum(any(o.get('target_unit_tag') in targets for o in u.get('orders',[])) for u in own if u['unit_type']==45)
 income=rows[-1]['score']['score_details']['collected_minerals']-depleted['score']['score_details']['collected_minerals']
 assert income>0 and remote_orders>0
 metadata,_=replay_metadata(ROOT/'game.SC2Replay');assert metadata['BaseBuild']=='Base75689'
 out=dict(status='verified_native_depleted_home_remote_mining',remote_order_observations=remote_orders,collected_minerals=income,action_errors=0,normal_cutoff=True,replay_saved=True,wall_seconds=report['results'][0]['wall_seconds'],peak_cpu=report['peak_cpu'],training=False,rl=False,limitations=['Debug killed home mineral patches and created one extra remote SCV for visibility. No resource boost or remote base.','Engineering recovery only; no learned macro strength or win established.'],bindings={str(p):sha(p) for p in [Path(__file__),ROOT/'report.json',ROOT/'trace.jsonl',ROOT/'static.json',ROOT/'game.SC2Replay']})
 (ROOT/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
