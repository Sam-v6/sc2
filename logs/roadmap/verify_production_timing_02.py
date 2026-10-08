"""Independent interval accounting and source-proof validation; no fitting."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
import mpyq
from src.learning.replay_extract import load_protocol, replay_metadata

ROOT = Path('logs/roadmap/human-command-cohort-02')
OUT = Path('logs/roadmap/production-timing-audit-02')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 report=json.loads((OUT/'report.json').read_text())
 assert json.loads(Path('logs/roadmap/production-decisions-01/verification.json').read_text())['status']=='verified_causal_actual_observation_windows'
 for p,h in report['bindings'].items(): assert sha(p)==h,p
 checks=[]
 for summary in report['games']:
  parent=ROOT/summary['game']; job=json.loads((parent/'job.json').read_text()); recon=json.loads((parent/'reconciliation.json').read_text())['games'][0]
  meta,_=replay_metadata(job['replay']); protocol=load_protocol(int(meta['BaseBuild'].removeprefix('Base')))
  archive=mpyq.MPQArchive(job['replay']); raw={(e['_gameloop'],e['m_sequence']):e for e in protocol.decode_replay_game_events(archive.read_file('replay.game.events')) if e['_event'].endswith('.SCmdEvent') and e.get('_userid',{}).get('m_userId')==recon['source_user_id']}
  accepted={(r['action_loop'],r['source_sequence']):r['commands'][0]['ability'] for r in map(json.loads,gzip.open(parent/'corpus/examples.jsonl.gz','rt'))}
  data=json.loads((OUT/(summary['game']+'.json')).read_text()); events={tuple(e['key']):e for e in data['events']}
  for key,event in events.items():
   if event['proof']=='verified_command': assert accepted[key]==event['ability'];continue
   if event['classification']=='possible_production': continue
   assert key in raw
   for reference in event['reference_keys']:
    reference=tuple(reference);assert reference in accepted and reference in raw
    assert raw[key]['m_abil']==raw[reference]['m_abil'] or (raw[key]['m_abil'] is not None and raw[reference]['m_abil'] is not None and all(raw[key]['m_abil'][k]==raw[reference]['m_abil'][k] for k in ('m_abilLink','m_abilCmdIndex')))
   if event['classification']=='production':
    flags=raw[key]['m_cmdFlags']; assert flags & 0x100 and flags & ~(0x100|0x2|0x8|0x10000|0x20000)==0
  original=json.loads(Path('logs/roadmap/production-decisions-01',summary['game'],'windows.json').read_text());end=original['source_loops'][-1]
  assert len(data['labels'])==len(original['windows'])
  coverage=set();counts=Counter()
  for label,window in zip(data['labels'],original['windows'],strict=True):
   assert label['loop']==window['loop'];start=label['loop']
   interval=[e for k,e in events.items() if start<=k[0]<start+44]
   positive=sorted((e for e in interval if e['classification']=='production'),key=lambda e:e['key'])
   uncertain=[e for e in interval if e['classification']=='possible_production']
   expected=True if positive else None if uncertain or start+44>end else False
   assert label['act'] is expected
   if label['first_ability'] is not None:
    assert positive[0]['ability']==label['first_ability'] and not any(e['key']<positive[0]['key'] for e in uncertain)
   counts[str(expected)]+=1
   coverage.update(range(start,min(start+44,end)))
  assert len(coverage)==summary['covered_elapsed_loops'];assert dict(counts)==summary['counts']
  checks.append(dict(game=summary['game'],intervals=len(data['labels']),counts=dict(counts),covered_loops=len(coverage)))
 bindings={str(p):sha(p) for p in [Path(__file__),OUT/'report.json',*[OUT/(g['game']+'.json') for g in report['games']]]}
 snapshot=OUT/'source-snapshot';snapshot.mkdir()
 for p in (Path(__file__),Path('logs/roadmap/audit_production_timing_02.py')):(snapshot/p.name).write_bytes(p.read_bytes())
 (OUT/'verification.json').write_text(json.dumps(dict(status='verified_source_proofs_and_interval_accounting',games=checks,bindings=bindings),indent=2)+'\n')
 print(json.dumps(checks),flush=True)
if __name__=='__main__':main()
