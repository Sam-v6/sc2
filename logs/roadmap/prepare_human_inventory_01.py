"""Verified source inventory reconstruction; current features unchanged, no fit/RL."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
import mpyq
import numpy as np
from src.learning.production_inventory import Inventory, stock_aliases, stock_counts
from src.learning.replay_extract import load_protocol, replay_metadata

ROOT=Path('logs/roadmap'); SOURCE=ROOT/'human-production-goals-02'; OUT=ROOT/'human-inventory-targets-01'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=False)
    original=json.loads((SOURCE/'preparation.json').read_text())
    intake=json.loads((ROOT/'human-visibility-reimport-01/verification.json').read_text())
    assert original['status']=='verified_preparation' and intake['status']=='verified_reimport'
    for receipt in (original,intake):
        for path,checksum in receipt['bindings'].items(): assert sha(path)==checksum,path
    names=original['names']
    refs={role:json.loads((SOURCE/f'{role}-rows.json').read_text()) for role in ('teaching','development')}
    bindings={str(p):sha(p) for p in [Path(__file__),Path('src/learning/production_inventory.py'),Path('docs/superpowers/plans/2026-10-06-human-inventory-targets.md'),SOURCE/'preparation.json',ROOT/'human-visibility-reimport-01/verification.json']}
    paths={Path(s['new']).name:Path(s['new']) for s in intake['sources']}
    labels, observed, coverage={}, {}, []
    for game,directory in paths.items():
        receipt=json.loads((directory/'dataset.json').read_text())
        data=json.loads((directory/'static.json').read_text())['game_data']
        aliases=stock_aliases(data)
        unit_names={u['unit_id']:u['name'] for u in data['units']}
        upgrade_names={u['upgrade_id']:u['name'] for u in data['upgrades']}
        with gzip.open(directory/'examples.jsonl.gz','rt') as stream: rows=list(map(json.loads,stream))
        metadata,_=replay_metadata(receipt['source_replay'])
        archive=mpyq.MPQArchive(receipt['source_replay'])
        decoder=load_protocol(int(metadata['BaseBuild'][4:]))
        events=list(decoder.decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
        assert all(a['_gameloop']<=b['_gameloop'] for a,b in zip(events,events[1:]))
        selected=[r for role in refs.values() for r in role if r['game']==game]
        query=sorted({t for r in selected for t in (r['loop'],r['loop']+1008)})
        tracker=Inventory(receipt['player']['player_info']['player_id'],aliases)
        position=0; snapshots={}
        for loop in query:
            while position<len(events) and events[position]['_gameloop']<=loop:
                tracker.apply(events[position]);position+=1
            snapshots[loop]=tracker.counts()
        mismatches=[]
        for ref in selected:
            row=rows[ref['row']]; loop=ref['loop']
            assert row['action_loop']==loop and row['observation']['game_loop']==loop
            state=row['observation']
            stock=stock_counts([unit_names[u['unit_type']] for u in state['units'] if u['alliance']==1],
                               [upgrade_names[u] for u in state['upgrades']],aliases)
            expected={n:snapshots[loop].get(n,0) for n in names}
            actual={n:stock.get(n,0) for n in names}
            if actual!=expected:
                mismatches.append(dict(row=ref['row'],loop=loop,differences={n:[actual[n],expected[n]] for n in names if actual[n]!=expected[n]}))
            key=(game,ref['row'])
            observed[key]=actual
            labels[key]={n:snapshots[loop+1008].get(n,0) for n in names}
        coverage.append(dict(game=game,rows=len(selected),current_exact=len(selected)-len(mismatches),current_mismatches=mismatches,aliases=aliases))
        bindings.update({str(p):sha(p) for p in [directory/'dataset.json',directory/'static.json',directory/'examples.jsonl.gz',Path(receipt['source_replay'])]})
        print(json.dumps(dict(game=game,rows=len(selected),current_exact=len(selected)-len(mismatches))),flush=True)
    for role,rows in refs.items():
        np.save(OUT/f'{role}-inventory.npy',np.array([[labels[(r['game'],r['row'])][n] for n in names] for r in rows],dtype=np.int32))
        np.save(OUT/f'{role}-current.npy',np.array([[observed[(r['game'],r['row'])][n] for n in names] for r in rows],dtype=np.int32))
        (OUT/f'{role}-rows.json').write_text(json.dumps(rows)+'\n')
        bindings[str(SOURCE/f'{role}-state.npz')]=sha(SOURCE/f'{role}-state.npz')
        bindings[str(SOURCE/f'{role}-rows.json')]=sha(SOURCE/f'{role}-rows.json')
    for path,checksum in bindings.items(): assert sha(path)==checksum,path
    report=dict(status='prepared_inventory_labels',names=names,horizon_loops=1008,feature_source=str(SOURCE),coverage=coverage,bindings=bindings,rl=False)
    (OUT/'preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],rows={r:len(v) for r,v in refs.items()},current_exact=sum(g['current_exact'] for g in coverage))),flush=True)
if __name__=='__main__': main()
