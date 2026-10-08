"""Recheck original tracker chronology after initial conversion bug repair."""
import hashlib,json
from pathlib import Path
import mpyq
from src.learning.replay_extract import replay_metadata,load_protocol
from src.learning.production_outcomes import production_outcomes
OUT=Path('logs/roadmap/human-production-goals-01'); prep=json.loads((OUT/'preparation.json').read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,digest in prep['bindings'].items():
    if p!='src/learning/production_outcomes.py': assert sha(p)==digest,p
checked=[]
for g in prep['coverage']:
    idx=g['game']; directory=next(Path(p).parent for p in prep['bindings'] if p.endswith(f'/{idx}/dataset.json'))
    r=json.loads((directory/'dataset.json').read_text()); s=json.loads((directory/'static.json').read_text())['game_data']; a={x['ability_id']:x.get('friendly_name','') for x in s['abilities']}
    products={u['name'] for u in s['units'] if u.get('race')==1 and a.get(u.get('ability_id'),'').startswith(('Build ','Train ')) and u['name']!='AutoTurret'}
    upgrades={u['name'] for u in s['upgrades'] if a.get(u.get('ability_id'),'').startswith('Research ')}
    meta,_=replay_metadata(r['source_replay']); ar=mpyq.MPQArchive(r['source_replay']); events=list(load_protocol(int(meta['BaseBuild'][4:])).decode_replay_tracker_events(ar.read_file('replay.tracker.events')))
    labels=production_outcomes(events,r['player']['player_info']['player_id'],products,{'OrbitalCommand','PlanetaryFortress'},upgrades)
    assert [list(x) for x in labels]==json.loads((OUT/f'{idx}-outcomes.json').read_text()),idx
    checked.append(idx)
report=dict(status='verified',preparation_sha256=sha(OUT/'preparation.json'),current_labeler_sha256=sha('src/learning/production_outcomes.py'),original_labeler_sha256=prep['bindings']['src/learning/production_outcomes.py'],unchanged_game_labels=checked)
(OUT/'label-reaudit.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report))
