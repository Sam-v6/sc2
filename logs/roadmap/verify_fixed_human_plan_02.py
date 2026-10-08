from pathlib import Path
import hashlib,json
from src.learning.tournament_record import decode_record
root=Path('logs/roadmap');out=root/'fixed-human-production-plan-02'
plan=json.loads((out/'plan.json').read_text());g=json.loads((root/'human-refinery-snapshot-reimport-01/reconciliation.json').read_text())['games'][0]
accepted={(r['loop'],r['sequence']):r for r in g['accepted']}
raw={(e['_gameloop'],e['m_sequence']):e for e in json.loads((root/'pro-preconverted-probe-01/raw-commands-870.json').read_text())}
data=json.loads((root/'joint-frozen-native-wait-02/static.json').read_text())['game_data'];abilities={a['ability_id']:a for a in data['abilities']}
assert not plan['unresolved'] and len(plan['tickets'])==203 and len(plan['repeated_present_orders'])==4
keys=[];precise_changes=0
for row in plan['tickets']+plan['repeated_present_orders']:
 key=(row['loop'],row['sequence']);keys.append(key);source=accepted[key]['command'];event=raw[key];command=row['command']
 assert command['units']==source['units'] and command.get('target_unit')==source.get('target_unit')
 assert command['queue']==bool(event['m_cmdFlags']&2)
 def canon(a):return abilities.get(a,{}).get('remaps_to_ability_id') or a
 assert canon(command['ability'])==canon(source['ability'])
 if command['ability']!=source['ability']:
  assert abilities[command['ability']]['link_index']==event['m_abil']['m_abilCmdIndex']
  assert abilities[command['ability']].get('available') is not False
 if source.get('target_point') is not None:
  point=event['m_data']['TargetPoint'];expected=[point['x']/4096,point['y']/4096]
  assert command['target_point']==expected
  precise_changes+=expected!=source['target_point']
 else:assert command.get('target_point') is None
assert len(keys)==len(set(keys))
assert [(r['loop'],r['sequence']) for r in plan['tickets']]==sorted((r['loop'],r['sequence']) for r in plan['tickets'])
assert all(all(s=='already_present_no_count_increase' for s in r['existing_queue_evidence']) for r in plan['repeated_present_orders'])
for p,h in plan['bindings'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
result=dict(status='verified_fixed_source_command_compilation',tickets=203,repeated_present_orders=4,
 original_coordinate_repairs=precise_changes,training=False,rl=False,native_playback=False,
 plan_sha256=hashlib.sha256((out/'plan.json').read_bytes()).hexdigest(),limitations=plan['limitations'])
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'source-snapshot'/'verifier.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(result,indent=2))
