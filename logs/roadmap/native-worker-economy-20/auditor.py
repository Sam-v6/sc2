"""Tracker-backed birth/death and economy comparison; snapshots are partial."""
import json,hashlib,mpyq
from pathlib import Path
from collections import Counter
from src.learning.replay_extract import replay_metadata,load_protocol
root=Path('logs/roadmap');out=root/'native-worker-economy-20';out.mkdir(exist_ok=False);sources=dict(human=root/'pro-preconverted-probe-01/2cda222081e80d9a1c188698ce9bcda6.SC2Replay',native=root/'fixed-human-plan-native-20/episode/game.SC2Replay');results={}
for name,path in sources.items():
 meta,_=replay_metadata(path);pr=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));events=list(pr.decode_replay_tracker_events(mpyq.MPQArchive(str(path)).read_file('replay.tracker.events')));own={};born=Counter();dead=Counter();births=[];statistics=[]
 for e in events:
  if e['_gameloop']>=9224:break
  kind=e['_event'].rsplit('.',1)[-1];tag=e.get('m_unitTagIndex'),e.get('m_unitTagRecycle')
  if kind in ('SUnitBornEvent','SUnitInitEvent') and e.get('m_upkeepPlayerId')==1:
   unit=e['m_unitTypeName'].decode();own[tag]=unit;born[unit]+=1
   if unit=='SCV':births.append(e['_gameloop'])
  elif kind=='SUnitDiedEvent' and tag in own:dead[own.pop(tag)]+=1
  elif kind=='SPlayerStatsEvent' and e['m_playerId']==1 and e['_gameloop'] in (2240,4480,6720,8800):statistics.append(dict(loop=e['_gameloop'],stats=e['m_stats']))
 results[name]=dict(births=dict(born),deaths=dict(dead),scv_birth_loops=births,statistics=statistics)
assert results['human']['births']['SCV']==55 and results['native']['births']['SCV']==45
assert results['human']['deaths'].get('SCV',0)==results['native']['deaths'].get('SCV',0)==0
assert results['human']['deaths']['Hellion']==10 and results['native']['deaths'].get('Hellion',0)==0
result=dict(status='verified_source_native_tracker_economy_difference',cutoff_exclusive=9224,results=results,source_scv_births=55,native_scv_births=45,worker_deaths_both=0,source_hellion_deaths=10,native_hellion_deaths=0,training=False,rl=False,limitations=['Source professional opponent and native VeryEasy scripted combat differ. Snapshot own-unit counts omit some still-alive workers; use tracker and food-worker totals.','Differences are descriptive, not proof that any single primitive caused all economic loss.'],bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),*sources.values())})
(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');(out/'auditor.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({k:v for k,v in result.items() if k not in ('results','bindings')}))
for name,r in results.items():
 for s in r['statistics']:
  if s['loop']==8800:print(name,{k:v for k,v in s['stats'].items() if k in ('m_scoreValueWorkersActiveCount','m_scoreValueMineralsCollectionRate','m_scoreValueVespeneCollectionRate','m_scoreValueMineralsCurrent','m_scoreValueMineralsUsedCurrentArmy','m_scoreValueMineralsLostArmy')})
