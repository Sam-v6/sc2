"""Stream full command representability; no fitted policy or optimizer."""
import hashlib,json,time
from collections import Counter
from pathlib import Path
from src.learning.entity_examples import replay_examples
from src.learning.actor_selection import construction_products

OUT=Path('logs/roadmap/human-visibility-reimport-01')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 verification=json.loads((OUT/'verification.json').read_text())
 assert verification['status']=='verified_reimport'
 for p,h in verification['bindings'].items():assert sha(p)==h,p
 results=[];began=time.monotonic()
 for entry in verification['sources']:
  d=Path(entry['new']);static=json.loads((d/'static.json').read_text())['game_data']
  counts=[max(x[key] for x in static[name])+1 for name,key in (('units','unit_id'),('abilities','ability_id'),('upgrades','upgrade_id'))]
  totals=Counter();exclusions=Counter()
  for inputs,label,command,reason in replay_examples(d,*counts,(0,1,2,4,8,16,32,64,128,256,512),construction_products(static),spatial=True,missing_fields=True):
   totals['commands']+=1
   totals['representable']+=label is not None
   if reason:exclusions[reason]+=1
  receipt=json.loads((d/'dataset.json').read_text());assert totals['commands']==receipt['issued_command_audit']['matched_issued_commands']
  r=dict(source=str(d),role=entry['role'],counts=dict(totals),exclusions=dict(exclusions));results.append(r);print(json.dumps(r),flush=True)
 result=dict(status='verified_label_inventory',results=results,seconds=time.monotonic()-began,training=False,rl=False,
 bindings={str(OUT/'verification.json'):sha(OUT/'verification.json'),__file__:sha(__file__)},
 limits=['Representability is an input/label engineering check, not imitation quality or game strength.'])
 (OUT/'label-inventory.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
