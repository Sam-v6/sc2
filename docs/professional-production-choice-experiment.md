# Professional production choice after primitive verification

October 7, 2026. The primitives-first reset now has native execution evidence
through the broad adapter, followed by one failed supervised choice experiment.
The full roadmap remains incomplete. None of this establishes learned Hard wins.

## Execution gate

`logs/roadmap/broad-production-combat-02` preserves three native VeryEasy/Macro
games on AcropolisLE, seeds 823221–823223, a 600-second game horizon and a
180-second wall bound per game. Its fixture submits scripted SCV, Barracks and
Marine requests through `JointImitationBot.on_step`; the loaded old checkpoint
is used only for engine-vocabulary setup, with no prediction calls. Request
history belongs to the fixture. Supply, worker scouting and combat are explicit
scripted assistance. The raw command and model interfaces remain intact.

| Opponent | Outcome | SCV births | Marine births | Completed Barracks | Raw/delayed errors |
|---|---|---:|---:|---:|---:|
| Terran | Scripted Victory | 8 | 114 | 5 | 0 |
| Zerg | Scripted Victory | 9 | 84 | 5 | 0 |
| Protoss | Scripted Victory | 9 | 82 | 5 | 0 |

Independent replay decoding verifies births and completed buildings. Native
observations/traces verify attack targets are currently visible, army movement
over 150 tiles from home, damage, kills, actor protection and separately counted
acknowledgements. Sampled host CPU peaks at 7.1%. These games verify basic economy,
construction, Marine production and combat through the adapter; they do not
exercise every Terran ability or replace the separate scripted 30/30 Hard panel.

The fixture targets four Barracks but counts foundations rather than all pending
builder orders; five complete. Treat that as a fixture planning limitation, not
a recommended production scheduler. A learned request scheduler must track an
accepted request through its observed effect before consuming it. The fixture
also deliberately extends no-request waits by eight loops; its protection
accounting follows that frozen behavior. The verifier checks the actual behavior,
not an assumed retry schedule. The preceding run01 stopped on a fixture-only
missing `orders` field; its failed receipt remains preserved.

## Fresh choice fit

`logs/roadmap/professional-choice-fit-01` binds the existing independently verified
professional corpus: 1,267 distinct teaching events and 289 reused diagnostic
events. Reserved games remain untouched. Inputs use the rich current-state entity
encoder and per-type status features. Human command history is empty; labels are
original verified production abilities, not future inventory quotas. All native
production families remain in the output vocabulary; no legality mask is used
for the reported choice accuracy.

The `ProductionComponent` has separate timing/choice heads over the existing
`GoalFirstPolicy.encode_context`. This fit starts fresh with seed 822103 and
never loads the failed timing weights. It uses 30 epochs, batch16, Adam .001,
game-balanced loss, 38,010 presentations, two CPU threads and no CUDA. The old
expanded GoalFirst checkpoint is evaluated on the same current observations,
without history and restricted to the same native production families.

| Frozen check | Observed | Result |
|---|---|---|
| Overall accuracy above teaching-majority baseline | 43.9% versus 38.8% | Pass |
| Nonworker recall at least 10 points above old checkpoint | 33.3% versus 14.7% | Pass |
| Building-choice recall at least 40% | 6/54, 11.1% | Fail |
| At least one correct building per diagnostic game | Two in each game | Pass |

An independent verifier loads the saved NPZ, reconstructs all current inputs,
checks history-reference columns are zero, recomputes all 289 probability vectors
and old-checkpoint choices, and reconstructs metrics and frozen gate outcomes.
Training/evaluation takes 39.4 seconds; sampled CPU peaks at 9.0%. No native
rollout or RL follows. The model is not promoted.

## Paired weighting result

`logs/roadmap/professional-choice-fit-02/verification.json` independently verifies
a failed paired experiment. The seed, sample order, fresh initialization,
optimizer, 30 epochs and 38,010 presentations match fit01. Only the family loss
weights changed: inverse square root of equal-game teaching prevalence, normalized
to mean one (building 1.7067, other .8320). Diagnostic labels did not set weights.
Overall accuracy is 115/289 (39.8%), nonworker recall 51/177 (28.8%), and building
recall 13/54 (24.1%, below the unchanged 40% gate). Each diagnostic game has correct
buildings, but false building choices are 37/235 (15.7%). Wall time 39.7 seconds,
sampled CPU peak 8.1%. No native rollout or RL; the model is not promoted.

The input audit under `logs/roadmap/professional-choice-input-audit-01` finds
recorded resources sufficient for one priced product on every building label.
This does not establish full actor-group affordability or command legality.
Producer order truncation occurs in seven teaching and one diagnostic building
observations. Player food used, idle-worker count and army count remain unknown.
Reflection of all coordinates changes only 9–16 of 289 top choices, with building
correctness 13–14/54. This is representation sensitivity, not a native mirrored
map test; orientation is unlikely to explain most errors. The choice context
does not consume map-grid features, so do not claim complete sensory coverage.

## What to change next

Building labels represent 236/1,267 teaching events and 54/289 diagnostic events.
The model predicts a building only 26/289 times. Most Depot labels are replaced
by SCV or Marine predictions; Barracks labels also get confused with Refineries.
The declared weighting experiment above improved building recall but failed.
The subsequent single [causal observation memory experiment](professional-observation-memory-experiment.md)
also failed, with building recall unchanged at 13/54. Close this comparison and
seek more compatible fully observed demonstrations or explicit expert corrections.
The completed experiment used earlier observations to expose recent economy and
production changes; it did not establish an aggregate benefit.
Preserve the evaluation gates and cap false building choices at fit02's 37/235.
Do not choose thresholds or weights by repeatedly optimizing these reused games,
add epochs indefinitely, or deploy a failed model.

If a model passes, connect it to an explicitly fixed scheduler: at most one
outstanding request, native actor/prerequisite checks, resource saving for the
selected request and observed-effect confirmation. An unaffordable building must
not be silently replaced by a cheap SCV. Supply/scouting/combat stay attributed
assistance. Start with a bounded native canary before all-race game competence
checks. Learned timing, broader command imitation, learned micro, RL improvement
and learned Hard/higher victories remain open roadmap requirements.
