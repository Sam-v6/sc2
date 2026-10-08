"""Offline morphology interpretation; the original failed fixture stays closed."""
import json
from pathlib import Path
from fixture import ARM,validate
from recurrent_worker import digest


def interpret(job,row):
    assert row['engineering_result']=='Tie' and row['status'] in ['completed','audit_failed']
    translated=dict(job);identity=None;forms=[]
    if job['target']=='SUPPLYDEPOT':
        trace=[json.loads(line) for line in Path(job['trace']).read_text().splitlines()]
        enemies=[enemy for frame in trace for tank in frame['tanks'] for enemy in tank['enemies']
                 if enemy['type'] in {'SUPPLYDEPOT','SUPPLYDEPOTLOWERED'}]
        assert enemies and len({enemy['tag'] for enemy in enemies})==1
        assert all(enemy['structure'] and not enemy['flying'] for enemy in enemies)
        identity=enemies[0]['tag'];forms=sorted({enemy['type'] for enemy in enemies})
        # The exact lowered form must independently satisfy the SAME frame,
        # range, command and observed-siege requirements of the original check.
        if 'SUPPLYDEPOTLOWERED' in forms:translated['target']='SUPPLYDEPOTLOWERED'
    audit=validate(translated,{**row,'status':'completed'})
    return {**audit,'original_status':row['status'],'original_target':job['target'],
            'interpreted_target':translated['target'],'structure_identity_tag':identity,'observed_forms':forms,
            'original_summary_changed':False,'offline_interpretation_only':True}


def main():
    inputs=json.loads((ARM/'inputs.json').read_text());summary=json.loads((ARM/'summary.json').read_text())
    assert not summary['completed'] and not summary['physical_gate_passed']
    ledger=json.loads((ARM/'ledger.json').read_text());assert len(ledger)==6
    hashes={str(path):digest(path) for path in [Path(__file__),ARM/'inputs.json',ARM/'summary.json',ARM/'ledger.json']}
    results=[]
    for job in inputs['jobs']:
        row=next(row for row in ledger if row['seed']==job['seed'])
        for key in ['trace','replay','receipt']:hashes[job[key]]=digest(job[key])
        results.append({'seed':job['seed'],'interpretation':interpret(job,row)})
    for path,expected in hashes.items():assert digest(path)==expected,path
    output=ARM.parent/'physical-morphology-interpretation.json';assert not output.exists()
    output.write_text(json.dumps({'recorded_physics_verified':True,'original_fixture_gate_passed':False,
        'original_summary_changed':False,'games_launched':0,'fits':0,'hashes':hashes,'cases':results},indent=2)+'\n')
    print(output)


if __name__=='__main__':main()
