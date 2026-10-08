# Recurrent Terran strength study: completed without promotion

Reliable all-race Hard strength remains unmet. Both arms fail the fixed development
support gate; neither is selected, extended or promoted. No benefit from memory is
established by this study's64training games per arm. This does not establish that
memory is useless for SC2. The reserved50000–50029final acceptance cases remain
untouched. Complete independent evaluation review passes90games/65,822decisions, allmodel/source
bindings and the training-only coverage recount.

## Actual training and evaluation

All128native training games completed:64per arm across Medium/Hard, three races,
five computer builds and two maps. All16rounds/32learning calls completed without
infrastructure failures. Each arm received256whole-episode PPO updates and
64episodes/attempts, with fresh residual optimizer state and a bitwise unchanged
parent network. Independent training review verifies94,846decisions and immutable
source/data/model/task chains. The90fresh evaluation games also completed without
infrastructure failures; model hashes stayed unchanged and no evaluation fitting
or trajectory archives were produced.

Counts below are victories/defeats/finite-time ties; returns use the original
combat-kills-v1 reward and discount. Recurrent, reset and reference share cases.

| Panel | Recurrent W/L/T; mean return | Reset W/L/T; mean return | Reference W/L/T; mean return |
| --- | --- | --- | --- |
| Hard greedy,12cases | 4/6/2; .177951 | 5/7/0; .274286 | 5/7/0; .270810 |
| Hard sampled,12cases | 1/11/0; .047237 | 0/12/0; -.022570 | 0/12/0; -.035485 |
| Easy sampled,6cases | 1/2/3; .116790 | 4/1/1; .318916 | 1/3/2; .135929 |

Greedy Hard per-race wins(Terran/Protoss/Zerg,4cases each): recurrent1/2/1,
reset0/1/4,reference2/2/1. Both trained arms lose three reference victories.
The recurrent arm loses one net greedy victory and has negative return gains for
allthree races; reset has no net greedy gain and worsens Terran/Protoss returns.
Reset's Easy improvement does not satisfy the requested Hard scope. Sampled
recurrent improvement does not offset the failed greedy Hard gate.

## Training-only action support

An outcome-independent support count finds tanks observed in15/64recurrent games
and17/64reset games, medivacs in9and6, and starports in13and12. Battlecruisers have
zero legal decisions and zero selections across both arms. Accepted commands are
not completed production; snapshots do not count every unit produced. This
identifies scarce advanced-production experience, not a demonstrated primitive
bug or a strength result. Counts bind all128audited training action files and
remain separate from evaluation and fitting. Evidence:
logs/recurrent-memory/strength-analysis/training-coverage.json and
training_coverage.py. Current models and gates remain unchanged.

## Resources and preserved evidence

Training's1268two-second whole-machine CPU windows average14.47percent,peak31.41.
Evaluation's1062windows average13.33percent,peak23.32. Both stay below the80percent
guard, use no GPU and leave zero engines at completion. Keep native replays
unopened; no videos until the overall user goal is complete.

Protocol: [fixed study](2026-10-05-recurrent-strength-study.md).
Evidence: logs/recurrent-memory/strength-study/inputs.json,
train-summary.json,train-ledger.json,train-cpu-windows.json,
evaluate-summary.json,evaluate-ledger.json,evaluate-cpu-windows.json;
logs/audit/recurrent-strength-implementation-review.json,
recurrent-strength-first-batch-independent-review.json and
recurrent-strength-training-independent-review.json and
recurrent-strength-evaluation-independent-review.json.
