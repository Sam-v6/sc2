# Current learning status

Updated October 6, 2026. The active phase is **loss diagnosis and reliable
primitives**. Human-imitation training and reinforcement learning are paused.
The full roadmap remains incomplete. The user explicitly authorized using
established bots to build reliable resource, production, attacking and combat
micro behavior before returning to professional imitation, then RL.

The [Terran primitives controller](terran-primitives-implementation.md) passes its
native smoke and 454-test suite. Wider construction spacing repaired trapped
Tanks, and the six-game all-race development panel now wins all six games,
independently verified. The Adept-shade attack exclusion is also repaired.
A fresh 30-game scripted Hard baseline panel is running in
`logs/roadmap/primitives-hard-baseline-01/panel`: ten games per race, five named
strategies, two maps, fresh seeds, with gates of21/30overall and7/10perrace.
This is scripted execution, not learned competence. Imitation and RL stay paused.
The human visibility audit identified a feature/native coordinate mismatch; the
importer is repaired, but existing corpora still require re-import and verification.

Start here, then read [the roadmap](learning-roadmap.md). Use
[the execution ledger](learning-execution.md) for detailed evidence. Historical
experiments are references, not an instruction to rerun every failed variant.

| Requirement | Current evidence | Still needed |
|---|---|---|
| Reliable execution primitives and scripted baseline | Tank exit blockage repaired; all six development games win; fresh baseline panel active | Finish and verify fresh baseline panel; inspect strategy/map/race failures |
| Broad gameplay controls and player-visible information | Raw command schema, native catalogue, missing-field masks, fog filtering and argument execution exist | Prove the learned controller uses the necessary controls reliably, including simultaneous unit control |
| Strong human examples | Eleven professional teaching games: 6,089 verified decisions, 6,086 representable; whole-game development split and untouched reserved games | More varied verified data, including Terran opponents; resolve unavailable observations where actual source evidence permits |
| Learn to copy human decisions | Full command imitation failed; simultaneous production-outcome imitation passes offline gates | Useful generalization and actual game competence |
| Learn better micro in a sandbox | Sandbox/training infrastructure and earlier experiments exist | Reliable held-out improvement and transfer to the full controller |
| Learn beyond humans through RL | Earlier constrained experiments exist | Resume only after a useful imitation starting point; prove improvement on fresh games |
| Beat Hard reliably, then harder opponents | Earlier constrained macro policy had partial Hard success | Full-roadmap controller must meet the defined all-race Hard panel and subsequent harder evaluations |
| Observe games/replays | Headless capture and prior Linux replay-to-video export exist | Keep artifacts usable; user does not want replay demonstrations before the goal is complete |

## What the recent experiments showed

The source repair recovered 146 professional production commands. Given the
correct ability and actors, the repaired model copied all 146 command arguments
on those teaching states. Its ordinary development performance did not improve.
This identifies a bottleneck on that subset, not a competent controller.

Predicting the next human production choice separately also generalized poorly.
A model using recent human actions fit 97.5 percent of teaching choices but only
30.4 percent in other games. Current-state trees recovered more uncommon building
choices than a linear model, but overall accuracy still trailed the worker-majority
baseline. These are offline diagnostics, not game strength.

Five additional verified professional games now add 2,543 decisions. The expanded
full-command fit uses the same maximum 6,390 optimizer updates / 101,940 example
presentations as the previous fit. Increased source coverage and teaching-only
support are the intervention. No training-budget extension or architecture sweep.

## Latest completed run

The expanded human-imitation run and independent verification are terminal.
All 30 epochs completed: 6,390 updates and 101,940 presentations, exposing all
6,086 representable teaching examples. Verification reconstructed 7,202 ordinary
predictions, 1,113 own-history predictions and the exact exposure schedule.

| Previously used development measure | Prior model | Expanded corpus |
|---|---:|---:|
| Production ability correct | 21/262 | 27/262 |
| Complete command correct | 28/1,113 | 30/1,113 |
| Production correct using own predicted history | 4/262 | 3/262 |

All three learning gain gates failed. Correct production choices were 26 workers
and one Marauder; no building decisions were correct. No native game or RL
followed. See [the closed result](superpowers/plans/2026-10-06-expanded-professional-imitation-results.md).

The CPU-only two-thread jobs used an 80 percent whole-host guard on three
consecutive samples, not a hard instantaneous cap. Fitting peaked at 93.3 percent;
the successful verification retry peaked at 99.6 percent. The first verification
attempt was stopped by the guard. No GPU workload was used.

## Current implementation direction

The simultaneous production-outcome model now passes its frozen offline gates.
It uses5,378teaching windows and976development windows over52families; labels,
checkpoint predictions and metrics independently verify. Building positive
precision/recall are52.4/57.5percent; military75.8/78.2percent. Fit19.78seconds,
CPU-only two threads, peak19percent whole-host CPU. No native competence claim.
See [verified result and limits](superpowers/plans/2026-10-06-human-production-goals-results.md).

The generic native executor is integrated and the frozen six-game Hard panel
is independently verified. All three Macro games sustained learned production;
all three Rush games failed. Results: zero wins, three defeats, three ten-minute
cutoffs. Macro worker peaks40/49/48and military peaks27/28/29. Panel CPU peak27.2percent.
See [native result and diagnosed issues](superpowers/plans/2026-10-06-human-production-goals-native-results.md).

Addon caster and production clearance repairs are now natively checked. The
same frozen six-game panel starts Factory TechLabs in all six games and records
no delayed action errors. Still zero wins: three Rush defeats and three Macro
cutoffs. Macro worker peaks decline to35/31/37; military peaks29/25/30.
CPU peak30.1percent. See [repair results and limits](superpowers/plans/2026-10-06-production-clearance-results.md).

The timing audit found affordable idle worker-production opportunities and large
spare supply in saved Macro games; this is diagnostic evidence, not proof of a
single cause. A saved timing-model experiment failed its baseline and family
error gates on reevaluation and was not deployed. Preserve that unfinished
experiment as historical work; do not resume fitting it by default.

Next resolve the scripted Terran cutoffs with native trace evidence, then test a
fresh all-race panel. Established Sharpy and Burny bot code has been inspected
and pinned as design references; the unchanged Reaper reference lost all six
local development games. See [the primitives diagnosis](primitives-reset-2026-10-06.md).
Do not restart imitation or RL to compensate for unreliable execution.
