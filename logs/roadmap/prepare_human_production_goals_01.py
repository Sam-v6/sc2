"""Verified replay outcomes as simultaneous supervised labels; no fit/RL."""
from collections import Counter
import gzip, hashlib, json
from pathlib import Path
import numpy as np
import mpyq
from scipy.sparse import csr_matrix, hstack, vstack, save_npz
from src.learning.entity_train import collect, validate_datasets
from src.learning.entity_type_status import unit_type_status
from src.learning.intention_probe import probe_features
from src.learning.production_outcomes import production_outcomes, window_counts
from src.learning.replay_extract import load_protocol, replay_metadata

ROOT=Path('logs/roadmap'); OUT=ROOT/'human-production-goals-01'
TRAIN=('294','870','955','839','991','523','1038','163','1085','1032','130')
HELD=('887','920','851')
paths={g:ROOT/('pro-demonstrations-production-08' if g in TRAIN[:6] else 'pro-demonstrations-09' if g in TRAIN else 'pro-demonstrations-07')/g for g in TRAIN+HELD}
assert not (OUT/'preparation.json').exists()
intake=json.loads((ROOT/'pro-source-expansion-02/final-verification.json').read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,digest in intake['bindings'].items(): assert sha(p)==digest,p
validated=validate_datasets([paths[g] for g in TRAIN],[paths[g] for g in HELD],missing_fields=True)
counts=json.loads((ROOT/'joint-professional-fit-05/configuration.json').read_text())['vocabulary']
bindings={str(p):sha(p) for p in [Path(__file__),Path('src/learning/production_outcomes.py'),Path('docs/superpowers/plans/2026-10-06-human-production-goals.md')]}
parts={'teaching':[],'development':[]}; coverage=[]
for g,d in paths.items():
    receipt=json.loads((d/'dataset.json').read_text()); catalog=json.loads((d/'static.json').read_text())['game_data']
    bindings.update({str(p):sha(p) for p in [d/'dataset.json',d/'static.json',d/'examples.jsonl.gz',Path(receipt['source_replay'])]})
    abilities={a['ability_id']:a.get('friendly_name','') for a in catalog['abilities']}
    # AutoTurret is energy-based micro rather than mineral production despite catalogue costs.
    products={u['name'] for u in catalog['units'] if u.get('race')==1 and abilities.get(u.get('ability_id'),'').startswith(('Build ','Train ')) and u['name']!='AutoTurret'}
    conversions={'OrbitalCommand','PlanetaryFortress'}
    upgrades={u['name'] for u in catalog['upgrades'] if abilities.get(u.get('ability_id'),'').startswith('Research ')}
    meta,_=replay_metadata(receipt['source_replay']); archive=mpyq.MPQArchive(receipt['source_replay']); protocol=load_protocol(int(meta['BaseBuild'][4:]))
    events=list(protocol.decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
    player=receipt['player']['player_info']['player_id']; outcomes=production_outcomes(events,player,products,conversions,upgrades)
    with gzip.open(d/'examples.jsonl.gz','rt') as stream: rows=list(map(json.loads,stream))
    end=min(events[-1]['_gameloop'],rows[-1]['action_loop'])
    examples=collect([d],counts,spatial=True,missing_fields=True)[0]; assert len(rows)==len(examples)
    role='teaching' if g in TRAIN else 'development'; included=0; horizon=1008
    # Independent per-window original-event reconstruction, not the production_outcomes helper.
    births={}; owners={}; morphs={}; research={}
    for e in events:
        kind=e['_event'].split('.')[-1]; time=e['_gameloop']
        if kind=='SUpgradeEvent' and e['m_playerId']==player and e['m_count']>0:
            research.setdefault(e['m_upgradeTypeName'].decode(),time)
        if 'm_unitTagIndex' not in e: continue
        tag=(e['m_unitTagIndex'],e['m_unitTagRecycle'])
        if kind in ('SUnitBornEvent','SUnitInitEvent'):
            owners[tag]=e['m_upkeepPlayerId']; births.setdefault(tag,(time,e['m_unitTypeName'].decode(),owners[tag]))
        elif kind=='SUnitOwnerChangeEvent':
            owners[tag]=e['m_upkeepPlayerId']; births.setdefault(tag,(time,'CAPTURE',owners[tag]))
        elif kind=='SUnitTypeChangeEvent' and owners.get(tag)==player:
            name=e['m_unitTypeName'].decode()
            if name in conversions: morphs.setdefault((tag,name),time)
        elif kind=='SUnitDiedEvent': owners.pop(tag,None)
    independent=[(t,'unit:'+n) for t,n,p in births.values() if t>0 and p==player and n in products]
    independent += [(t,'unit:'+n) for (_,n),t in morphs.items() if t>0]
    independent += [(t,'upgrade:'+n) for n,t in research.items() if t>0 and n in upgrades]
    assert sorted(independent)==sorted(outcomes),(g,'chronology')
    own_names=Counter(e['m_unitTypeName'].decode() for e in events if e['_event'].endswith(('SUnitBornEvent','SUnitInitEvent')) and e['m_upkeepPlayerId']==player)
    for i,(r,(inputs,_,_,_)) in enumerate(zip(rows,examples,strict=True)):
        loop=r['action_loop']
        if loop+horizon>end: continue
        target=window_counts(outcomes,loop,horizon)
        expected=dict(Counter(name for t,name in independent if loop<=t<loop+horizon)); assert target==expected
        state,_=probe_features(inputs,*counts[:2]); state=hstack([state,csr_matrix(unit_type_status(inputs,counts[0]).reshape(1,-1))]).tocsr()
        parts[role].append((state,target,dict(game=g,row=i,loop=loop))); included+=1
    item=dict(game=g,role=role,rows=len(rows),included=included,end_loop=end,outcomes=dict(Counter(n for _,n in outcomes)),excluded_birth_names={n:c for n,c in own_names.items() if n not in products})
    coverage.append(item); print(json.dumps(dict(game=g,role=role,included=included,outcomes=len(outcomes))),flush=True)
    (OUT/f'{g}-outcomes.json').write_text(json.dumps(outcomes)+'\n')
names=sorted({n for _,target,_ in parts['teaching'] for n in target})
unknown_development=Counter(n for _,target,_ in parts['development'] for n in target if n not in names)
for role,items in parts.items():
    save_npz(OUT/f'{role}-state.npz',vstack([x[0] for x in items]).tocsr())
    np.save(OUT/f'{role}-counts.npy',np.array([[target.get(n,0) for n in names] for _,target,_ in items]))
    (OUT/f'{role}-rows.json').write_text(json.dumps([x[2] for x in items])+'\n')
for p,digest in bindings.items(): assert sha(p)==digest,p
report=dict(status='verified_preparation',rl=False,horizon_loops=1008,loops_per_second=22.4,names=names,coverage=coverage,unknown_development=dict(unknown_development),bindings=bindings,validated=validated)
(OUT/'preparation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],families=len(names),rows={r:len(x) for r,x in parts.items()},unknown_development=dict(unknown_development))),flush=True)
