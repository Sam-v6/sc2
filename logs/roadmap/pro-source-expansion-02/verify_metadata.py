"""Reconstruct producer metadata and bind all reader tables used by this intake."""
import hashlib,json
from pathlib import Path
import sc2reader
from src.learning.production_identity import producer_ability
P=Path(__file__).parent
r=json.loads((P/'command-reconciliation-02.json').read_text());checked=0
root=Path(sc2reader.__file__).parent
paths=[p for p in root.rglob('*') if p.is_file() and p.suffix in ('.py','.csv','.json')]
paths += [Path(__file__),P/'command-reconciliation-02.json',Path('src/learning/production_identity.py')]
bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
for g in r['games']:
    reader=sc2reader.load_replay(next(p for p in g['bindings'] if p.endswith('.SC2Replay')),load_level=2,load_map=False)
    cat=json.loads(Path(next(p for p in g['bindings'] if Path(p).name=='static.json')).read_text())['game_data']
    native={a['ability_id']:a for a in cat['abilities']}
    assert not g['metadata_conflicts']
    for m in g['producer_mappings']:
        ability=reader.datapack.abilities[(m['link']<<5)|m['index']]
        assert ability.build_unit.name==m['producer']
        assert producer_ability(ability.build_unit.name,m['index'],cat)==m['ability']
        assert native[m['ability']]['friendly_name']==m['name']
        checked+=1
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==d for p,d in bindings.items())
report=dict(status='verified',mappings=checked,bindings=bindings)
(P/'metadata-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status='verified',mappings=checked,bound_reader_files=len(paths)-3)))
