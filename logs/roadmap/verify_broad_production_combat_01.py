"""Independent replay effects, command provenance and combat checks."""
import gzip,hashlib,json,math
from collections import Counter
from pathlib import Path
import mpyq
from src.learning.teacher_states import remember_command
from src.learning.replay_extract import replay_metadata,load_protocol
ROOT=Path('logs/roadmap/broad-production-combat-01')
contract=json.loads((ROOT/'contract.json').read_text());report=json.loads((ROOT/'report.json').read_text())
assert report['status']=='completed' and len(report['results'])==3,report['status']
assert report['peak_cpu']<=contract['cpu_limit']
for p,h in contract['bindings'].items():
    assert hashlib.sha256((ROOT/'source-snapshot'/p).read_bytes()).hexdigest()==h,p
summaries=[];all_gates=True
for job,receipt in zip(contract['jobs'],report['results'],strict=True):
    folder=Path(job['output']);rows=[json.loads(l) for l in gzip.open(folder/'trace.jsonl.gz','rt')]
    metadata,details=replay_metadata(folder/'game.SC2Replay')
    assert metadata['BaseBuild']=='Base75689'
    protocol=load_protocol(int(metadata['BaseBuild'].removeprefix('Base')))
    events=list(protocol.decode_replay_tracker_events(mpyq.MPQArchive(str(folder/'game.SC2Replay')).read_file('replay.tracker.events')))
    births=Counter(e['m_unitTypeName'].decode() for e in events if e['_event'].endswith('.SUnitBornEvent') and e.get('m_controlPlayerId')==1 and e['_gameloop']>0)
    barracks_tags={(e['m_unitTagIndex'],e['m_unitTagRecycle']) for e in events if e['_event'].endswith('.SUnitInitEvent') and e.get('m_controlPlayerId')==1 and e.get('m_unitTypeName')==b'Barracks'}
    completed_barracks=sum((e['m_unitTagIndex'],e['m_unitTagRecycle']) in barracks_tags for e in events if e['_event'].endswith('.SUnitDoneEvent'))
    history=[];control=set();until=0;fixture_codes=Counter();assist_codes=Counter();fixture=assists=delayed=0;combat=Counter();max_distance=0;targets=0
    for row in rows:
        st=row['observation'];loop=st['game_loop']
        assert st['recent_commands']==history[-32:],(job['race'],loop,'fixture-only history')
        if loop>=until:control=set()
        command=row.get('issued_command');codes=row.get('results',[])
        if command:
            assert len(codes)==1;fixture+=1;fixture_codes.update(map(str,codes))
            assert command['ability'] in (524,321,560),'Unexpected fixture macro action'
            if codes[0]==1:
                history.append(remember_command(command,st,loop));history=history[-32:]
                until=loop+max(1,row['delay']);control=set(command['units'])
        else:assert not codes
        assert set(row['primitive_protected'])==control
        commands=row.get('assistance',[]);codes=row.get('assistance_results',[])
        assert len(commands)==len(codes)
        actors=[tag for c in commands for tag in c['units']]
        own={u['tag']:u for u in st['units'] if u['alliance']==1}
        assert len(actors)==len(set(actors)) and set(actors)<=set(own) and not set(actors)&control
        visible={u['tag'] for u in st['units'] if u['alliance']==4 and u.get('display_type',1)==1 and u.get('health',0)>0}
        for c in commands:
            assert c['ability'] not in (524,321,560),'Assistance invented production'
            if any(own[tag]['unit_type']==48 for tag in c['units']):
                combat[c['ability']]+=1
                if c.get('target_unit'):
                    assert c['target_unit'] in visible,'Combat target not currently visible'
                    targets+=1
            if c['ability']==319:
                assert len(c['units'])==1
        centers=[u['position'][:2] for u in st['units'] if u['alliance']==1 and u['unit_type']==18]
        if centers:
            for u in own.values():
                if u['unit_type']==48:max_distance=max(max_distance,math.dist(u['position'][:2],centers[0]))
        assists+=len(commands);assist_codes.update(map(str,codes));delayed+=len(st['action_errors'])
    assert fixture==receipt['fixture_commands'] and receipt['learned_commands']==0 and not receipt['checkpoint_predictions_used']
    assert dict(fixture_codes)==receipt['action_results'] and dict(assist_codes)==receipt['primitive_results'] and assists==receipt['primitive_commands']
    errors=delayed+sum(n for c,n in (fixture_codes+assist_codes).items() if c!='1')
    gates=contract['gates'];score=receipt['score']
    checks=dict(worker_births=births['SCV']>=gates['worker_births'],marine_births=births['Marine']>=gates['marine_births'],
                barracks_completions=completed_barracks>=gates['barracks_completions'],
                damage=score['damage_dealt']>=gates['damage_dealt'],kills=score['killed_value']>=gates['killed_value'],
                movement=max_distance>=gates['army_distance_from_start'],action_errors=errors==0,
                visible_target_attacks=targets>0)
    all_gates &= all(checks.values())
    result=dict(race=job['race'],result=receipt['result'],gate_pass=all(checks.values()),checks=checks,
                births=dict(births),barracks_completions=completed_barracks,fixture_commands=fixture,
                assisted_commands=assists,combat_abilities=dict(combat),visible_target_attacks=targets,
                max_army_distance=max_distance,action_errors=errors,score=score,
                learned_commands=0,learned_competence=False)
    summaries.append(result);print(json.dumps(result),flush=True)
paths=[Path(__file__),ROOT/'contract.json',ROOT/'report.json']
for job in contract['jobs']:paths.extend(Path(job['output'])/n for n in ('game.SC2Replay','episode.json','trace.jsonl.gz','static.json'))
result=dict(status='verified_native_production_combat_execution' if all_gates else 'failed_native_execution_gate',
            games=summaries,peak_cpu=report['peak_cpu'],training=False,rl=False,
            learned_competence=False,limits=contract['limits'],bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
(ROOT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes())
