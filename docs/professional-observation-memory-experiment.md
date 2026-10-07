# Professional production choice with earlier observations

The current-state choice model still fails building decisions after one declared
family-weighting experiment. Test whether recent observed economy and production
changes help; this is a hypothesis, not a diagnosed cause. Keep imitation and RL
distinct: this experiment trains on human examples only. No RL or native games
have occurred in this preparation.

## Verified data preparation

`logs/roadmap/professional-observation-memory-01/verification.json` has status
`verified_causal_observation_pointers_and_empty_command_features`. Preparation
and verification scripts live under `logs/roadmap/` as
`prepare_professional_observation_memory_01.py` and
`verify_professional_observation_memory_01.py`.

For each of the existing 1,267 teaching and 289 reused diagnostic target events,
select the latest actual source observation at or before target loop minus 45,
112 and 336 loops (approximately 2, 5 and 15 seconds at 22.4 loops/second). Ties
choose the last source row. Missing observations stay missing; never interpolate.
Pointers reference the full repaired `human-command-cohort-02/*/corpus/examples.jsonl.gz`,
not just production events. Source and target hashes are bound to the receipt.
Reserved games remain untouched.

The independent verifier uses a separate exhaustive selector, reconstructs every
pointer and target key, verifies strict chronology, and encodes all 2,382 distinct
past observations. All human-history reference columns and history slots are
empty. Only observation dictionaries enter encoding; source commands, delay,
label and game identity must not become model features.

Of 4,668 possible past-frame slots, 4,632 exist. Missing counts are 9, 9 and 18
for the three lags. Age ranges in loops are 45–385, 112–390 and 336–709; medians
59, 125 and 349. These command-event observations are sparse, not a dense fixed
cadence. Actual age and missing masks must be model inputs. Preparation verifies
selection and existing feature sanitization only, not memory-model behavior.

## One bounded model experiment

Keep fit02's labels, family weights, seed 822103, sample order, batch16, Adam .001,
30 epochs, CPU-only two-thread execution and 38,010 target-event presentations.
Report additional observation-frame exposure separately. Do not load failed
timing weights or introduce command history, queue-tail changes, spatial
augmentation, legality masks or another loss-weight sweep.

Use the existing shared observation encoder for current and past states. Add a
small recurrent contribution to current context with a zero-initialized output
projection: initial predictions must match the current-only model. Missing all
past states must bypass the contribution exactly, including after fitting.
Test initialization equivalence, gradients, save/load, missing-slot behavior,
actual ages and rejection of human history before implementation. Process past
states in chronological order, retaining their requested-slot masks and ages.

Before fitting, independently verify model inputs against the receipt. No model
implementation or fit is complete yet. Native inference must later maintain the
same causal bounded observation buffer, including observations between decisions;
do not validate offline history then substitute different history during play.

Frozen gates: overall accuracy above teaching-majority baseline; nonworker recall
at least ten percentage points above the old checkpoint; building recall at least
40%; at least one correct building per diagnostic game; false building choices
no more than 37/235 (fit02). Report every game and retain failures. These are reused
diagnostics, not fresh generalization evidence.

If it passes, independently reconstruct predictions and run a bounded native
canary with the verified primitives and explicit fixed scheduler. Actual learned
game competence remains necessary. If it fails, close this current representation
experiment and seek more compatible fully observed demonstrations or expert
corrections; do not keep sweeping memory length, epochs or weights. Do not infer
that professional intent is fundamentally impossible to learn from these failures.
