"""Audit terminal games only; never read a still-running race trace."""
import gzip,hashlib,json,math
from collections import Counter
from pathlib import Path
from src.learning.replay_extract import replay_metadata
ROOT=Path('logs/roadmap/reserved-choice-competence-06')
def main():
 contract=json.loads((ROOT/'contract.json').read_text())
 for p,h in contract['bindings'].items():
  source=Path(p);rel=source.relative_to(Path.cwd()) if source.is_absolute() else source
  assert hashlib.sha256((ROOT/'source-snapshot'/rel).read_bytes()).hexdigest()==h,p
 progress=json.loads((ROOT/'report.json' if (ROOT/'report.json').exists() else ROOT/'progress.json').read_text());games=[]
 for result in progress['results']:
  race=result['race'];directory=ROOT/race;receipt=result['receipt']
  if receipt['status'] not in ('completed','truncated'):continue
  assert (directory/'episode.json').exists() and (directory/'game.SC2Replay').exists()
  metadata,_=replay_metadata(directory/'game.SC2Replay');assert metadata['BaseBuild']=='Base75689'
  accepts=Counter();errors=set();first=None;last=None;remote=0;frames=0;idle=0;bases={};peak_workers=0
  with gzip.open(directory/'trace.jsonl.gz','rt') as f:
   for line in f:
    row=json.loads(line);s=row.get('observation',{})
    for e in s.get('action_errors',[]):errors.add((s['game_loop'],e['unit_tag'],e['ability_id'],e['result']))
    if row.get('phase')!='production_choice':continue
    frames+=1;last=row
    if first is None:first=row
    own=[u for u in s['units'] if u['alliance']==1];townhalls=[u for u in own if u['unit_type'] in (18,130,132) and not u.get('is_flying') and u.get('build_progress',1)>=1]
    visible={u['tag']:u for u in s['units'] if u['alliance']==3 and u.get('mineral_contents',0)>0}
    remote_targets={tag for tag,u in visible.items() if not any(math.dist(u['position'][:2],b['position'][:2])<10 for b in townhalls)}
    remote+=sum(any(o.get('target_unit_tag') in remote_targets for o in u.get('orders',[])) for u in own if u['unit_type']==45)
    peak_workers=max(peak_workers,s['player']['food_workers']);idle+=s['player']['idle_worker_count']==0
    for b in townhalls:bases[b['tag']]=dict(position=b['position'][:2],max_ideal=max(b.get('ideal_harvesters',0),bases.get(b['tag'],{}).get('max_ideal',0)))
    cmd=row['choice'].get('accepted_pending')
    if cmd:accepts[cmd['ability']]+=1
  # Income is from the ordinary final observation phase, not unit counts.
  final=None
  with gzip.open(directory/'trace.jsonl.gz','rt') as f:
   for line in f:
    row=json.loads(line)
    if 'score' in row:final=row
  games.append(dict(race=race,receipt_status=receipt['status'],result=receipt['result'],wall_seconds=receipt['wall_seconds'],normal_native_cutoff=receipt['status']=='truncated' and receipt['result']=='Tie',actual_victory=receipt['result']=='Victory',observed_action_errors=sorted(errors),frames=frames,zero_idle_worker_frames=idle,remote_mineral_order_observations=remote,peak_workers=peak_workers,last_player=last['observation']['player'],completed_base_locations=list(bases.values()),accepted_abilities=dict(accepts),saved_replay=True))
 out=dict(status='audited_terminal_games',games=games,all_race_victory_gate_pass=len(games)==3 and all(g['actual_victory'] and not g['observed_action_errors'] for g in games),training=False,rl=False,live_panel='report.json absent' if not (ROOT/'report.json').exists() else False,limitations=['Frozen conditional-production checkpoint with scripted timing, actor/placement and primitives; bootstrap policy filename does not identify actual choice model.','Cutoffs are not victories. No Hard or broad imitation success inferred.'],choice_checkpoint=contract['choice_checkpoint'])
 (ROOT/'terminal-game-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
