"""Verify preserved observations and new labels, including provenance isolation."""
import gzip,json,hashlib
from pathlib import Path
root=Path('logs/roadmap');out=root/'human-command-repeats-01';new=out/'corpus/870';old=root/'human-refinery-snapshot-reimport-01/corpus/870'
receipt=json.loads((new/'dataset.json').read_text());assert receipt['status']=='completed' and not receipt['disable_fog'] and receipt['unresolved_repeat_contexts']==399
for mapping in (receipt['source_bindings'],receipt['code_bindings'],{str(new/k):v for k,v in receipt['corpus_bindings'].items()}):
 for p,h in mapping.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
before={(r['action_loop'],r['source_sequence']):r for r in map(json.loads,gzip.open(old/'examples.jsonl.gz','rt'))}
after={(r['action_loop'],r['source_sequence']):r for r in map(json.loads,gzip.open(new/'examples.jsonl.gz','rt'))}
assert len(before)==851 and len(after)==1156 and set(before)<=set(after)
for key,a in before.items():
 b=after[key];assert a['commands']==b['commands'] and a['original_command']==b['original_command'] and a.get('label_translation')==b.get('label_translation')
 for field in ('player','map','units','owned_memory','memory','unknown_fields'):
  assert a['observation'].get(field)==b['observation'].get(field),(key,field)
added={(r['loop'],r['sequence']):r for r in json.loads((out/'audit.json').read_text())['added']}
assert set(added)==set(after)-set(before)
for key,row in added.items():
 example=after[key];assert example['original_command']==row['command']
 assert 'source_repeat_provenance' in example and 'source_repeat_provenance' not in example['observation']
 assert example['observation']['game_loop']==key[0]
 for tag in row['command']['units']:
  actor=next(u for u in example['observation']['units'] if u['tag']==tag)
  assert actor['alliance']==1
assert after[7171,637]['original_command']['units']==[4357619713]
assert after[7171,637]['original_command']['target_point']==[134.5,37.5]
result=dict(status='verified_reimported_source_repetitions',labels=1156,old_preserved=851,added=305,old_player_unit_map_observations_preserved=True,history_changed_to_include_actual_repeats_and_unknown_slots=True,provenance_outside_observations=True,unknown_repeat_contexts=399,training=False,rl=False,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),new/'dataset.json',new/'examples.jsonl.gz',old/'examples.jsonl.gz')})
(out/'corpus-verification.json').write_text(json.dumps(result,indent=2)+'\n');(out/'source-snapshot/corpus-verifier.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(result))
