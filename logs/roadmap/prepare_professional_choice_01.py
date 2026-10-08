"""One verified production event per example; no future-window duplication."""
import gzip,hashlib,json
from collections import Counter
from pathlib import Path
ROOT=Path('logs/roadmap/human-command-cohort-02');OUT=Path('logs/roadmap/professional-production-choice-01')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 verified=json.loads((ROOT/'verification.json').read_text());assert verified['status']=='verified_existing_command_cohort_expansion'
 for p,h in verified['bindings'].items():assert sha(p)==h,p
 manifest=json.loads((ROOT/'manifest.json').read_text());OUT.mkdir(exist_ok=False);bindings={str(Path(__file__)):sha(__file__),str(ROOT/'verification.json'):sha(ROOT/'verification.json'),str(ROOT/'manifest.json'):sha(ROOT/'manifest.json')};games=[];identities=set()
 for game in manifest['games']:
  parent=ROOT/game['game'];job=json.loads((parent/'job.json').read_text());receipt=json.loads((parent/'corpus/dataset.json').read_text());data=json.loads(Path(job['catalog']).read_text())['game_data'];names={a['ability_id']:a.get('friendly_name','') for a in data['abilities']};folder=OUT/game['game'];folder.mkdir();counts=Counter();source_keys=[]
  with gzip.open(parent/'corpus/examples.jsonl.gz','rt') as original,gzip.open(folder/'examples.jsonl.gz','xt') as out:
   for line in original:
    row=json.loads(line);assert len(row['commands'])==1;command=row['commands'][0];name=names[command['ability']]
    if not(name.startswith(('Build ','Train ','Research ')) or name in ('Morph OrbitalCommand','Morph PlanetaryFortress')):continue
    key=(row['action_loop'],row['source_sequence']);identity=(game['game'],*key);assert identity not in identities;identities.add(identity);source_keys.append(key);counts[name]+=1
    assert row['observation']['game_loop']==row['action_loop']
    example=dict(observation=dict(row['observation'],recent_commands=[]),label=dict(ability=command['ability'],source_key=key,command=command),source_game=game['game'])
    out.write(json.dumps(example,separators=(',',':'))+'\n')
  item=dict(game=game['game'],role=game['role'],human_result_code=game['human_result_code'],events=len(source_keys),counts=dict(counts),source_keys=source_keys);games.append(item);print(json.dumps({k:v for k,v in item.items() if k not in ('counts','source_keys')}),flush=True)
  for p in [parent/'corpus/dataset.json',parent/'corpus/examples.jsonl.gz',Path(job['catalog']),folder/'examples.jsonl.gz']:bindings[str(p)]=sha(p)
 assert sum(g['events'] for g in games if g['role']=='teaching')==1267
 assert sum(g['events'] for g in games if g['role']=='diagnostic')==289
 for p,h in verified['bindings'].items():assert sha(p)==h,p
 (OUT/'report.json').write_text(json.dumps(dict(status='prepared_distinct_professional_production_choices',games=games,bindings=bindings,training=False,rl=False,limits=['Each verified source event appears once; no future-window examples.','Partial-source current observation is pre-effect at issue loop; no future actors or targets used as inputs.','Original command arguments remain label-only; fitting is conditional ability choice, not complete raw execution.','Source-backed manager repetitions retained with distinct event keys; not necessarily independent human strategic decisions.','Six teaching games include two human losses; three diagnostics reused; reserved games unchanged.']),indent=2)+'\n')
if __name__=='__main__':main()
