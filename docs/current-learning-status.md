# Current learning status

Updated October 7, 2026. The **initial scripted Hard baseline is verified**;
the basic production/combat adapter gate now also passes across all three races.
A separately declared scripted request fixture used the broad adapter and won
three VeryEasy games, with actual worker/Marine births, completed Barracks,
outward movement, visible-target attacks and zero action errors. CPU peaked 7.1%.
These are execution fixtures, not learned victories or an additional Hard panel.
One bounded professional production-choice fit then resumed; it is terminal and
failed its building-choice gate. RL remains paused. The scripted
baseline's 30/30 Hard wins do not establish reliable execution in that adapter.
Mining, combat and protected WorkerScout assistance are connected. The fresh
200-second native scout fixture verifies selection, protection, damage retreat
and observed return to mining, with zero raw/delayed errors and 5.4% sampled host
CPU peak. Production in that fixture was explicitly scripted; it proves execution,
not learned competence. Reactive supply is now available as an explicit
`--reactive-supply` assist alongside `--primitive-assistance`. Matched native
90-second checks verify one requested/completed Depot and supply cap 23 versus
15 in control, zero action errors and 23.8% sampled host CPU peak. The checkpoint
still makes nine submissions and no army. At loop 832 it requests Train Marine
from an SCV without a Barracks; all 1,185 unavailable requests repeat that action.
This is a model choice/actor error, not evidence that accepted unit training fails.
Check requested actions against actual income,
construction, production and combat effects before resuming learning.

The fresh current-state choice fit used 1,267 distinct professional events,
30 epochs / 38,010 presentations, with no failed timing weights, human history,
legality masks or native rollout. Independent verification recomputes all 289
diagnostic predictions: accuracy 43.9% versus 38.8% majority; nonworker recall
33.3% versus 14.7% old checkpoint; building recall only 6/54 (11.1%, required 40%).
Optimizer/evaluation wall time 39.4 seconds; sampled CPU peak 9.0%. The model is
not promoted. It predicts buildings only 26/289 times, versus 54 gold building
events; SCV/Marine choices dominate. The paired weighting experiment subsequently
failed too: building recall rose to 13/54 (24.1%, required 40%), overall accuracy
was 39.8%, and false building choices were 37/235 (15.7%). Independent verification
reconstructs all predictions; 38,010 presentations took 39.7 seconds with 8.1%
sampled host CPU peak. No native rollout or RL followed. Resource/queue and
reflection audits do not establish a dominant resource-corruption or orientation
cause. The subsequent single experiment tested earlier observations, without human
command history, rather than another weight/epoch sweep. Its causal snapshot
pointers are independently verified: 4,632 available frames from 2,382 distinct
past observations, with explicit ages and missing slots. The optional memory
component is now implemented and tested. Its single frozen fit independently
failed: building recall stayed 13/54 (24.1%), overall accuracy was 114/289 (39.4%),
and false building choices were 32/235 (13.6%). The extra 113,310 past-frame
encodings did not improve aggregate building recall. Wall time 148.6 seconds;
sampled host CPU peak 8.9%. No native rollout or RL followed. Close this planned
current-observation/memory comparison; seek more compatible fully observed human
demonstrations or explicit expert corrections, rather than weight, epoch or
memory-length sweeps on these reused games. See
[the observation memory experiment](professional-observation-memory-experiment.md).
See [the choice experiment](professional-production-choice-experiment.md).

The latest data preparation recovers five already cached professional games that
were omitted from the current choice corpus. Independent verification preserves
2,543 old commands and adds 944; all 3,487 states pass causal fog reconstruction.
Their 906 production events include 147 building events. Peak rebuild host CPU
5.6%; no fitting, downloads, native games or RL. These games were previously used
in broad imitation, are not fresh evaluation, and retain the same partial sensory
contract. Combined teaching coverage is now independently verified: 2,173
production events, including 383 building events, with original examples and
diagnostics preserved exactly. The single frozen data-expansion fit completes
65,190 target presentations in 68.7 seconds, at 8.0% sampled host CPU peak.
Independent verification reports overall 42.6%, nonworker 36.2%, building 22/54
(40.7%, clearing that gate), but false building choices 41/235 exceed the frozen
maximum 37/235. Overall status remains failed; no native rollout or RL follows.
Twenty-two false building choices cannot afford even one native-priced product.
The separate resource-only inference audit now passes its frozen offline checks:
144/289 correct (49.8%), nonworker 70/177 (39.5%), buildings unchanged at 22/54,
and false buildings 21/235 (8.9%). Independent verification reconstructs every
probability vector and filtered choice. No weights or gates change. A small tested
helper is available, but native play is not wired yet; native availability,
pending requests, supply, actors and placement still need verification. Next run
a bounded native conditional-choice canary through verified primitives, retaining
matching observation projection and explicit assistance. Inspect any first
choice-to-effect failure for expert corrections; do not reopen arbitrary sweeps.
See [the resource inference audit](professional-resource-filter-experiment.md) and
[the data comparison](professional-choice-data-expansion-experiment.md).

The subsequent native conditional-choice canary is terminal and failed. Independent
verification reconstructs788 predictions and72 successful immediate production
acknowledgements; traces show25new SCVs,8completed production buildings and15new
observed combat units (MULEs excluded). A Depot at loop10565 later receives
`CantBuildLocationInvalid` at10684. The prototype misses that delayed failure,
holds a global pending request and aborts after448loops. It also uses empty placement
spacing reservations and releases builder protection before a foundation appears.
Wall69.0seconds, host CPU peak6.4%. No completed replay, victory or RL follows.
Next repair and test construction follow-through and physical placement before
a fresh canary; weak army output and excess buildings remain model concerns.
See [the native canary diagnosis](professional-choice-native-canary.md).

Construction follow-through is now repaired and tested: delayed errors, real
foundation/addon effects, pending actor protection, physical spacing, grid-center
alignment, reachable builder selection and route-aware timeout. Native04 reaches
the600-second cutoff normally, with zero action errors and a saved replay.
Independent verification reconstructs911 predictions and pending protection;
replay decoding proves28new SCVs,8completed production buildings and16military
births. Military remains below the unchanged20-unit gate; result Tie, no victory
or RL claim. Wall56.6seconds; host CPU peak24.1% including concurrent tests.
Full suite595tests/40optional skips. A native query audit identifies17building
choices that replace higher-probability available training solely because our
actor rule rejects busy producers (9Marines,6SCVs,1Reaper,1Medivac). Next test
bounded training queues before retraining the model; native resource/supply guards
and explicit assistance must remain intact.
See [the additional command recovery](additional-professional-command-recovery.md).

The latest mixed-source timing fit is terminal and failed its frozen gates.
Independent verification found no qualifying cutoff on calibration or either
evaluation game. Its diagnostic cutoff is unqualified; no production-choice
fit, native rollout or RL followed. Evidence is preserved under
`logs/roadmap/mixed-production-fit-01/`. The data-readiness records below describe
earlier preparation, not the current next action.
The [mixed-source data preparation](mixed-source-production-data.md) is terminal
and independently verified: native teaching supplies 467 production / 1,002 wait / 205
unknown intervals; all eight games cover 99.85% elapsed time at actual 44-loop cadence.
Professional choice has 1,267 distinct teaching and 289 diagnostic events, no future
windows. Native teaching is five Mez games; Lyra calibrates, Huski/Rom evaluate,
all reused diagnostics clearly labeled. Reserved games unchanged. Source naming
repairs require native catalogue proof; uncertain commands stay censored.
Full suite 570 tests / 32 optional skips, CPU peak 23.2%, no fit/predictions/bot games/RL.
The planned mixed-source timing/choice experiment subsequently failed the timing
gate described above; this preparation establishes data readiness only.
The [mixed-source production experiment](mixed-source-production-experiment.md)
now has a verified dense-data pilot: reused diagnostic Rom yields 120 states
every 44 loops, preserves all 299 native actions, and covers 99.87% of elapsed
time, at 6.6% CPU peak. This is Masters data, not professional provenance.
Next audit production-specific human issuance and prepare existing native source
splits, then test Masters timing plus professional choice under frozen gates.
No fit, model prediction or RL has occurred; reserved games remain untouched.
The [production timing coverage audit](human-production-timing-coverage.md) closes
the proposed two-second act/wait fit without training: source-backed classification
leaves 619/1,557 teaching intervals unknown, only 122 confirmed waits, and 20–25%
of elapsed game time uncovered. Both source-state and interval verifiers pass.
Full suite now 560 tests / 32 optional skips. Resolve quiet-period coverage before
learning timing; verified command identities remain useful, but scripted cadence
would need explicit attribution. No training, simulation or RL in this audit.
The [broad-controller primitive bridge](broad-imitation-primitive-bridge.md) now
passes regression checks and two native integration canaries. Its opt-in mining
and combat assistance runs during model waits, protects model-controlled actors,
and stays separate from learned history. Rejected learned actions no longer start
waits or enter history. Full suite: 555 tests, 32 optional skips. Native pair:
13 assisted mining submissions, zero action errors, 7.6% host CPU peak. Both are
90-second cutoffs with 15 workers and no Depot/army; the old checkpoint still
fails macro, and no training or strength claim follows. This broad adapter
did not include reactive supply or WorkerScout at that initial snapshot; both now
have separately documented native execution checks, with supply explicitly opt-in.
The [nine-game command cohort recovery](human-command-cohort-recovery.md) is now
terminal and independently verified: 6,748 command labels, including 1,737
recovered commands (227 production commands), with preserved owned/player/map
fields and independently reconstructed enemy visibility/memory. Teaching has
5,099 labels; reused diagnostics have 1,649. Two teaching games are human losses,
explicitly retained; reserved games remain untouched. The causal next-production
label audit verifies 2,527 teaching and 645 diagnostic windows, censoring 3,576 windows
across unknown events or absent next production. These windows are not independent
decisions or immediate execution instructions. No model fit, simulation or RL
ran during this preparation. Next connect current-state command/timing decisions
to current legal execution, preserving the verified mining/supply/combat assists;
do not rerun future-count forecasts or tune fixed replay playback indefinitely.
The [command-repeat recovery](human-command-repeat-recovery.md) now independently
verifies305 newly recovered human labels, preserving all851 previous labels and
player/unit/map observations. The reimported winning game contains1156 labels.
Command-manager repetitions and target updates carry original provenance outside
observations;399 uncertain contexts remain explicit unknown history slots.
The [worker-queue diagnosis](human-worker-queue-diagnosis.md) restores four issued
requests previously misclassified by unchanged queue counts; plan06 has247
instructions. The [reactive-supply experiment](reactive-supply-assistance-result.md)
now verifies53 SCV births versus45 without assistance at the same cutoff9224,
near the source's55. Confirmed worker queue stalls fall159.29→10 combined
producer-seconds. Native25 resolves187/247 and reaches the same later Cyclone
funding deadline10552 as native22. Two extra Depots complete; a third is under
construction. All seven supply warnings retain matching queued orders, with no
other action errors; CPU peaks8.1%. This is explicit scripted supply priority
through a fixed human plan, not learned supply behavior or a victory. Use the
verified assist in the next state-conditioned imitation-execution experiment.
The [reservation canary](resource-reservation-canary-result.md) passes saved-state
checks but fails earlier on a Depot/Factory geometry collision, so it is not
promoted. Keep exact playback as a regression corpus and its gate incomplete;
stop priority sweeps and return to learned current-state decisions. Training and RL remain paused.
The [gas-assignment ablation](gas-assignment-ablation-result.md) reduces worker
switching but does not improve funding or execution timing. The experimental
option was removed; the verified supply-assisted behavior remains unchanged.
The [producer topology audit](human-producer-topology.md) and
[earlier fixed-plan diagnosis](fixed-human-plan-native-result.md) remain partial
evidence. Useful imitation and complete source command coverage remain unproven.
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
[winning-game queue audit](human-production-queue-audit.md) historically classified220queue
increases and four repeated/present orders; the four classifications are now
superseded by completion-window and queue-truncation counterexamples, but zero imported addon commands
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

### Bounded native production queues verified

Native 05 fixes the demonstrated idle-only producer restriction without model
changes: 27 explicit queued training requests each produce a one-to-two native
order transition. It completes the matched 600-second cutoff with zero errors,
26 replay SCV births, 17 military births and 15 completed production buildings.
The frozen military minimum of 20 remains unmet. Verification recomputes 948
prediction vectors; sampled host CPU peak is 7.2 percent. All 598 default tests
pass (40 optional skips). See [the native canary record](professional-choice-native-canary.md).

Of 40 building decisions, 32 prefer buildings even when funded native-available
training remains eligible. This locates a remaining decoder/model decision problem; raw probabilities
must be audited before attributing the selected fallback to the model. Keep imitation and RL training paused
while inspecting remaining production constraints and offensive/micro effects.

### Concurrent execution works; conditional decisions still fail

A further audit finds 177.9 game seconds globally blocked on one pending
construction request in native 05. The army never reaches the scripted 40-supply
offense threshold. Native 06's concurrent prototype exposes a queued SCV rollover
tracking bug; the tested repair and pending-actor protection produce a terminal
native 07 with zero errors, 45 concurrent selections, 675 protected pending actor
observations and 1,172 recomputed model predictions. All 599 default tests pass
(40 optional skips).

Native 07's strategy is worse: 50 SCV births, 12 military births, only one
completed producer and 37 Bunker requests. The 600-second Tie cutoff saves a
replay; military and building gates fail. CPU peak is 23.4 percent, wall time
83.816 seconds. Execution repairs do not establish model competence. Keep the
full goal active and consult the existing authorized Astra adviser about the
next human-imitation formulation before another fitting sweep. No RL is running.
See [the detailed native diagnosis](professional-choice-native-canary.md).

### Corrected Bunker diagnosis and frozen decoder comparison

All 37 native 07 Bunkers displaced an unaffordable raw top model prediction:
27 Factories, nine Starports, one Barracks. The cheaper fallback consumes funds
needed for the preferred capacity. Earlier attribution of Bunker purchases to
raw model preferences was too broad. Parent and existing Astra adviser agree.

A frozen same-checkpoint matched pair compares native 08 fallback with native
09 persistent resource-reserved intent. Native 08 reproduces the 37 Bunkers,
12 military births and one completed producer. Its recorded native queries
verify insufficient funds are ignored while missing building prerequisites are
retained. The second arm is bounded by the unchanged 600-second cutoff, gates,
80-percent CPU ceiling and a 60-second unissued-intent stall abort. All 602
default tests pass (40 optional skips). No training or RL.

### Reserved-intent comparison interrupted by gas targeting

The frozen pair is terminal and closed as interrupted. Native 09 recomputes
473 predictions and verifies 17 submitted intents, then aborts on its eighteenth
intent: a Refinery targeting a still-observed neutral geyser beneath an owned
completed Refinery. Placement result 42 blocks submission; no action errors or
normal completion. CPU peak 6.4 percent, wall time 18.491 seconds. The
`claimed_geysers` helper now includes owned gas buildings, with a captured-state
regression observed red before the fix. All 603 default tests pass (40 skips).

The canary's starting-base-only gas search also omits two observed free geysers
near its completed expansion. The existing production-goal controller's broader
observed-target handling is a reference to reuse. Next verify occupied exclusion
and expansion targeting in a native primitive fixture. Do not repeat fitting or
claim this interrupted pair demonstrates reservation efficacy. See the detailed
[canary record](professional-choice-native-canary.md); the full goal stays active.

### Expansion gas execution now independently verified

The shared `refinery_sites` helper includes free observed gas near completed
owned expansion bases and excludes occupied gas, unfinished bases and flying
bases. The production-goal controller now uses it. A captured-position regression
is observed failing before implementation. All 604 default tests pass (40 skips),
with Ruff/diff checks passing.

The native `refinery-expansion-fixture-03` verifies three actual Refinery starts
and completions from replay events, including expansion construction followed
by 188 gas extracted there. There are zero errors and a normal 120-second cutoff.
Wall time 10.197 seconds; host CPU peak 5.8 percent. Debug resources, a pre-created
expansion CommandCenter and four added SCVs isolate execution; this is not a
learned macro or game-strength result. Prior two harness failures remain saved.

Next wire the verified gas targeting into both fresh policy comparison arms.
The earlier interrupted pair and failing gates remain unchanged. Continue with
the frozen model and explicit intent budgets before deciding whether another
imitation fit is warranted; RL stays paused.

### Reserved intent passes matched production gates; actual wins still unproven

After the verified gas repair, the same-checkpoint matched pair is independently
verified: fallback produces zero military units/producers; reserved intent
produces 26 military births and 17 completed producers, with 52 new SCVs and zero
errors. All original production gates pass for reserved intent. Both games are
600-second cutoff Ties, and 20 Factory requests show remaining overbuilding.
See [the detailed canary record](professional-choice-native-canary.md).

The first actual-game three-race panel stops in Terran on a unit-target Refinery
travel timeout; the timer includes point-target travel but omits gas travel.
The second attempt queries the blocked geyser centre and withholds a legal
build. Both failed panels are preserved; other races are unattempted. Shared
`command_point` and `builder_approach_points` helpers now resolve target geometry
and offer outside-footprint route candidates. The native refinery fixture 04
verifies centres return zero, approach paths are positive, all three Refineries
complete, and expansion gas is harvested without errors. All 606 default tests
pass (40 optional skips), with Ruff/diff checks passing.

Current live work: `reserved-choice-competence-03`, using the frozen model and
`run_professional_choice_native_13.py`, three sequential 1,200-second VeryEasy
games with original panel seeds, 300-second wall limits and 80-percent CPU guard.
Check its actual process/receipt before restarting or counting outcomes. The
full learned Hard/higher and broad human-imitation roadmap remains active; RL
stays paused.

### Competence panel 03 has stopped; inspect layout feedback next

The formerly live panel is now terminal after its first Terran game: a Factory
intent stalls for 60 game seconds because the normal placement seed and both
owned-base fallbacks find no complete Factory/addon-pad site. Last logged loop
13948 has 2,930 minerals/2,044 gas, no pending requests, 86 workers and 19
military units. Four accepted Refineries carry positive approach-route queries
and travel allowances, with zero observed action errors. The earlier travel
limit is repaired, but no actual win or all-race result is established.

`reserved-choice-competence-03/failure-audit.json` binds the diagnosis. Zerg and
Protoss are unattempted; the callback abort saves no final replay. Next make
physical placement rejection explicit in intent handling, separate from funding
waits and model overbuilding. No source-bound process is live now. All 606
default tests pass (40 optional skips); full roadmap and learned Hard competence
remain incomplete, and RL stays paused.

### Placement feedback and the next loss mechanism (2026-10-07)

`reserved-choice-competence-04` is terminal. Frozen checkpoint and matched Terran
seed824201; no fitting or RL. The new native14 wrapper invalidates a physically
rejected placement/path intent, releases its reservation, and withholds that
ability for224loops (10game seconds) before rechecking. Funding waits retain
intent. This changes execution feedback only; placement clearance, strategy
scores and quotas remain unchanged. Shared preference selection has two focused
regressions; all608 default tests pass (40 optional skips), and Ruff passes.

Saved source hashes were rechecked against the normalized snapshot. The trace
records20 physical rejections and69 accepted commands after the first rejection,
so the previous placement rejection no longer holds the controller for60seconds.
The game instead aborts106.441wall seconds later on a Hellion intent atloop18136
(last savedloop18128), after60game seconds waiting. Last player has1890minerals,
2528gas,200/200supply,116workers,84army supply,44military units,zero idleworkers,
and no pending requests. Three supply-cap action errors (code14) appear twice
each in trace phases. Peak measured whole-host CPU22.1percent. There is no normal
finish or replay; Zerg/Protoss were not attempted. No win is established.

`logs/roadmap/reserved-choice-competence-04/failure-audit.json` records the evidence.
Next distinguish supply blocking from technical/resource availability, including
queued supply, and audit why the model continues producing workers at fixed
cadence. Do not hide that macro defect with an unexplained worker cap or count
these partial production gains as human imitation success. Training/RL remains
paused and no source-bound process is live.
