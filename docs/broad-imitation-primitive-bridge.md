# Broad imitation controller: execution primitive bridge

October 7, 2026. The raw-command imitation adapter can now explicitly opt into
shared mining and combat primitives using `--primitive-assistance`. The broad
ability, actor group, target, queue, autocast and delay heads remain intact.
No model fit or RL ran during this change. This is an execution integration,
not a claim that imitation now wins games.

Previously `JointImitationBot` returned immediately whenever the learned agent
had no decision due. It had neither the shared mining/combat helpers nor their
between-decision cadence. The production-only experiment had these helpers,
but the full raw-command controller did not.

## Behavior and accounting

With assistance enabled, mining runs at intervals of at least 24 loops and
combat can run on intervening observations. Observation steps are capped at eight
loops, also respecting earlier learned decision times and the user's smaller cap.
An accepted learned command protects its actor group from assistance until the
next learned decision time. This preserves learned worker movement and army
orders during the model's wait. Construction helpers also retain their existing
builder protection and interruption-resumption behavior.

The shared helpers explicitly script mining/gas assignment, MULEs, Depot lowering,
construction resumption, attack destinations/timing and per-unit combat. They do
not train workers or soldiers or start production buildings. This adapter does
not yet include the fixed-plan reactive Depot assist or the production experiment's
WorkerScout. Supply construction and scouting decisions remain model requests.
All assistance and its native acknowledgements are logged separately from learned
commands and acknowledgements. Assistance never enters learned command history.

A related execution defect is corrected: a native-rejected learned command no
longer enters history or starts the predicted wait. Only an immediate success
acknowledgement does that. Submitted-command totals still include actual rejected
submissions, with results retained; `accepted` distinguishes them in the trace.
A success acknowledgement is not proof of a completed building or unit.
Later engine errors remain visible in observations and require their own diagnosis.

## Regression and native checks

New regression cases failed before implementation for missing assistance during
waits, missing assistance alongside protected learned actors, and erroneous
history after rejection. They now pass. Checks exercise the real mining/combat
helpers and raw action serialization, using a simulated native protocol boundary.
Existing construction-placement tests still pass. The full suite ran 555 tests
successfully, with 32 optional skips; Ruff and whitespace checks pass.

Two matched native canaries use the unchanged historical
`joint-professional-fit-05` checkpoint, AcropolisLE, Zerg VeryEasy/Macro, seed 820501,
90 game seconds, at most eight observation loops and a 90-second wall bound per
game. This checkpoint predates the newly repaired cohort; it was not promoted
or retrained. These games test the bridge rather than another unchanged model fit.

| Measure | Control | Assisted |
|---|---:|---:|
| Result | 90-second cutoff / Tie | 90-second cutoff / Tie |
| Learned command submissions | 9 | 9 |
| Scripted mining submissions | 0 | 13 |
| SCV births after opening | 3 | 3 |
| Final workers / supply cap | 15 / 15 | 15 / 15 |
| Final mineral bank | 1,055 | 1,075 |
| Raw / delayed action errors | 0 / 0 | 0 / 0 |
| Engine worker wall time | 23.699 seconds | 23.304 seconds |

Host CPU peaked 7.6% across the pair; GPU was disabled. The assisted trace contains
95 between-decision rows and 104 rows with model-controlled actors protected.
The independent verifier reconstructs learned history from successful submitted
commands, checks actor ownership and absence of assistance conflicts, verifies
separate acknowledgement totals, checks the absence of scripted production,
and reconstructs actual SCV births from the original replay tracker. Both games
have 13 original player-stat samples. Source, checkpoint and trace hashes validate.

Neither run builds a Depot or an army. The 20-mineral bank difference is not a
material strategy gain. Native combat was not exercised in this pair; the shared
combat primitive has separate scripted baseline evidence and actor conflicts are
covered by regression tests. Keep the broad model's macro failure explicit.
The completed scripted 30/30 Hard baseline remains a different controller/result.

## Artifacts and next action

`logs/roadmap/broad-primitive-canary-01` holds the frozen contract, two original
replays, raw traces, receipts, report, source snapshot and `verification.json`.
`run_broad_primitive_canary_01.py` is the bounded harness;
`verify_broad_primitive_canary_01.py` is rerunnable after completion.

The next learning experiment can use this opt-in bridge and the verified
[nine-game command cohort](human-command-cohort-recovery.md). It must learn usable
production decisions/timing from current observations, rather than standing future
inventory forecasts, and demonstrate actual supply, worker and military production.
Declare supply/scouting/micro assistance explicitly wherever enabled. Full raw
control, useful human imitation, micro learning/transfer, RL improvement and
learned Hard/higher wins remain unfinished. Do not replay this same failed old
checkpoint at higher difficulty or claim that scripted assistance is learning.
