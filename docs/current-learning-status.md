# Current learning status

Updated October 7, 2026. The **initial scripted Hard baseline is verified**;
the active next phase is reconnecting human imitation to the verified primitives.
The [fixed-plan native diagnosis](fixed-human-plan-native-result.md) now verifies
actual Factory attachment through a shared Tech Lab, stable producer/worker
bindings and nine original builder movements. The latest bounded canary resolves
127 of212 instructions with zero delayed action errors before stopping on a
missing source Factory. Its original replay uses a command-target update omitted
by the importer; inherited ability and worker selection must be recovered next.
These are forced diagnostic exits against VeryEasy, not learned victories.
The [producer topology audit](human-producer-topology.md) and
[203-command source compilation](fixed-human-production-plan.md) remain useful
partial evidence. The expanded fixed plan has212 instructions; useful imitation
and complete source command coverage remain unproven.
Research queue accounting now preserves specific upgrade levels, and specific
level-one availability no longer permits level-two requests. These fixes pass
regression tests using the specific command IDs observed in the native research
fixture. Generic multi-level source orders remain ambiguous; no new game-strength
claim or training restart follows from this repair.
The [human ordering experiment](human-production-precedence-result.md) has now
failed its quality gates; its simple human-derived majority baseline performed
better. The [native execution comparison](human-prior-native-result.md) found
and corrected an expiry stall. A fresh positive-rearm canary passes its engineering
gate: Barracks by 51 seconds, six Marines and 34 workers at four minutes. The
six-game all-race development panel is [verified](human-prior-development-panel-result.md):
production continues in all games, but zero victories and 54–78 Depot starts expose
repeated spending from standing forecasts. The [cadence diagnostic](human-production-cadence-result.md) reduces this to
14 Depots, but still banks 7,000 minerals with only one Barracks. Its opening gate
passes; its strict one-Depot cadence gate does not. The [inventory label audit and first fit](human-inventory-target-result.md) now
verify: labels are usable, but the regressor fails production-capacity accuracy.
The [protected scouting transfer](human-scout-transfer-result.md) now passes a
native canary: enemy vision by139seconds, damage retreat and return to mining.
The [human-goal retrieval audit](human-goal-retrieval-result.md) independently
verifies source selection and held targets. The final shortage state retrieves
seven Barracks and three Factories; this is offline evidence, not a native win.
Absolute inventory deficits and intent retirement now pass tests and native
reconstruction. The [matched inventory comparison](human-inventory-native-result.md)
is closed as failed: more capacity and lower mineral bank, but fewer workers,
insufficient military growth and more supply blocking; both games Tie. The [owned-base placement repair](owned-base-placement-result.md) now verifies:
zero placement failures, two extra completed Barracks, seven production buildings;
still Tie with52SCVs and70.71seconds supply blocking. The
[demonstration quality audit](human-demonstration-quality.md) finds the dominant
retrieved example is a loss; successful economic coverage and addon execution
remain concerns. The updated primitives won three fresh Hard Rush games, one
per race, with independently verified production and zero action errors. The
adviser recommends testing execution of one fixed winning human production plan
before fitting another policy. First audit whether the existing converted source
can distinguish new production orders, repeats, cancellations and addon changes;
the original replay needs an unavailable engine version. The
[winning-game queue audit](human-production-queue-audit.md) now verifies220queue
increases and four repeated/present orders, but zero imported addon commands
despite nine original own addon starts. The
[source-backed Lift/Land repair](human-lift-land-recovery.md) recovers32commands
and preserves all804oldlabels in a fresh teaching-game rebuild. The
[addon relocation repair](human-addon-recovery.md) adds three verified point
commands, giving839labels, and four native fixtures prove build-in-place versus
relocation behavior. The
[early in-place addon conversion](human-in-place-addon-recovery.md) now verifies
three more canonical execution labels with original provenance and no effect
leakage, giving842labels. Two later grouped/flagged commands remain excluded.
The
[production metadata repair](human-production-metadata-recovery.md) now verifies
eight Viking/research labels and one snapshot-based Refinery label, giving851.
The Refinery target remains unavailable in current raw-command inputs. A live
research goal pointer bug is fixed and independently verifies accepted research
with rising order progress. Next resolve cancellation, producer/addon binding and
ambiguous generic source research orders before the fixed-plan test. Do not infer exact paid
production starts from eventual unit births.
No promotion, unchanged fit or RL restart.
RL remains paused. The full roadmap is incomplete, and scripted victories are
not learned-controller victories.

The [Terran primitives controller](terran-primitives-implementation.md) won all
30 fresh baseline games: ten per race, five named strategies, two maps. Original
replays, tracker production, sampled visibility/weapon compatibility and action
failure accounting independently verify. Whole-host CPU peaked at 9.3 percent.
Jobs requested API Hard (value 5); the engine names this opponent Harder in replays.
See [the baseline result](scripted-hard-baseline.md) for exact scope and limits.

The [repaired human corpus](human-visibility-repair.md) is independently verified:
all 7,202 original command labels and own-unit observations are preserved.
6,083 teaching and 1,112 development commands are representable, with explicit
unsupported-target exclusions. The native executor now uses the mining/combat primitives. A fresh supervised
fit passes independently verified offline checks, but its first native canary
failed to build an army. See [the bridge result](human-primitives-bridge-result.md).
Do not rerun the unchanged full-command fit or credit scripted assistance as learning.
The [opening-order diagnosis](human-production-order-diagnosis.md) records the
additional command and input-sensitivity audits; unchanged outcome timing also
failed its quality gates.

Start here, then read [the roadmap](learning-roadmap.md). Use
[the execution ledger](learning-execution.md) for detailed evidence. Historical
experiments are references, not an instruction to rerun every failed variant.

| Requirement | Current evidence | Still needed |
|---|---|---|
| Reliable execution primitives and scripted baseline | Verified 30/30 fresh scripted wins; initial all-race gate passes | Reconnect the verified primitives to human decisions; retain baseline and audit rare action failures |
| Broad gameplay controls and player-visible information | Raw command schema, native catalogue, missing-field masks, fog filtering and argument execution exist | Prove the learned controller uses the necessary controls reliably, including simultaneous unit control |
| Strong human examples | Eleven professional teaching games: 6,089 verified decisions, 6,083 representable after visibility repair; whole-game development split and untouched reserved games | More varied verified data and human development Terran coverage (teaching already has two TvT games); resolve unavailable observations where actual source evidence permits |
| Learn to copy human decisions | Full command imitation failed; fresh production-outcome fit passes offline; native all-race sustained production verifies, but macro overproduction and zero development victories remain | Useful generalization and actual game competence |
| Learn better micro in a sandbox | Sandbox/training infrastructure and earlier experiments exist | Reliable held-out improvement and transfer to the full controller |
| Learn beyond humans through RL | Earlier constrained experiments exist | Resume only after a useful imitation starting point; prove improvement on fresh games |
| Beat Hard reliably, then harder opponents | Scripted baseline 30/30; earlier constrained macro policy had partial learned success | Full-roadmap learned controller must pass its own all-race Hard panel and harder evaluations |
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
