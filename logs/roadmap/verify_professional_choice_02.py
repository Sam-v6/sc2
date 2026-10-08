"""Independently check one-to-one source-event identity and current observations."""
import gzip,hashlib,json
from pathlib import Path
ROOT=Path('logs/roadmap/human-command-cohort-02');OUT=Path('logs/roadmap/professional-production-choice-02')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return list(map(json.loads,gzip.open(p,'rt')))
def main():
 report=json.loads((OUT/'report.json').read_text())
 for p,h in report['bindings'].items():assert sha(p)==h,p
 checks=[];seen=set()
 for game in report['games']:
  parent=Path(game['source_cohort'])/game['game'];job=json.loads((parent/'job.json').read_text());data=json.loads(Path(job['catalog']).read_text())['game_data'];names={a['ability_id']:a.get('friendly_name','') for a in data['abilities']}
  source=read(parent/'corpus/examples.jsonl.gz');expected={}
  for row in source:
   command=row['commands'][0];name=names[command['ability']]
   if name.startswith(('Build ','Train ','Research ')) or name in ('Morph OrbitalCommand','Morph PlanetaryFortress'):expected[(row['action_loop'],row['source_sequence'])]=row
  actual=read(OUT/game['game']/'examples.jsonl.gz');assert len(actual)==len(expected)==game['events']
  for example in actual:
   key=tuple(example['label']['source_key']);identity=(game['game'],*key);assert identity not in seen;seen.add(identity);original=expected[key]
   assert example['observation']==dict(original['observation'],recent_commands=[])
   assert example['label']['command']==original['commands'][0]
   assert example['label']['ability']==original['commands'][0]['ability']
   assert example['source_game']==game['game']
  checks.append(dict(game=game['game'],role=game['role'],verified_events=len(actual)))
 assert len(seen)==2462
 for p,h in report['bindings'].items():assert sha(p)==h,p
 bindings={str(p):sha(p) for p in [Path(__file__),OUT/'report.json']}
 (OUT/'verification.json').write_text(json.dumps(dict(status='verified_distinct_source_choices_and_current_observations',games=checks,bindings=bindings),indent=2)+'\n')
 snapshot=OUT/'source-snapshot';snapshot.mkdir()
 for p in (Path(__file__),Path('logs/roadmap/prepare_professional_choice_02.py')):(snapshot/p.name).write_bytes(p.read_bytes())
 print(json.dumps(checks),flush=True)
if __name__=='__main__':main()
