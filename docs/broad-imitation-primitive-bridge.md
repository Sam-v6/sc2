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
not train workers or soldiers or start production buildings. This adapter now
includes the production experiment's protected WorkerScout, with selection,
damage/deadline return and learned-actor protection. Scout events and commands
are separately logged; they never enter learned history. Explicit
`--reactive-supply` now enables scripted Depot assistance as well. Without it,
supply construction remains a model request. It requires `--primitive-assistance`.
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

The scout transfer adds two integration regressions, observed failing before the
change and passing afterward. The full suite now passes 576 tests, with 36 optional
skips. `logs/roadmap/broad-scout-canary-02` preserves a native execution fixture,
replay, observations, frozen source, contract and independent verification. Its
production was the existing scripted baseline; the actual assistance call was
`JointImitationBot.run_primitives`. One scout was selected at loop 1928, protected
through 126 observations, returned after damage at loop 2928, and had an observed
mining order at loop 2936. All assistance acknowledgements succeeded, delayed
errors were absent, collected minerals reached 2,810 and sampled CPU peaked 5.4%.
The 200-second cutoff is not a victory or learned competence result. The preceding
fixture `broad-scout-canary-01` failed because the baseline's own scouting routine
reclaimed the adapter scout; its failed receipt is preserved, not counted as a pass.

Further imitation and RL are paused. Supply coordination is now verified as below;
next exercise production and combat through this adapter with explicit execution
fixtures, then reconnect useful human decisions. A scripted fixture is not a
learned competence result.

### Reactive supply transfer

Supply assistance uses the existing queue-aware supply rule, native availability,
placement and builder pathing queries. It protects a newly accepted builder until
the observation echoes the order or foundation; an absent echo after 44 loops is
an explicit timeout event. Existing foundations/orders suppress duplicate requests.
Successful model production on the same step reserves its mineral cost and
construction footprint/addon space before supply is considered. All assistance
stays outside learned history. Generic addon prices require agreement between
native alias products; ambiguous prices still fail instead of being guessed.

Four integration tests cover supply during model waits, pending builder protection,
same-step spending, existing/model-requested Depots and building-site conflicts.
The full suite passes 581 tests, with 36 optional skips; Ruff and whitespace checks
pass. Native catalogue checks price generic and specific TechLabs at 50/25 and
Reactors at 50/50 minerals/gas.

`logs/roadmap/broad-supply-canary-01` binds two 90-second games, the same frozen
historical checkpoint and seed 823101. Both use mining/scouting/combat assistance;
only the second enables reactive supply. The independent replay/trace verifier
confirms one scripted Depot submission and one completed Depot, raising the cap
from 15 to 23. Control has none and remains at 15. Both have three SCV births,
15 workers, nine model submissions, no army and zero raw/delayed errors. Sampled
host CPU peaks at 23.8%. These are cutoffs, not victories.

The first unavailable model request at loop 832 is Train Marine (560) from SCV
4349231105, with no Barracks present. All 1,185 unavailable requests repeat Train
Marine. Supply execution is repaired, but this checkpoint's choice and actor
selection are unusable. Do not rerun it hoping that additional supply will teach
it production. Source snapshots preserve the native-tested code; the subsequent
generic-addon price repair has separate regression and native-catalogue checks.

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
