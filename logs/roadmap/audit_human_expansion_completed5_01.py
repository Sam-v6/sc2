"""Audit complete new human datasets without loading or evaluating any model."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
from src.learning.gameplay import Command

BASE=Path('logs/roadmap')
IDS=[51572,51685,51885,51754,51483]
OUT=BASE/'human-corpus-expansion-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with gzip.open(p,'rt') as f:
        yield from map(json.loads,f)

contract=json.loads((OUT/'contract.json').read_text())
snapshot=json.loads((OUT/'progress.json').read_text())
(OUT/'completed5-progress-snapshot-01.json').write_text(json.dumps(snapshot,indent=2)+'\n')
assert all(sha(Path(p))==digest for p,digest in contract['sources_before'].items())
assert set(contract['replay_roles'])=={'51572','51685','51885','51754','51483'}
assert all(role=='candidate_teaching' for role in contract['replay_roles'].values())
assert contract['reserved_game_excluded']==51886 and not contract['fit'] and not contract['RL']
completed={run['id']:run for run in snapshot if run.get('status')=='completed'}
retry_receipts={}
for number in (51754,51483):
    retrydir=BASE/f'human-{number}-retry-02-receipts'
    retrycontract=json.loads((retrydir/'contract.json').read_text())
    retryreport=json.loads((retrydir/'report.json').read_text())
    assert retryreport['status']=='completed' and retryreport['sources_unchanged']
    assert retrycontract['source_before']==retryreport['source_after']
    assert all(sha(Path(p))==digest for p,digest in retrycontract['source_before'].items())
    assert retrycontract['role']=='candidate_teaching' and retrycontract['no_fit'] and retrycontract['no_RL']
    completed[number]=dict(retryreport,id=number)
    retry_receipts[str(number)]={'contract_sha256':sha(retrydir/'contract.json'),'report_sha256':sha(retrydir/'report.json')}
fit_contract=json.loads((BASE/'expanded-human-macro-01/contract.json').read_text())
assert fit_contract['role_change_before_fit']['51483']['new']=='reserved_fresh_expansion_validation'
assert fit_contract['role_change_before_fit']['51483']['sha256']==sha(BASE/'human-replays/51483.SC2Replay')
assert all(item['sha256']!=fit_contract['role_change_before_fit']['51483']['sha256'] for item in fit_contract['train_inventory'])
for n in IDS:
    run=completed[n]
    assert run['extract_exit']==0 and run['issued_exit']==0
    assert all(sha(Path(p))==digest for p,digest in run['output_hashes'].items())
result=[]
for n in IDS:
    native=BASE/f'human-{n}-expansion-0{2 if n in (51754,51483) else 1}'
    issued=BASE/f'issued-{n}-expansion-0{2 if n in (51754,51483) else 1}'
    receipt=json.loads((issued/'dataset.json').read_text())
    audit=receipt['issued_command_audit']
    assert receipt['status']=='completed' and receipt['disable_fog'] is False
    player=receipt['player']['player_info']
    assert player['player_id']==1 and player['player_name']=='Mez' and player['race_actual']==1 and player['type']==1
    assert receipt['observation_stride']==1 and receipt['untranslated_gameplay']==0
    assert sha(Path(receipt['replay']))==receipt['sha256']
    previous=None;frames=0;types=set();max_workers=0;max_supply=0
    for state in rows(native/'observations.jsonl.gz'):
        loop=state['game_loop']
        assert previous is None or loop==previous+1
        previous=loop;frames+=1
        assert all(u.get('display_type',1)==1 for u in state['units'])
        assert all(c['game_loop']<=loop for c in state['recent_commands'])
        assert all(m['last_seen_loop'] is None or m['last_seen_loop']<=loop for m in state['memory'])
        assert all(m['last_seen_loop']<=loop and not m['observed'] for m in state['owned_memory'])
        own=[u for u in state['units'] if u['alliance']==1]
        types.update(u['unit_type'] for u in own)
        max_workers=max(max_workers,sum(u['unit_type']==45 for u in own))
        max_supply=max(max_supply,state['player'].get('food_used',0))
    assert frames==receipt['recorded_observations'] and previous==receipt['last_loop']
    matched=0;numrows=0;previous=-1;abilities=Counter();queued=0;bursts=0
    examples=list(rows(issued/'examples.jsonl.gz'))
    unresolved={r['event']['_gameloop'] for r in audit['unresolved_events']}
    masked=0
    for i,row in enumerate(examples):
        assert row['observation']['game_loop']==row['action_loop']-1
        assert row['action_loop']>previous
        previous=row['action_loop'];numrows+=1
        gap=None if i==len(examples)-1 else examples[i+1]['action_loop']-row['action_loop']
        must_mask=gap is not None and any(row['action_loop']<t<row['action_loop']+gap for t in unresolved)
        assert row['next_action_delay']==(None if must_mask else gap)
        masked+=must_mask
        bursts+=len(row['commands'])>1
        for c in row['commands']:
            command=Command(c['ability'],tuple(c['units']),c['target_unit'],tuple(c['target_point']) if c['target_point'] is not None else None,c['queue'],c['autocast'])
            assert Command.from_proto(command.to_proto())==command
            matched+=1;abilities[c['ability']]+=1;queued+=c['queue']
    assert numrows==receipt['rows'] and matched==audit['matched_issued_commands']
    assert matched+len(audit['unresolved_events'])==audit['issued_events']
    assert masked==audit['masked_timing_rows']
    static=json.loads((issued/'static.json').read_text())
    catalog={a['ability_id']:a.get('friendly_name',a.get('link_name')) for a in static['game_data']['abilities']}
    result.append({'id':n,'replay_sha256':receipt['sha256'],'map':receipt['metadata']['Title'],
        'teacher':'Mez','professional':False,'role':'reserved_fresh_expansion_validation' if n==51483 else 'candidate_teaching','frames':frames,'last_command_loop':previous,
        'end_observation_loop':receipt['last_loop'],'matched_commands':matched,'rows':numrows,'burst_rows':bursts,
        'unresolved_commands':len(audit['unresolved_events']),'masked_timing_rows':masked,'queued_commands':queued,
        'max_observed_workers':max_workers,'max_food_used':max_supply,'own_unit_types':sorted(types),
        'abilities':{str(a):{'name':catalog.get(a),'count':count} for a,count in sorted(abilities.items())}})
assert len({r['replay_sha256'] for r in result})==len(IDS)
reserved=sha(BASE/'human-replays/51886.SC2Replay')
assert reserved not in {r['replay_sha256'] for r in result}
report={'status':'completed','scope':'five complete datasets including two separately verified retries;four teaching and one reserved fresh validation;no model calls; data integrity and causal timestamps, not independent proof of every fog pixel or learned competence',
        'new_games':len(result),'matched_commands':sum(r['matched_commands'] for r in result),
        'new_named_teachers':0,'professional_games':0,'reserved_game_excluded':51886,'no_model_loaded':True,
        'helper_sha256':sha(Path(__file__)),'results':result,
        'verified_contract_sha256':sha(OUT/'contract.json'),'verified_progress_snapshot_sha256':sha(OUT/'completed5-progress-snapshot-01.json'),
        'verified_retry_receipts':retry_receipts,'verified_role_assignment_contract_sha256':sha(BASE/'expanded-human-macro-01/contract.json'),'all_source_and_output_hashes_verified':True,'planned_games':5,'audited_games':5,'whole_batch_terminal':True,'original_attempt_batch_status':'incomplete','new_teaching_games':4,'reserved_fresh_expansion_validation':51483}
assert all(sha(Path(p))==digest for p,digest in contract['sources_before'].items())
(OUT/'integrity-audit-completed5-01.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='results'}))
