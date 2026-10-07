"""Verify live catalogue goal, ability availability, acceptance and order progress."""
from pathlib import Path
import hashlib,json,mpyq
from src.learning.replay_extract import load_protocol,replay_metadata
ROOT=Path('logs/roadmap/upgrade-pointer-fixture-02');report=json.loads((ROOT/'report.json').read_text());contract=json.loads((ROOT/'contract.json').read_text());assert report['status']=='completed' and report['peak_cpu']<=80 and len(report['results'])==1
for p,h in report['bindings'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
receipt=report['results'][0];job=receipt['job'];assert receipt['status']=='completed' and job==contract['jobs'][0]
data=json.loads(Path(job['catalog']).read_text());abilities={a['ability_id']:a for a in data['abilities']};upgrade=next(u for u in data['upgrades'] if u['name']=='TerranVehicleAndShipArmorsLevel1');assert upgrade['ability_id']==2297 and abilities[2297]['available'] is False and abilities[864]['available'] is True and abilities[864]['remaps_to_ability_id']==3700
rows=list(map(json.loads,Path(job['trace']).read_text().splitlines()));issued=[r for r in rows if r['commands']];assert len(issued)==1;r=issued[0];cmd=r['commands'][0];actor=cmd['units'][0];assert r['goal']['ability']==864 and cmd['ability']==864 and r['results']==[1] and 864 in r['available'][str(actor)]
assert not any(row['delayed_errors'] for row in rows)
progress=[]
for row in rows:
 for u in row['observation']['units']:
  if u['tag']==actor:
   for order in u.get('orders',[]):
    if order['ability_id']==864:progress.append(order.get('progress',0))
assert len(progress)>2 and max(progress)>min(progress)
replay=Path(job['replay']);meta,_=replay_metadata(replay);proto=load_protocol(int(meta['BaseBuild'].removeprefix('Base')));archive=mpyq.MPQArchive(str(replay));init=proto.decode_replay_initdata(archive.read_file('replay.initData'));assert init['m_syncLobbyState']['m_userInitialData'][0]['m_randomSeed']==job['seed']
paths=[Path(__file__),ROOT/'report.json',ROOT/'contract.json',Path(job['trace']),Path(job['catalog']),replay]
v=dict(status='verified_live_upgrade_pointer_repair',inactive_metadata_ability=2297,resolved_active_ability=864,available_specific_ability=864,accepted_commands=1,action_errors=0,observed_order_frames=len(progress),progress_range=[min(progress),max(progress)],peak_cpu=report['peak_cpu'],seed=job['seed'],engineering_only=True,training=False,rl=False,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},limitations=['Debug-created Armory/Factory and resources isolate catalogue/command execution.','Eight seconds proves accepted research and increasing order progress, not upgrade completion or game strength.'])
(ROOT/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
