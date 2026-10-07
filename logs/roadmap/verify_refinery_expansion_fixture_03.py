"""Verify source bindings, raw selection/harvesting, and actual replay construction."""
import json,hashlib,math
from pathlib import Path
import mpyq
from src.learning.production_clearance import refinery_sites,claimed_geysers
from src.learning.production_request import ProductionRequest
from src.learning.gameplay import Command
from src.learning.replay_extract import replay_metadata,load_protocol
ROOT=Path('logs/roadmap/refinery-expansion-fixture-03')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 contract=json.loads((ROOT/'contract.json').read_text());report=json.loads((ROOT/'report.json').read_text());assert report['status']=='completed' and report['peak_cpu']<=80
 for p,h in contract['bindings'].items():
  source=Path(p);assert sha(source)==h
  relative=source.relative_to(Path.cwd()) if source.is_absolute() else source;dest=ROOT/'source-snapshot'/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes());assert sha(dest)==h
 rows=[json.loads(s) for s in (ROOT/'trace.jsonl').read_text().splitlines()];static=json.loads((ROOT/'static.json').read_text());data=static['game_data'];catalog={a['ability_id']:a for a in data['abilities']}
 home=static['home'];expansion=static['expansion'];issued=[];pending={};protected=0;completed=None;mining=[];gas_at_completion=None
 for row in rows:
  state=row['observation'];loop=state['game_loop'];own=[u for u in state['units'] if u['alliance']==1]
  assert not state['action_errors'] and all(code==1 for code in row['results']+row['assistance_results'])
  sites=refinery_sites(state,catalog);assert row['sites']==[u['tag'] for u in sites];assert row['claimed']==sorted(claimed_geysers(state,catalog))
  for event in row['pending']:
   tag=event['actor'];assert pending[tag].status(state)==event['status']
   if event['status']=='started':del pending[tag]
   else:protected+=1
  for command,code in zip(row['commands'],row['results'],strict=True):
   assert code==1 and command['ability']==320 and command['target_unit'] in row['sites'];assert command['units'][0] not in pending
   cmd=Command(320,tuple(command['units']),target_unit=command['target_unit']);pending[command['units'][0]]=ProductionRequest(cmd,state,data)
   point=next(u['position'][:2] for u in state['units'] if u['tag']==command['target_unit']);issued.append(dict(loop=loop,command=command,point=point))
  for c in row['assistance']:assert not set(c['units'])&set(pending)
  for trace in row['placement']:assert trace['placement_result']==1 and not trace.get('rejected')
  expansion_refinery=next((u for u in own if u['unit_type']==20 and u.get('build_progress',1)>=1 and math.dist(u['position'][:2],expansion)<15),None)
  if expansion_refinery:
   if completed is None:
    completed=dict(loop=loop,tag=expansion_refinery['tag'],initial_contents=expansion_refinery['vespene_contents']);gas_at_completion=row['score'].get('score_details',{}).get('collected_vespene',0)
   for u in own:
    if u['unit_type']==45 and any(o['ability_id']==295 and o.get('target_unit_tag')==expansion_refinery['tag'] for o in u.get('orders',[])):mining.append(dict(loop=loop,worker=u['tag']))
 assert len(issued)==3 and completed and mining
 assert all(math.dist(i['point'],home)<15 for i in issued[:2]);assert math.dist(issued[2]['point'],home)>15 and math.dist(issued[2]['point'],expansion)<15
 last=rows[-1];refinery=next(u for u in last['observation']['units'] if u['tag']==completed['tag']);extracted=completed['initial_contents']-refinery['vespene_contents'];assert extracted>0
 income=last['score'].get('score_details',{}).get('collected_vespene',0)-gas_at_completion;assert income>0
 metadata,_=replay_metadata(ROOT/'game.SC2Replay');assert metadata['BaseBuild']=='Base75689';protocol=load_protocol(75689)
 events=list(protocol.decode_replay_tracker_events(mpyq.MPQArchive(str(ROOT/'game.SC2Replay')).read_file('replay.tracker.events')))
 starts={(e['m_unitTagIndex'],e['m_unitTagRecycle']) for e in events if e['_event'].endswith('.SUnitInitEvent') and e.get('m_controlPlayerId')==1 and e.get('m_unitTypeName')==b'Refinery'}
 done={ (e['m_unitTagIndex'],e['m_unitTagRecycle']) for e in events if e['_event'].endswith('.SUnitDoneEvent')};assert len(starts)==3 and len(starts&done)==3
 paths=[Path(__file__),ROOT/'contract.json',ROOT/'report.json',ROOT/'trace.jsonl',ROOT/'static.json',ROOT/'game.SC2Replay']
 result=dict(status='verified_native_expansion_refinery_and_gas_collection',replay_refinery_starts=3,replay_refinery_completions=3,issued=issued,expansion_completion=completed,expansion_harvesting_observations=len(mining),expansion_gas_extracted=extracted,collected_gas_after_expansion_completed=income,protected_pending_observations=protected,action_errors=0,normal_120_second_cutoff=True,peak_cpu=report['peak_cpu'],wall_seconds=report['results'][0]['wall_seconds'],training=False,rl=False,limits=['Engineering fixture with debug resources,one pre-created expansion CommandCenter,four extra SCVs.','All three Refineries use actual native build/placement commands; harvesting uses existing mining primitive.','No learned decisions, macro economy acceptance, victory, or Hard competence.'],bindings={str(p):sha(p) for p in paths})
 (ROOT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('bindings','issued')}))
if __name__=='__main__':main()
