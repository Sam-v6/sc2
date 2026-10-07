"""Find unresolved native production candidates before compiling a human plan."""
from pathlib import Path
from collections import Counter
import hashlib,json
from src.learning.tournament_record import decode_record
ROOT=Path('logs/roadmap/human-in-place-addon-reimport-01');OUT=Path('logs/roadmap/human-production-prefix-01');OUT.mkdir(exist_ok=True)
reconciliation=ROOT/'reconciliation.json';g=json.loads(reconciliation.read_text())['games'][0];record_path=Path('logs/roadmap/pro-preconverted-probe-01/fall-record-870.bin');record=decode_record(record_path.read_bytes());catalog_path=Path('logs/roadmap/joint-frozen-native-wait-02/static.json');catalog={a['ability_id']:a for a in json.loads(catalog_path.read_text())['game_data']['abilities']};selected={(s['loop'],s['sequence']):s['tags'] for s in g['selections']};frames={int(loop):i for i,loop in enumerate(record['steps']['game_loop'])};macro=lambda a:catalog.get(a,{}).get('friendly_name','').startswith(('Build','Train','Research','Morph','Lift','Land','Cancel'))
accepted=[a for a in g['accepted'] if a['loop']<13440 and macro(a['command']['ability'])];missing=[]
for row in g['audit']['unresolved_events']:
 event=row['event'];loop=event['_gameloop']
 if loop>=13440 or loop not in frames:continue
 selection=selected.get((loop,event['m_sequence']));actions=[]
 for command in record['actions'][frames[loop]]:
  if macro(command['ability']) and (selection is None or {tag & 0xFFFFFFFF for tag in command['units']}<=set(selection)):
   actions.append(dict(ability=command['ability'],name=catalog[command['ability']].get('friendly_name'),units=command['units'],target_type=command['target_type']))
 if actions:missing.append(dict(loop=loop,sequence=event['m_sequence'],reason=row['reason'],flags=hex(event['m_cmdFlags']),raw_ability=event['m_abil'],candidates=actions))
paths=[Path(__file__),reconciliation,record_path,catalog_path,ROOT/'verification.json']
r=dict(status='descriptive_production_prefix_coverage',seconds=600,matched_macro_commands=len(accepted),by_name=dict(Counter(catalog[a['command']['ability']].get('friendly_name') for a in accepted)),unresolved_native_macro_candidates=missing,training=False,rl=False,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},limitations=['Candidate proximity and selection are not proof of command identity.','Only existing converted source frames are screened; source gaps and excluded raw events without a frame remain unknown.','This is not an executable production plan or complete coverage claim.'])
(OUT/'audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
