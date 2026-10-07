"""Independent per-event inventory deltas/prefix sums; no production helper."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
import mpyq
import numpy as np
from src.learning.replay_extract import load_protocol,replay_metadata

ROOT=Path('logs/roadmap'); OUT=ROOT/'human-inventory-targets-03'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((OUT/'preparation.json').read_text())
assert prep['status']=='prepared_inventory_labels'
for path,checksum in prep['bindings'].items():assert sha(path)==checksum,path
intake=json.loads((ROOT/'human-visibility-reimport-01/verification.json').read_text())
paths={Path(s['new']).name:Path(s['new']) for s in intake['sources']}
names=prep['names'];index={n:i for i,n in enumerate(names)}
refs={role:json.loads((OUT/f'{role}-rows.json').read_text()) for role in ('teaching','development')}
actual={role:np.load(OUT/f'{role}-inventory.npy') for role in refs}
current={role:np.load(OUT/f'{role}-current.npy') for role in refs}
verified=0;parity=0;remaining=[];boundary_compatible=0
for game,directory in paths.items():
    receipt=json.loads((directory/'dataset.json').read_text());data=json.loads((directory/'static.json').read_text())['game_data']
    by_id={u['unit_id']:u for u in data['units']};alias={}
    for row in data['units']:
        parent=row
        while parent.get('unit_alias'):parent=by_id[parent['unit_alias']]
        alias[row['name']]=parent['name']
    if 'HellionTank' in alias:alias['HellionTank']='Hellion'
    def contribution(item):
        counts=Counter()
        if item and item[1]==receipt['player']['player_info']['player_id']:
            name=alias.get(item[0],item[0]);counts['unit:'+name]+=1
            if name in ('OrbitalCommand','PlanetaryFortress'):counts['unit:CommandCenter']+=1
        return counts
    with gzip.open(directory/'examples.jsonl.gz','rt') as stream: observations=list(map(json.loads,stream))
    upgrade_names={u['upgrade_id']:u['name'] for u in data['upgrades']}
    metadata,_=replay_metadata(receipt['source_replay']);archive=mpyq.MPQArchive(receipt['source_replay']);decoder=load_protocol(int(metadata['BaseBuild'][4:]))
    events=list(decoder.decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
    times=[];deltas=[];units={};upgrades=set()
    for e in events:
        change=Counter();kind=e['_event'].rsplit('.',1)[-1]
        if 'm_unitTagIndex' in e:
            tag=(e['m_unitTagIndex'],e['m_unitTagRecycle']);before=units.get(tag)
            if kind in ('SUnitInitEvent','SUnitBornEvent'):units[tag]=(e['m_unitTypeName'].decode(),e['m_upkeepPlayerId'])
            elif kind=='SUnitTypeChangeEvent':units[tag]=(e['m_unitTypeName'].decode(),before[1])
            elif kind=='SUnitOwnerChangeEvent':units[tag]=(before[0],e['m_upkeepPlayerId'])
            elif kind=='SUnitDiedEvent':units.pop(tag)
            change.update(contribution(units.get(tag)));change.subtract(contribution(before))
        if kind=='SUpgradeEvent' and e['m_playerId']==receipt['player']['player_info']['player_id'] and e['m_count']>0:
            name='upgrade:'+e['m_upgradeTypeName'].decode()
            if name not in upgrades:change[name]+=1;upgrades.add(name)
        times.append(e['_gameloop']);deltas.append([change[n] for n in names])
    prefix=np.vstack([np.zeros(len(names),dtype=np.int32),np.cumsum(np.asarray(deltas,dtype=np.int32),axis=0)])
    assert prefix.min()>=0
    game_verified=0;game_parity=0
    for role,rows in refs.items():
        for i,r in enumerate(rows):
            if r['game']!=game:continue
            state=observations[r['row']]['observation']
            owned={u['tag']:u for u in state.get('owned_memory',[])}
            owned.update({u['tag']:u for u in state['units'] if u['alliance']==1})
            independent_current=Counter()
            for unit in owned.values():independent_current.update(contribution((by_id[unit['unit_type']]['name'],receipt['player']['player_info']['player_id'])))
            for upgrade in state['upgrades']:independent_current['upgrade:'+upgrade_names[upgrade]]=1
            assert np.array_equal([independent_current[n] for n in names],current[role][i]),(game,r,'observed inventory')
            future=prefix[np.searchsorted(times,r['loop']+1008,side='left')]
            present=prefix[np.searchsorted(times,r['loop'],side='left')]
            assert np.array_equal(future,actual[role][i]),(game,r,'future labels')
            game_verified+=1
            if np.array_equal(present,current[role][i]):game_parity+=1
            else:
                left,right=np.searchsorted(times,r['loop'],side='left'),np.searchsorted(times,r['loop'],side='right')
                compatible=any(np.array_equal(value,current[role][i]) for value in prefix[left:right+1])
                boundary_compatible+=int(compatible)
                remaining.append(dict(game=game,row=r['row'],loop=r['loop'],same_loop_event_prefix_compatible=compatible,differences={n:[int(current[role][i,j]),int(present[j])] for j,n in enumerate(names) if current[role][i,j]!=present[j]}))
    verified+=game_verified;parity+=game_parity
    print(json.dumps(dict(game=game,verified=game_verified,current_exact=game_parity)),flush=True)
receipt=dict(status='verified_inventory_boundary_audit',same_loop_event_prefix_compatible_rows=boundary_compatible,label_rows=verified,current_exact=parity,current_mismatches=remaining,event_boundary='strictly_before_query_loop',rl=False,
    bindings={str(p):sha(p) for p in [Path(__file__),OUT/'preparation.json',Path('src/learning/production_inventory.py')]+list(OUT.glob('*-inventory.npy'))+list(OUT.glob('*-current.npy'))+list(OUT.glob('*-rows.json'))})
(OUT/'verification-boundaries.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(status=receipt['status'],verified=verified,current_exact=parity,mismatch_rows=len(remaining))),flush=True)
