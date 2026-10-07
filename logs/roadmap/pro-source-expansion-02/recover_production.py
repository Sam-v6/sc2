"""Apply verified producer name/index correspondence before new-source import."""
from pathlib import Path
import hashlib,json,sc2reader
import importlib
data_module=importlib.import_module("sc2reader.data")
from src.learning.production_identity import producer_ability
from src.learning.tournament_commands import reconcile_commands
P=Path(__file__).parent
source=P/'command-reconciliation-01.json';old=json.loads(source.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert all(sha(p)==d for p,d in old['bindings'].items())
results=[]
for g in old['games']:
    assert all(sha(p)==d for p,d in g['bindings'].items())
    i=g['idx'];events=json.loads((P/f'raw-commands-{i}.json').read_text());actions=json.loads((P/f'fall-actions-{i}.json').read_text())['actions']
    path=next(p for p in g['bindings'] if p.endswith('.SC2Replay'))
    reader=sc2reader.load_replay(path,load_level=2,load_map=False)
    catalog_path=next(p for p in g['bindings'] if Path(p).name=='static.json')
    catalog=json.loads(Path(catalog_path).read_text())['game_data'];abilities={a['ability_id']:a for a in catalog['abilities']}
    names={(x['link'],x['index']):x['name'] for x in g['replay_names']}
    selections={(x['loop'],x['sequence']):x['tags'] for x in g['selections']}
    baseline,audit=reconcile_commands(events,actions,selections,abilities,names)
    def serialized(rows):return json.loads(json.dumps([dict(r,command=r['command'].as_dict()) for r in rows]))
    assert serialized(baseline)==g['accepted'] and audit==g['audit']
    mappings={}
    for e in events:
        raw=e['m_abil']
        if raw is None:continue
        key=(raw['m_abilLink'],raw['m_abilCmdIndex'])
        meta=reader.datapack.abilities.get((key[0]<<5)|key[1])
        if meta is None or meta.build_unit is None:continue
        ability=producer_ability(meta.build_unit.name,key[1],catalog)
        if ability is not None:mappings[key]=dict(ability=ability,producer=meta.build_unit.name,name=abilities[ability]['friendly_name'])
    eventkeys={(e['_gameloop'],e['m_sequence']):e for e in events};conflicts=set()
    oldkeys={(r['loop'],r['sequence']) for r in baseline}
    for r in baseline:
        raw=eventkeys[r['loop'],r['sequence']]['m_abil']
        key=(raw['m_abilLink'],raw['m_abilCmdIndex']) if raw else None
        if key in mappings and mappings[key]['ability']!=r['command'].ability:conflicts.add(key)
    revised=dict(names)
    revised.update({k:m['name'] for k,m in mappings.items() if k not in conflicts})
    accepted,newaudit=reconcile_commands(events,actions,selections,abilities,revised)
    assert serialized([r for r in accepted if (r['loop'],r['sequence']) in oldkeys])==g['accepted']
    result=dict(g,accepted=serialized(accepted),audit=newaudit,replay_names=[dict(link=k[0],index=k[1],name=v) for k,v in revised.items()],producer_mappings=[dict(link=k[0],index=k[1],**v) for k,v in mappings.items() if k not in conflicts],metadata_conflicts=[list(k) for k in sorted(conflicts)])
    result['bindings']=dict(g['bindings'],**{str(source):sha(source),str(Path(data_module.__file__)):sha(data_module.__file__)})
    results.append(result)
    print(i,len(baseline),len(accepted),len(newaudit['unresolved_events']),flush=True)
receipt=dict(games=results,training_eligible=False,bindings=dict(old['bindings'],**{str(Path(__file__)):sha(__file__),'src/learning/production_identity.py':sha('src/learning/production_identity.py')}))
(P/'command-reconciliation-02.json').write_text(json.dumps(receipt,indent=2)+'\n')
