import collections
import gzip
import json
from pathlib import Path
import sys
from sc2.ids.unit_typeid import UnitTypeId

ARMY = {getattr(UnitTypeId, name).value for name in (
    'MARINE','MARAUDER','REAPER','GHOST','HELLION','HELLIONTANK',
    'SIEGETANK','SIEGETANKSIEGED','CYCLONE','WIDOWMINE','WIDOWMINEBURROWED',
    'THOR','THORAP','VIKINGFIGHTER','VIKINGASSAULT','MEDIVAC','BANSHEE',
    'RAVEN','LIBERATOR','LIBERATORAG','BATTLECRUISER')}
root = Path(sys.argv[1])
rows = []
for p in sorted(root.glob('*/episode.json')):
    receipt = json.loads(p.read_text())
    born = set()
    selected = collections.Counter()
    results = collections.Counter()
    commands = queued = long = interruptions = max_army = 0
    with gzip.open(p.parent / 'trace.jsonl.gz', 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            own = {u['tag']:u for u in row['observation']['units'] if u['alliance']==1}
            born.update(u['tag'] for u in own.values()
                        if u['unit_type'] in ARMY and u.get('build_progress',0)>=1)
            army = row['observation']['player'].get('food_army',0)
            max_army = max(max_army,army)
            if row['rl_decision']:
                selected[row['rl_decision']['ability']] += 1
            cmds, codes = row['issued_model_commands'], row['model_action_results']
            if len(cmds)!=len(codes):
                raise ValueError('Model command/result attribution mismatch')
            results.update(codes)
            for cmd in cmds:
                commands += 1
                queued += cmd['queue']
                if cmd['ability'] in (4,16,17,18,23):
                    interruptions += any(any(318<=o['ability_id']<=328
                        for o in own.get(tag,{}).get('orders',[]))
                        for tag in cmd['units'])
            long += sum(d.get('delay',0)>=16 for d in row['decisions']
                if d.get('command') and d.get('source')!='idle_worker_harvest')
    rows.append(dict(game=p.parent.name,result=receipt['result'],
        completed_army_units=len(born),maximum_army_supply=max_army,
        final_army_supply=receipt['army_supply'],workers=receipt['workers'],
        score=receipt['score'],commands=commands,queued_commands=queued,
        predicted_delays_at_least_16=long,selected=dict(selected),
        engine_results=dict(results),queue_full_per_command=results[203]/commands
        if commands else 0,possible_construction_interruptions=interruptions))
(root/'execution-audit.json').write_text(json.dumps(rows,indent=2)+'\n')
for row in rows:
    print(row['game'], row['result'], 'army produced',row['completed_army_units'],
          'max supply',row['maximum_army_supply'],
          'queue-full rate',round(row['queue_full_per_command'],3))
