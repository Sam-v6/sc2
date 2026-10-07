# Active roadmap execution

The user resumed the roadmap on October 5, 2026. The earlier
[requested-pause status](project-status-2026-10-05.md) is a historical snapshot.
The roadmap is not complete. Keep the previous narrow macro experiments frozen.

Implementation is in `.worktrees/terran-rl`, branch `Sam-v6/terran-rl`.
The commands below run from that worktree. Run artifacts are ignored under
`logs/roadmap/`; preserve those directories when handing off or archiving.

## Current evidence

| Gate | Implemented and checked | Remaining |
| --- | --- | --- |
| A: shared controls | Raw ability, unit group, unit/point target, queue and autocast schema; full visible-map entities, scouting memory, map grids, recent commands; hidden-health checks; debug census of 52 Terran states and 121 queried abilities | Contextual ability states, physical execution beyond representative families and learned selection |
| B: replay extraction | Matching-build preflight; fog enabled; observation before command; sixteen source-labelled human games from four Terran players reconstructed; issued-command repeats audited; unresolved timing intervals masked | Verified professional Terran games, wider player coverage and issued/executed event audit |
| C: imitation | Consistent five-game component pipeline; expanded nine-game macro fit; staged command audits; raw unit groups, arguments and delay labels | Shared entity/context learning, consistent expanded full-command fit, worker selection/queue execution, independent-player transfer and useful live-game competence |
| D: micro | Native DefeatRoaches adapter using shared entities/commands; trace, scores and replay; CPU-only return-driven policy search; held-out combat-score gains; ordinary-game transfer measured | Other scenarios and successful full-game transfer |
| E: full-game RL | Historical CPU raw-ability PPO bridge and native collection/update/paired evaluation; combat-return mechanism experiments; all RL currently held for human imitation | Native wins over frozen imitation; learned arguments and durable competence |
| F: Hard and beyond | Historical narrow learner development results remain documented | Reliable fresh all-race wins, map/build variation, harder evaluations |

The interface fixture `logs/roadmap/interface-third/` physically checked SCV
production, construction, healing, siege/unsiege, independently moved Marines
and queued orders. All nine checks and nine command results succeeded. It uses
debug setup and is engineering evidence, not learned competence.

The scripted nearest-target micro baseline
`logs/roadmap/roaches-baseline-first/` lost: 99 frames, 509 successful commands,
545.13 damage dealt, 392 damage taken, 200 killed value, 17.5 game seconds.
The first search is `logs/roadmap/micro-search-01/`, four generations of twelve
candidates, two workers, 60-game-second horizon. Hypothesis: independent targeting
and cooldown-aware movement can improve combat return without scripted timing.
Reward is killed value + 0.2 damage dealt - 0.5 damage taken + survival seconds
+ 1000 for native Victory. Stop after the bounded batch and compare on fresh seeds;
worker failures abort rather than becoming training returns. This compact linear
movement/targeting controller is an explicit initial micro experiment, not the
final broad-action Terran policy. Survival shaping can encourage fleeing; report
kills/damage separately and test transfer before promotion.

## Replay compatibility and provenance

The installed engine is Base75689 / data hash
`B89B5D6FA7CBF6452E721311BFBC6CB2`. An anonymous DI-star 4.10.0 sample successfully
stepped to its terminal result: 15,424 observations, 559 gameplay commands,
46 abilities. The raw API reports a command issued at loop t in the observation
packet at t+1; training uses the state at t-1. The API also exposes command-manager
repeat events, so its count must not be mistaken for the count of human SCmdEvent
records. Recorded commands all referenced the observed player's own units.

Compatible human sources acquired (about 238 KB total):

- [51574: Mez vs Vanya](https://lotv.spawningtool.com/51574/), Terran player 2,
  4570 MMR, TvP. The site's professional tag refers to Vanya, the Protoss opponent.
- [51573: Mez vs Sura](https://lotv.spawningtool.com/51573/), Terran player 2,
  4549 MMR, TvZ.
- [50925: Lyra vs anogashy](https://lotv.spawningtool.com/50925/), Terran player 2,
  4623 MMR, TvT.

These are Masters-level human feasibility examples, **not verified professional
Terran demonstrations**. Source URLs and SHA-256 receipts accompany the originals
in `logs/roadmap/human-replays/`. Extracted datasets are `human-51574/`,
`human-51573/`, `human-50925/`.

Named GuMiho and Bunny professional source replays were also acquired, but require
Base75025 / 4.9.3. A bounded HTTP range fetched the official old executable
(~21 MB) and small config files, leaving the original installation untouched.
The isolated runtime fails CASC asset initialization. Do not claim that binary
acquisition repaired playback, and do not download the entire 3.6 GB archive.
A bounded 52 MiB archive prefix recovered and checksum-verified the old encoding
and root manifests. An isolated overlay retained original assets through symlinks
and merged the supplemental local index entries. Native startup still failed.
An offline CascLib diagnostic decoded 701,765 root paths and verified six core
files, but also identified a missing old Liberty GameData asset. Its responsibility
for the native failure is unproved. Stop further asset acquisition without a traced
required-file failure; a missing exact replay map dependency also remains. Compatible stronger
human replay work can proceed independently. Assets/diagnostics are under
`logs/roadmap/runtime-4.9.3/` and `logs/roadmap/pro-replays/`.

An early Spawning Tool screen appeared to ignore ISO dates. The later
`pro-date-filter-audit-02.json` gets identical filtered links with M/D/YY,
MM/DD/YYYY and ISO dates when using the same Terran/pro filters, so the earlier
claim that ISO dates are unsupported is not established. Use binary metadata
and actual Terran identity for acceptance regardless of site date/tag results.

## Commands

```bash
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m src.learning.interface_probe --help
.venv/bin/python -m src.learning.replay_extract logs/roadmap/human-replays/51573.SC2Replay --player 2 --output logs/roadmap/example-new --wall-seconds 300 --source https://lotv.spawningtool.com/51573/
.venv/bin/python -m src.learning.sandbox --map DefeatRoaches --output logs/roadmap/baseline-new --seconds 60
.venv/bin/python -m src.learning.micro_train --output logs/roadmap/search-new --generations 4 --population 12 --workers 2 --seconds 60
.venv/bin/python -m src.learning.sandbox --policy logs/roadmap/micro-search-01/best.json --output logs/roadmap/eval-new --seed 9000 --seconds 60
```

Native execution needs local sockets and can require sandbox escalation. Use the
existing bounded process-group supervisor. CPU-only training; latest limit is
approximately 80% total machine load. A sample during two-worker search measured
11% on 32 logical CPUs; that is a sample, not a permanent limit. Do not restart
GPU work. Keep native replays; do not show victory demonstrations before the
user's goal is complete.

Latest production unit verification: 187 tests passed in 9.674 seconds, saved in
`logs/roadmap/unittest-twentyeighth.log`. Five new tests cover opt-in worker
construction cues and legacy feature compatibility. Native search/extraction results must be
inspected after completion before recording gains or moving gates forward.

## First terminal learning results

All three Masters replays reconstructed to terminal results with schema-2 timing
labels: 51574 has 1,151 command-burst rows / 1,168 raw gameplay commands;
51573 has 601 / 601; 50925 has 590 / 600. Their observed controlled-unit tags
passed the own-unit audit in the checked TvZ dataset. Professional Terran identity
is still not verified for these sources.

The 48-episode micro search completed in 184.38 seconds. On eight fresh matched
seeds, the learned controller's mean killed value was 1,587.5 versus 387.5 for
nearest-target attack. Mean damage dealt was 2,401.14 versus 796.30. Five learned
runs reached the 60-second cutoff; all baseline runs lost earlier. Cutoffs are
**not victories**. Mean damage taken also increased (1,014.88 versus 526.62) as
more enemy waves were encountered. Evidence: `micro-heldout-01/panel.json`.

The ordinary-game transfer development probe held the old macro checkpoint
SHA-256 `0f3e05d9efd5eba4fd238a6282e462599ffc675f008b98fd42925e99f6bb16c6`
fixed, comparing scripted combat against learned control of Marines within 15
tiles of a visible enemy. Seeds 99000–99002, Simple64, Hard, all three races:
scripted combat won 1/3; learned combat won 0/3. All learned micro commands were
accepted by the engine. This is a failed transfer gate, not a successful full-game
policy. Retain the checkpoint and replay evidence; do not promote it. The Marine
policy was trained only against roaches, its target-distance coefficient prefers
farther targets, and transfer changes decision cadence from four to eight loops.
These are concrete hypotheses to inspect in replay traces before another batch.
The probe code is `src/learning/transfer.py`; receipts are `micro-transfer-01/`.

## Imitation failures and label corrections

The first per-unit imitation model (imitation-03) and shared-command models
(imitation-global-01/02) failed live VeryEasy games without producing an army.
The latter issued Smart 1,414 times out of 1,417 commands. Offline prediction
accuracy is not live-game competence. No checkpoint is promoted.

Auditing original binary replay SCmdEvent records identified engine repeats:
51573 contains 195 issued events versus 601 reconstructed commands. The separate
issued-51573 dataset uniquely matches 194 events; one addon target was normalized
by the engine and conservatively excluded. The original reconstruction is retained.
51574 matches 495/505; 50925 matches 342/347. Unmatched/ambiguous events are preserved
in receipt audits, never converted to waits. Delay labels are recomputed between
retained issued commands. Controlled actors are resolved from earlier own-unit
observations, including temporarily absent gas-mining workers; no tracker or future
state enters the actor.

Models choose an engine ability first, then condition unit type/group, target,
queue and timing on that ability. All engine ability IDs remain representable.
The live adapter masks actual available abilities and uses current target tags.
Training-only normalization and class priors are saved with the model. Current
network inputs include unit composition, nearest visible enemy, economy, history
and entity attributes; full map grids and recurrent/attention encoders remain open.

The issued-command model reached the 600-second VeryEasy cutoff but still built
no army. Base-relative mirrored coordinates (imitation-canonical-02) also reached
the cutoff without an army. Neither cutoff is a victory. Canonical-01 is an invalid
intermediate fit with mismatched target coordinates; do not execute or promote it.
The next bounded experiment balances rare commands using inverse square-root
training frequency, so common movement commands cannot dominate every teaching
update. This changes teaching weights, not gameplay legality or a scripted build
order.

The balanced model (imitation-balanced-01) built one depot, two barracks and an
Orbital Command in a 600-second VeryEasy probe. Production/construction choices
were learned. It produced no army and lost all workers; the run hit the cutoff,
not Victory. This is material macro execution progress, still below gate C.
An explicitly attributed execution-assistance probe assigns each newly produced
idle SCV to visible minerals once, never overriding a current model command or
ongoing order. It does not choose worker production or buildings. Its counts and
flag are separate in episode receipts.

The newborn-only worker assistance issued zero commands: new SCVs already had
orders, and later idle workers were often previously moved by the model. Those
probes (imitation-balanced-harvest-01/02) are retained as unsuccessful diagnostics.
The current optional --idle-worker-harvest primitive handles idle workers, excluding
workers with ongoing orders or selected by the model this frame. It is explicitly
attributed and does not alter production/construction choices.

## Observation and placement development

Three further Masters Mez sources (51958 TvZ, 51890 TvP, 51891 TvP; ~283 KiB)
were reconstructed to terminal results. All match Base75689. They are not pro
Terran examples. Their issued datasets uniquely match 279/281, 500/507 and
531/544 human commands, respectively, with unresolved events preserved. The
current fit uses 1,999 issued commands from five whole Mez games; Lyra's 342
commands remain a separate held-out player/game. Imputation never uses tracker
or future enemy state.

The global model now additionally encodes per-type own/enemy positions, health,
energy, cooldowns, construction progress, queue length/progress, idle fraction
and own order-ability counts. Coordinates face toward map center from the own
base. Older saved models retain their original input dimensions through explicit
checkpoint metadata. Individual learned pointers, recurrent memory and map-grid
encoding remain open. Spatial coordinate loss was weak compared with categorical
loss: Huber loss with bounded gradients improves training target error from about
25 to 13 tiles in the two-game development fit, but held-out error is still large.
Offline improvement does not establish live competence.

Native failures identified actual construction geometry rejection: action code 41
is CantFindPlacementLocation. The placement primitive now queries the engine
on nearby half-tile positions and currently visible gas positions, choosing the
closest legal point to the modeled request. It preserves ability, unit group and
queue; records requested/issued coordinates and rejections; never chooses a build
order or expansion strategy. A spatial model built four Command Centers and
reached a 600-second cutoff without an army. This improves physical execution,
not macro competence. Rejected intent is retained rather than fabricated as wait.

Command sampling uses the model's probabilities restricted only by actual engine
availability and a reproducible seed. The sampled probe still failed to build a
useful army and lifted its Command Center; it is exploration evidence, not RL
training. Worker assistance and learned command totals are separately attributed.
Astra reviewed the stalled imitation pipeline read-only, as authorized by the
user when progress stalls. Do not start a large RL campaign from these checkpoints
or claim gate C passed.

## Opening curriculum and selected-unit conditioning

The review found two concrete failures. Live model history included scripted
harvesting while teaching history contained human decisions only. The live input
now uses model-issued history; full assistance remains visible in unit orders and
is traced separately. Coarse mean-position/dominant-type selection could not
reproduce 5/153 opening actor groups even with perfect labels. A binary learned
membership selector replaces that shortcut without limiting group composition.
Ground-truth individual membership round-trips all 153 groups; this is codec
evidence, not learned strength or an engine legality test.

The five whole-game training sources supply all 153 commands issued in their
first 120 seconds, with equal total teaching weight per replay. No ability classes
are removed. `imitation-prefix-01` fits command identity at 98%, gets the first
TrainSCV command right in all five games, and recalls all production commands.
The frozen-context actor model `actor-prefix-01` exactly selects 142/153 groups
(92.8%). Lyra remains held out. These are training fit checks, not generalization.

Three 120-second live probes with that model built workers and supply but no army.
Tracing revealed a Command Center selected with worker scouting arguments. The
new `arguments-prefix-01` learns target, mode, queue and timing from the selected
group and frozen macro context. It cannot overwrite the macro ability. Training
target error is 1.77 tiles, mode accuracy 98.7%, target type 87.5%, timing 75.8%.
Two 180-second probes on seeds 40010/40011 built a Barracks and Refinery and
produced one army supply each; Terran also upgraded to an Orbital Command. Both
are cutoffs against VeryEasy, not wins. Receipts:
`prefix-arguments-zerg-01/`, `prefix-arguments-terran-01/`.

Current bounded experiment: compare the old argument head on the same Zerg seed
and 180-second horizon, then fit the five complete opening prefixes through 240
seconds (600 epochs CPU-only; held-out Lyra unchanged). Hypothesis: actual-group
conditioning removes rally/scout confusion, and the longer prefix provides the
production/gas/expansion examples needed after the initial opening. Inspect first
command, production recall, argument errors and exact actor groups before any
new native batch. Limit live follow-up to three 300-second openings; stop and
inspect if no army develops. This is preparation for imitation competence, not
a full-game RL campaign or a passed gate C.

The 240-second fit reached 99.4% training command accuracy, 100% production
recall and 480/494 exact actor groups. Selected-group argument training error is
0.87 tiles. Held-out Lyra command accuracy is 44.4%, so generalization remains
weak. Five-minute native development probes: Zerg produced one army supply but
six CC/Orbital structures; Terran produced no army and five CCs. These are failures
of useful macro, not successful imitation games.

The Terran trace first wanted a depot at 85 minerals. Masking substituted Stop;
later blocked SCV production became repeated depot orders that interrupted
construction. An optional `--wait-unavailable` execution variant reevaluates the
same learned intent each step instead of substituting an unrelated command.
It does not choose prerequisites or a build order. The frozen matched run issued
34 commands, all accepted, and built one CC, one Orbital, Barracks, Refinery and
two depots, but only one army supply. It subsequently requested CC locations
beyond the map edge and stalled on 202 CC decisions. Artifact:
`prefix240-wait-terran-01/`. This closes the hypothesis that availability fallback
alone is sufficient for useful macro.

Astra's second trace review identified spatial deadlock. Clamping constant input
features changed only 2/416 macro decisions and left CC targets beyond the map;
live mineral types were already represented in training. Do not spend another
batch treating unused random features as the primary cause.

Next bounded mechanism test: `spatial-prefix-240-01` scores uniform four-tile
candidate positions aligned to native footprint size. Inputs use local terrain,
placement/pathing grids, currently visible resources and units, builder distance
and frozen command context. There is no scripted expansion list. Human build
locations provide nearby-cell positive labels; the engine filters actual legality
at execution. Macro command, unit selection and nonconstruction arguments stay
frozen. On the same eight held-out Lyra construction commands, target error is
16.15 tiles versus 36.42 for coordinate regression (training 42 commands: 2.50
tiles, grid coverage error 1.61). These conditional geometry checks use the human
ability/group, not closed-loop predictions. Two matched 300-second openings on
seeds 40020/40021 will measure repeated placement rejection and completed army
production. If legal locations merely enable excess CCs without an army, close
this rescue hypothesis; do not extend it into a large RL run.

Both spatial probes developed more production: Terran ended at five army supply,
23 workers, Factory/Starport, two CCs plus one Orbital; Zerg ended at six army
supply, 28 workers, Factory/Starport, four CCs plus one Orbital. Against the matched
waiting-only Terran run, army supply rose from one to five. Both still reached
the 300-second cutoff, and expansion is excessive. The spatial mechanism improved
live production, but does not establish useful full-game strength. Artifacts:
`prefix240-spatial-terran-01/`, `prefix240-spatial-zerg-01/`.

Next competence check: two frozen-policy 1,200-second VeryEasy games on fresh
Zerg/Terran seeds, at most 240 wall seconds each. Record terminal results, army
and build progress, idle/repeated decisions and resource utilization. Do not count
cutoffs as complete games or victories. Stop after this pair before proposing RL
or longer imitation fits. The live adapter also avoids a redundant macro forward
pass when the engine-legal ability is already the model's raw argmax; argument
conditioning is identical.

The longer frozen checks both ended in native Defeat: Terran at 973.9 game seconds
(11 surviving army supply, 43 workers, almost all structures destroyed); Zerg at
1,192.9 seconds (no workers or army). They took 77.96 and 104.24 wall seconds,
respectively. These terminal games show production and actual fighting, but fail
useful full-game competence. Neither is a promoted model or a passed Hard gate.
Native replays and traces remain in `imitation-long-terran-01/` and
`imitation-long-zerg-01/`.

Next bounded fit: use all five human replay prefixes through 600 seconds, with
the same held-out Lyra game and equal replay weight, for 800 CPU-only epochs.
The four-minute teaching cutoff omitted later production/defense examples, so
this tests whether later recorded decisions improve sustained production. Inspect
first commands, production recall and prediction fit before any actor/argument
fit or live follow-up. This is one curriculum extension, not an RL batch.

The dense engine-wide input is mostly zeros (58,710 macro features). Input products
and gradients now operate on every currently nonzero column; no unit, ability or
observation feature is removed, including novel live entities. Adam also retains
decay for dormant rows with saved optimizer moments. Dense-reference parity and
checkpoint/gradient tests verify this optimization. Report kernel and entire-game
timings separately; kernel speed is not simulation speed.

The input-kernel benchmark measured 2.23x speedup on a 64-frame teaching batch,
with 456 active columns out of 58,710; maximum floating-point difference was
9.54e-6. It is recorded in `sparse-kernel-benchmark.json`, not claimed as full-game
speedup. The 600-second fit completed in 162.49 seconds: 1,524 commands, 99.15%
training ability accuracy, correct first TrainSCV in all five games and production
recall 98.7–100%. Lyra held-out ability accuracy is only 18.1% and target error
67.8 tiles. This is strong fit to one player's demonstrations and poor independent
generalization, not a passed imitation gate.

Bounded continuation of that curriculum experiment: fit actor membership (350
epochs), selected-group arguments (800 epochs), and spatial candidates (150
epochs) against the same saved macro and data window. No additional replay
acquisition or native games are included in that fitting budget. Check conditional
fit and held-out placement before at most two fresh 1,200-second live games;
stop to inspect if sustained army production remains absent. Do not infer strength
from supervised command accuracy.

## Semantic perception experiment

The ten-minute curriculum's follow-up models finished: actor membership matched
1,312/1,524 training groups, selected-group target error was 1.07 tiles, and
construction placement errors averaged 2.73 training / 11.24 held-out tiles.
Fresh Very Easy games still failed: Terran seed 40041 ended in Defeat at 773.75
seconds with no workers or army and no damage/kills; Zerg seed 40040 reached the
1,200-second cutoff with no workers or army, 511.85 damage and 175 killed value.
The surviving Zerg buildings were flying. These results reject promotion and
further blind curriculum enlargement. Evidence is retained under
`imitation600-long-terran-01/` and `imitation600-long-zerg-01/`.

A concrete information gap was found in the macro encoder: history retained only
two ability IDs, making worker Smart orders indistinguishable from townhall Smart
rallies. Completed upgrades and per-building assigned/ideal harvesters were also
absent. The opt-in `--semantic-history` encoder now keeps four prior commands'
actor types, target type/alliance/position, queue, group size and age, plus
harvester assignments and completed upgrades. Roles are recorded using only
information known when each command was issued, and survive subsequent unit
death or transformation. Unknown targets remain unknown. Previous checkpoint
shapes and default encoders remain supported. Actor, argument, spatial and live
encoders read the same macro checkpoint flags. This is still a small feedforward
model, not recurrent memory or a completed perception milestone.

The matched four-minute fit `imitation-semantic-240-01/` took 66.99 CPU-only
seconds: 494 commands, 99.8% training ability accuracy, all five first commands
TrainSCV, 100% training production recall. Held-out ability accuracy is 32.3%
(previous four-minute fit 44.4%); target error is 48.65 tiles (previous 53.3).
Actor membership fits 478/494 groups; selected-group target error is 0.53 tiles;
spatial training / held-out errors are 2.64 / 11.30 tiles. These are conditional
teaching metrics, not live strength. The five training games contain TvP/TvZ;
held-out Lyra is TvT, so this split confounds player and matchup generalization.

Only one of the 494 opening commands belongs to a mixed-ability burst. Thus burst
flattening deserves repair but cannot explain most failures in this opening
curriculum. Burst sequencing and quiet/no-op example coverage remain open.

Queue identity is now checked during issued-command reconciliation using the
native fixture's verified SCmdEvent flag bit 2. Re-auditing all six human games
preserved the previously reported match counts; mismatched queue settings are
rejected. Full ability-link identity auditing remains open.

The fourteen full-suite run passed 149 tests in 9.64 seconds, including sparse
training-column parity and the initial semantic-input checks. Two additional
focused tests verify past roles surviving death and unknown targets remaining
unknown; the next full-suite run must include them. Ruff and `git diff --check`
passed before the native follow-up.

The semantic model's matched native openings did not improve production:
Terran seed 40021 ended at the 300-second cutoff with 2 army supply / 28 workers;
Zerg seed 40020 with 2 / 22. Both are Tie truncations, not victories. Terran lifted
its Barracks at 173.2 seconds and never landed it, then repeatedly requested
Reapers. Zerg requested Reapers hundreds of times with zero gas. The unavailable
intent guard prevents substitutions but can preserve an impossible intention
indefinitely. No full-game extension or promotion is authorized by these results.

The broader engineering fixture `interface-extended-fourth/` passed all 20
physical checks and all 20 command results: the original nine plus research,
repair, depot lowering/raising, transport loading/unloading, add-on construction
and cancellation, scan, and Barracks lift/land. The first three attempts exposed
fixture setup problems (debug damage takes effect on the next frame, spawned
structures alter placement, and a loaded passenger cannot participate in a
movement assertion). Those attempts remain preserved; the fourth passed in
7.44 wall seconds. This extends representative family evidence, not proof of
all abilities or learned use of those commands.

## Quiet-state temporal experiment (bounded)

Astra's read-only review identified action-event-only teaching as the next
specific hypothesis: the model is asked which command occurred *given that a
command occurred*. It lacks actual intervening production/resource-accumulation
states, and predicted delay does not supply these observations.

Six four-minute prefixes were natively reconstructed again with fog enabled,
storing 1,345 observations at four-loop stride per replay (`dense240-ID/`).
`occupancy240-ID/` preserves each original matched event's exact pre-command
state and adds genuine quiet samples. A quiet sample within four loops of any
matched or unresolved issued event is excluded; unsupported commands are never
relabelled WAIT. This is a hybrid of exact event samples and regularly spaced
quiet samples, not exact uniform occupancy or silently rounded command timing.
The rare multi-command event retains its ordered commands; autoregressive burst
execution is still open. Five training prefixes retain 494 commands plus 5,659
quiet samples; held-out Lyra retains 99 commands plus 1,124 quiet samples.

One CPU-only budget is running: 600 epochs, inverse-square-root ability weights,
equal total replay weight, semantic inputs, 900-second wall deadline,
`imitation-occupancy-240-01/`. Temporary projected training matrices preserve the
full saved engine vocabulary and live input; dense/projected update parity has
been checked. Native follow-up, if justified, uses fixed four-loop reevaluation
rather than the predicted delay, with unchanged availability/placement checks
and explicit idle-worker harvesting assistance. Actor/argument/spatial components
must be refitted to this exact macro checksum; old models cannot be rebound.

Before native follow-up require training production-event recall >=95%, held-out
commanded ability accuracy >=32.3% (the matched semantic event model), quiet
accuracy >=80%, and balanced event/quiet accuracy >0.5 (always-WAIT baseline).
Compare a teacher-forced previous-model delay scheduler as an offline diagnostic,
reporting its assumed command acceptance separately from native legality.
At most two matched 300-second games are planned. Close the arm if it increases
waiting without reducing impossible-intent streaks and improving completed army
production over the matched 5/6-army spatial baseline. Quiet human frames may
still fail to teach recovery from learner-created errors; do not respond to a
failure by blindly enlarging passive replay fits. Expert corrections on actual
learner states or a deliberately identified RL bridge would then be required.

The latest completed full suite passed 151 tests in 9.74 seconds. New quiet-frame,
always-WAIT metric, and mixed-schema death-memory checks are added and require
a fresh full-suite result before checkpointing these changes.

The sixteenth full suite passed all 156 tests in 10.06 seconds; Ruff and diff whitespace checks passed. The quiet-state fitting experiment remains running and has no promotion evidence yet.

The quiet-state arm is closed before native follow-up. The 600-epoch fit took
284.07 seconds with 800 projected training columns / 97,914 full features.
Training event accuracy was 99.4%, quiet accuracy 95.9%, and production recall
100%; held-out event accuracy was only 19.2%, quiet accuracy 54.9%, balanced
score 0.370. The previous teacher-forced delay scheduler's balanced score was
0.482 (6.1% event / 90.3% quiet; it assumes all intended commands succeed).
The new fit fails all predeclared held-out thresholds. No actor/argument/spatial
fits or native games are warranted from this checkpoint. Preserve report,
checkpoint and `occupancy-240-01-gate.json`; do not extend this arm blindly.
Implementation checkpoint: `645b916`; 156 tests and the extended native fixture
passed. The next direction must address recovery on learner-visited states or
RL experimentation, with any supplemental teacher's provenance explicit.

## Broad-ability RL bridge

After quiet-frame generalization failed, Astra reviewed two alternatives and
recommended a raw-action RL bridge. Grafting the old 27-action expert into another
controller would require translating its own stance, masks and executor. The
new experiment directly samples the learner's own state distribution.

`src/learning/broad_rl.py` adds a zero-initialized 32-feature ability-logit residual
and independent value head, preserving every engine ability and WAIT. The frozen
human macro's WAIT context supplies its features. Original macro/actor/argument/
spatial checkpoints stay byte-identical; argument contexts still come exclusively
from the original macro. Native availability is the only ability mask. Target
modes still follow the engine catalog, but untrained or poor arguments can fail
and remain an explicit limitation.

Sampling uses `(1-epsilon)*masked_policy + epsilon*uniform_legal`, epsilon 0.1.
PPO records and differentiates the actual mixture likelihood, including its
responsibility factor; finite-difference gradient tests cover actor, value and
entropy. Greedy evaluations record actual deterministic probability one and
cannot be fed to the training updater. Rejected/undecodable choices remain in
trajectories. Frozen likelihood and value replay are checked before updates.
Discount and GAE depend on actual elapsed loops, measured in five-second units.
The reward is deliberately unchanged across this arm: incremental killed-resource
value /100, +100 native Victory, -100 native Defeat, zero finite-horizon timeout.
There is no new economic/damage shaping. A timeout is a truncated native game and
a finite-horizon training endpoint; it is never labelled a victory.

The first native one-minute smoke failed only at terminal response unwrapping;
its artifact remains. A focused regression test now checks the actual nested API
response. The repaired smoke retained all 336 decisions, including failures,
and queried the final native score/clock. The full pipeline smoke
`broad-rl-pipeline-smoke-01/` completed three one-minute training games, 1,008
samples, 32 optimizer updates, and six fresh paired controls (12 evaluation
games) in 52.51 seconds. All were cutoff Ties with zero combat return. This is
collection/update/evaluation engineering evidence, not reward-driven learning or
strength. It deliberately used a horizon too short to assess combat competence.

Next fixed protocol: 24 x 600-second Very Easy training episodes, eight per race,
three CPU-only workers (maximum four), then six fresh paired cases (two per race)
comparing greedy trained and zero-residual controllers under identical fixed
four-loop cadence, native masking and explicit idle-worker harvesting assistance.
Use the four-minute spatial checkpoint family, which previously produced 5/6 army
supply in matched openings. The control matters because removing predicted sleep
and replacing unavailable-intent waits already changes behavior. Require more
native wins and greater mean ordinary combat return than zero-residual control;
no automatic extension. Increased production or kills alone is mechanism evidence.
Close ability-only learning if reward-bearing exploration chiefly fails during
unit/argument execution. Any continuation must identify that actual bottleneck.
Professional imitation and reliable all-race Hard gates remain open.

Independent read-only PPO review found no Critical or Important issues. Its one
minor cadence-provenance finding was repaired: residual execution now always
uses fixed cadence, including direct CLI runs. The full suite passed 165 tests
in 9.729 seconds (`unittest-eighteenth.log`); Ruff and whitespace checks passed.

### Fixed-cadence bridge: closed without promotion

Commit `66de683`, `broad-rl-24-01/`: completed 24 training games, 2,396 optimizer
updates and all six fresh paired evaluations (12 games), in 687.62 seconds.
Both evaluated controllers won 0/6. Mean native-outcome difference was zero;
mean combat-return difference was +1.375, equivalent to 137.5 extra killed-resource
value per game because terminal outcomes balanced. The declared wins-and-return
gate failed. This is a reward-driven production/combat mechanism improvement,
not Very Easy competence or Hard acceptance. Preserve the trained checkpoint;
do not automatically extend this training batch.

The training traces contain 75,635 model commands, 9,196 queue-full results and
1,384 possible construction interruptions (movement/stop/hold/attack issued to
workers with build orders; these are candidate interruptions, not a verified
count of cancelled buildings). All training games ended with zero army supply.
Greedy trained evaluations did produce army, including final 6/12 supply in the
first Terran/Protoss pairs, versus zero for those frozen controls. See the report,
native episode receipts and execution audit; sampling and greedy behavior differ.

Astra identified a temporal mismatch in its earlier fixed-cadence recommendation:
the frozen argument model commonly predicts longer command intervals, while the
bridge overrides them with four loops. Before tempering logits, learning queue
heads or adding rewards, isolate that mismatch. Next screening: six fresh paired
sampled cases (seeds 41600–41605, two per opponent race), 600-second Very Easy games,
same zero residual and four frozen checkpoints, epsilon 0.1 and identical worker
assistance. Compare fixed four-loop decisions with the learned predicted delay
after **native-accepted** commands. WAIT, undecodable, placement-rejected and
engine-rejected attempts retry next control step. No PPO updates occur.

Require more completed army units in at least four of six pairs and no worse mean
ordinary combat return. Report queue-full results per model command and potential
construction interruptions. Reduced command count alone does not pass. Only a
passed screening justifies declaring a separate duration-aware RL arm. Full-game
micro and higher reaction rates will still need separate control; slowing a bad
macro sequence does not fulfill the unlimited-attention objective.

The accepted-command cadence regression passed, then the full suite passed 166
tests in 9.727 seconds (`unittest-nineteenth.log`). Ruff and whitespace checks
passed. An independent read-only review found no issues in the timing patch,
including WAIT, failed placement/native rejection, callback scope and separating
harvest-assistance results. Screening source and contracts are retained under
`logs/roadmap/cadence-screen-01.py` and `cadence-screen-01/`.

Four additional small professional-tagged source candidates were acquired and
metadata checked: [Cure 52120](https://lotv.spawningtool.com/52120/),
[52121](https://lotv.spawningtool.com/52121/),
[52122](https://lotv.spawningtool.com/52122/), and
[demuLarva/Lambo 52146](https://lotv.spawningtool.com/52146/). All require unavailable
Base75800 / 4.10.1, data hash `DDFFF9EC4A171459A4F371C6CC189554`.
They have source/hash receipts and `pro-4.10.1-preflight.json`, but no reconstructed
observations and are excluded from training. The
[SC2EGSet paper](https://www.nature.com/articles/s41597-023-02510-7) describes parsed
game/tracker events rather than our causal fog-safe player observations. It does
not presently replace the matching-engine extraction step; no bulk dataset was
downloaded.

### Command-duration screening: passed execution gate

Commit `44f9386`, `cadence-screen-01/`: all twelve native games and trace audits
completed in 198.34 seconds. Learned accepted-command durations increased
completed army units in 5/6 pairs (deltas 10, 0, 10, 1, 14, 24), versus zero
completed army in every fixed-cadence arm. Queue-full errors per command fell
from 6.4–25.4% to zero in all six learned-duration arms. Mean combat-return
difference was +23.4583; this includes one avoided Defeat and additional kills.
No native wins occurred. Potential construction-interruption counts remain
diagnostic rather than confirmed cancelled-building counts. The predeclared
army-production/return gate passed; no professional or Hard acceptance follows.

Next declared RL arm: `broad-duration-24-01/`, 24 x 600-second Very Easy games,
three workers, seeds 41700–41723, same frozen four-minute model family, fresh
zero residual, unchanged epsilon/reward/PPO/GAE. Accepted commands use predicted
durations; failed/WAIT attempts retry after four loops. Evaluate six fresh paired
greedy cases at seeds 42700–42705 against zero residual under the **same learned
duration** control. Require more native wins AND better mean combat return;
no automatic extension. Duration-aware rollout elapsed times are handled by
the existing tested elapsed-loop returns.

In parallel, the installed `DefeatZerglingsAndBanelings` sandbox was checked with
the existing nearest-target baseline: native Defeat, 125 killed value, 214.53
damage dealt, terminal 405 damage taken, 7.5 game seconds. This exposed a small
reward-accounting omission: the old micro receipt used its final callback frame,
before the last five damage points and terminal clock. A regression reproduced
missing terminal kills; micro now queries the final nested native observation.
`banelings-baseline-02/` confirms the corrected terminal score/clock. Old micro
evidence retains its historical scoring convention; use fresh paired controls.

Next second-scenario micro arm: four generations x twelve candidates, one worker,
60-second horizon, training seed 42110, existing 12-parameter movement/visible-
targeting policy search and unchanged reward formula. After the fixed 48 games,
compare eight fresh paired seeds 42200–42207 to nearest-target control using
corrected terminal scores. Require mean killed value at least 1.5x baseline,
no greater mean damage taken and more native wins; survival alone cannot pass.
This remains a primitive experiment and does not establish ordinary-game transfer.

The complete suite passed 167 tests in 9.770 seconds (`unittest-twentieth.log`),
including both terminal-response adapters. Ruff passed. `broad_train` exposes
`--learned-cadence`; its original fixed-cadence default remains unchanged.

Micro criterion correction **before any held-out evaluation**: inspection of the
installed map's `MapScript.galaxy` showed repeated six-Zergling/four-Baneling waves.
Each cleared wave preserves surviving Marine health, relocates the group and adds
four Marines. Its official score adds five per enemy death and subtracts one per
own death. The 120-second timer pauses the mission; clearing a wave spawns another.
Consequently the proposed native-win criterion was incorrect for this sandbox,
and absolute damage taken confounds additional reinforcements with worse combat.
That original micro gate is invalid, not passed. No training reward/model choice
changes. `banelings-map-mechanics.json` binds this inspection to map/script hashes.

The corrected primitive check, declared before seeds 42200–42207 run, requires
strictly greater mean killed-resource value, at least 1.5x the fresh paired
nearest-target baseline, and no worse aggregate damage-taken/killed-value ratio.
Report official score, outcomes and survival separately; zero-kill fleeing cannot
pass. This is a scored-wave primitive check, not a relaxed full-game win gate.
Professional extraction, full-game micro transfer and Hard acceptance remain open.

### Terminal results and return to human imitation

`broad-duration-24-01/report.json` closes the declared duration-aware arm:
24 training games and twelve paired evaluation games completed in 586.48 wall
seconds, with 320 optimizer updates. Both evaluation arms won zero of six games.
Mean combat return improved by 4.125, but the required native-win gate failed.
No promotion or automatic extension follows. Trace inspection found many Marine
Attack commands targeting neutral minerals or friendly units, and many point
targets clamped to map boundaries. Ability-only reinforcement learning leaves
the frozen target and unit-selection models unable to correct these decisions.

`banelings-heldout-01/report.json` closes sixteen fresh sandbox games. The learned
primitive doubled mean killed-resource value (159.375 to 318.75), reduced the
aggregate damage/killed-value ratio from 2.6824 to 1.5529, and increased mean
official score from 26.875 to 39.75. The corrected scored-wave primitive gate
passed. Every game in both arms ended in native Defeat. Ordinary-game transfer,
professional imitation and Hard acceptance remain unproved.

The user clarified that human imitation must precede further full-game RL.
Hold further RL and micro-transfer experiments until imitation is demonstrably
competent. The roadmap remains active; this changes sequencing, not acceptance.

`human-argument-audit-01.json` checks the retained four-minute argument model on
the entirely held-out Lyra game, supplying the actual human ability and selected
unit group. Mean target error is 39.84 tiles over the first four minutes and
92.64 over the complete held game; mode accuracy falls from 74.7% to 57.0%.
This isolates a substantial argument-generalization failure independently of
macro and actor errors. Training/live coordinate conventions agree on inspection;
no conversion bug is established. The five four-minute teaching prefixes contain
65 Attack commands, only five aimed at enemy units. Complete teaching games
contain 380 Attack commands, including forty aimed at enemies.

`arguments-full-human-01/` is a supervised-only experiment using all 1,999 issued
commands from the same five teaching games, the same frozen macro context and
600 epochs. It excludes the Lyra game throughout fitting. Complete held-game
target error improves to 35.66 tiles (61.5% lower), mode accuracy to 70.2%, and
target-alliance accuracy to 88.2%. Opening target error improves to 26.94 tiles.
Training target error is 4.35 tiles. This is evidence that full demonstrations
help, but the large train/held gap and low held target-type accuracy (27.5%)
still fail competent imitation. Do not promote it to live gameplay on the
strength of training accuracy. Expand compatible human coverage across players,
maps and matchups, and evaluate target identity/geometry on held games before
another native training campaign. Professional replay extraction remains open.

Further bounded source screening retained six small originals and SHA receipts:
51753 (Mez Terran vs BattleB Protoss) requires Base75025; 52108 is ZvZ on
Base75800; 51996 contains PANDA Terran at 5800 MMR on Base75800; 52090 contains
Uzikoti Terran at 6040 MMR on Base75800; 55330 contains JimRising Terran at
4940 MMR on Base75800. The one compatible candidate, 53513, contains ROOT Terran
at 2611 MMR versus Very Easy AI. None adds verified compatible professional
Terran teaching. No candidate was silently admitted to the strong-teacher corpus.
Source filter pages are retained in `pro-terran-window-01.json` and
`human-terran-window-02.json`; replay metadata, rather than the site's broad patch
filter or professional tag, determines actual build and observed player's race.
The remaining supervision work includes learning current-target identity directly
from entities, rather than relying solely on separate type/alliance logits plus
an extrapolated point. Evaluate that change on held human games before live use.

### Supervised target-identity comparison

`src/learning/target_selection.py` encodes every currently observed candidate's
type, alliance, actor-relative geometry, health/resources and prior target orders,
along with explicit chosen ability and selected-group composition. Friendly,
neutral and enemy choices remain available; there are no combat target recipes.
The model scores candidate identities directly. It excludes hidden and remembered
targets, uses prior command history only, and does not use unit tags as features.
It is not wired into live gameplay pending competent held-game results.

`target-human-fit-01/` completed a fixed 150-epoch CPU-only supervised fit in
13.08 seconds. Five full Mez games teach 289 unit-target commands; the held-out
Lyra game supplies 51. The actual human ability, actors and unit-target mode are
supplied to both models to isolate target grounding. Relative to the frozen
full-human argument decoder, exact held target matches increase from 5/51 to
12/51 (9.8% to 23.5%) and distance error falls from 15.61 to 10.79 tiles. No held
targets were excluded. The comparative gate passes, but 23.5% accuracy is far
below competent imitation. The held game includes no unit-target Attack commands,
so this comparison alone cannot establish combat targeting. Nearest-group-center
selection scores 0/51; it is a simple diagnostic, not a strong teacher baseline.

An independent read-only review found no blocking leakage, split, weighting or
comparison issues and explicitly rejected treating this as live/RL readiness.
The full suite passed 169 tests in 9.750 seconds (`unittest-twentyfirst.log`),
including visibility exclusions, explicit ability conditioning and invariance
to unit tags/candidate ordering; Ruff passed.

Next declared diagnostic: `target-human-crossval-01/` evaluates the unchanged
150-epoch target scorer across all six complete human games, each excluded from
its own fit. Report every fold, unavailable targets and enemy/Attack strata.
Each fold balances training replay weights and derives normalization from its
training games only. The older argument baseline is omitted because it was fitted
on five of these games. This wider audit addresses matchup and combat coverage;
it does not authorize live promotion or another RL campaign.

The six-fold audit completed in 57.12 wall seconds. Across 340 held unit-target
commands, exact identity accuracy was 29.1%, type accuracy 54.7%, and mean distance
error 10.27 tiles. Across 53 enemy-target commands the corresponding values were
13.2%, 26.4%, and 11.60 tiles. Most decisively, only 6/40 enemy-directed Attack
targets matched exactly (15%); correct type was chosen for 12/40, with 13.03-tile
mean error. One TvZ fold matched zero of seventeen attack targets. No held targets
were unavailable/excluded in any fold. These results contradict combat imitation
readiness despite the first comparative improvement. Keep the scorer experimental
and unwired; further RL remains on hold. Additional independent compatible human
players, richer target relations and fresh held games are required before promotion.

### Third human player and fresh target comparison

Bounded TvT source screening found replay 51960 (Huski, 4507 MMR, versus Mez,
4546 MMR) on exactly Base75689 / B89B5D6FA7CBF6452E721311BFBC6CB2. Candidates
51898 and 51896 require unavailable Base75800 and remain excluded. Huski is a
source-named human, not a verified professional. `human-51960-p1/` reconstructs
player one to terminal Defeat in 89.385 wall seconds, retaining all 10,711
consecutive fog-enabled engine observations for command alignment and 96 sampled
quiet states. No untranslated native gameplay commands were reported.

`issued-51960-p1/` aligns 305 commands with 312 human SCmdEvents, excludes 418
engine repeats, and explicitly records seven unresolved events. Those seven
events are not silently converted to teaching labels. This adds a seventh game
and third named human to the reconstruction corpus. Both sides of replay 51960
must stay together in every split; a second player view is not an independent
held game.

Before reconstruction finished, `huski-target-held-01-contract.json` froze the
existing target, full-human argument and macro checkpoint hashes for a fresh
comparison without fitting on 51960. `huski-target-held-01-with-strata.json`
reports 56 unit-target commands: direct selection matches 16/56 versus 3/56 for
the argument decoder, with distance error 8.50 versus 25.36 tiles. All targets
were currently available. Of seven enemy-directed unit Attack commands, direct
selection matches 4/7 versus 0/7, with distance error 4.07 versus 40.09 tiles.
The fresh comparative gate passes. The nearest-group-center diagnostic has zero
exact matches but slightly lower mean distance (7.20 overall and 3.99 for attacks),
so distance alone would exaggerate the learned benefit. Forty-seven point-directed
or unseen-target attacks are outside this unit-pointer comparison. The small
combat sample and failed six-fold results still preclude competent imitation,
live promotion, professional acceptance and further RL. All jobs are terminal.

### Native old-runtime failure traced and narrowed

`old-casc-probe/native-trace-01/` traces the existing isolated Base75025 process:
it aborts after opening the first modified CASC index, before opening any data
archive. A separate `runtime-4.9.3-indexpad-01/` clone pads short index copies to
196,608 bytes without changing their payloads or acquiring assets. Native tracing
now opens all sixteen selected index buckets and five archive files, then fails
at a different startup stage. The original installation's index SHA inventory is
unchanged; archive opens are read-only (`indexpad-native-progress-01.json`).
This resolves an index-layout obstruction, not native playback as a whole.

The new native failure identifies **GameData/AssetsProduct.txt**, content key
`1566ae22ab93ec0f9e246c9efbc7fec4`, as required and unavailable. This is a traced
required-file failure, unlike the earlier unproved Liberty manifest hypothesis.
The verified old encoding maps it to encoded key
`31271d461c33eda86a4723e3cbdd8038`, decoded size 264,581 bytes. Bounded archived
index members locate its 24,654-byte physical record in data.002 at offset
236,180,873. Loose CDN attempts and sampled group/archive index endpoints are
unavailable. The official ZIP's encrypted deflate stream requires decoding its
preceding bytes, so recovering this small record needs approximately 225 MiB of
archive-prefix input, not a 24 KB range request.

`required-assetsproduct-download-plan-01.json` records the exact official source,
member/header checks, stream offset, record size, expected content/encoded hashes
and a proposed 250 MiB maximum. That larger download has **not** been executed.
User authorization is pending because the user prohibited large unsolicited
downloads. If authorized, decode only the bounded prefix, verify encoded-header
and frame hashes plus full decoded MD5/size, and install only the verified record
into an isolated overlay. Then repeat native startup and trace any next failure.
Do not assume this one asset guarantees professional replay reconstruction;
additional required files and the exact replay map may remain. No whole 3.6 GB
archive, sudo, GPU work or further RL is authorized by this proposal. Independent
supervised imitation work can proceed while the download decision is pending.

### Independent actor-relative point experiment

`arguments-actor-origin-01/` completed a controlled supervised-only fit while the
download question was pending. It uses the same five full teaching games, 1,999
commands, input features, seed 5001, equal-replay weights and 600 epochs as the
full-human argument model. Only the point reference changes from base origin to
selected-group centroid; orientation still uses the base's canonical signs.
Fitting took 31.42 wall seconds on CPU. The Lyra and Huski games remain excluded
from fitting but are now reused diagnostic validation, not untouched final tests.

Mean error across valid targets declines from 35.66 to 31.10 tiles for Lyra and
37.22 to 27.61 for Huski. Restricting to actual point-target commands gives
36.32 to 32.79 tiles across 169 Lyra commands and 38.19 to 28.39 across 163 Huski
commands (`report-with-point-strata.json`). The declared geometric comparison
passes, but these errors remain much too large for competent imitation. Other
shared categorical heads do not establish improvement; Huski target-alliance
accuracy is only 50%. No native game or RL follows this fit.

This experimental checkpoint records `point_origin=selected_group_centroid`.
The current live argument decoder expects base-relative coordinates, so this
artifact must not be passed to live play before explicit coordinate-convention
support and its regression checks. Retain the experiment rather than silently
replacing the compatible base-relative checkpoint.

### Explicit ability input does not resolve held-game geometry

`arguments-direct-ability-01/` keeps the five training games, 1,999 commands,
600 epochs, seed 5001 and base-relative labels fixed, while appending an explicit
chosen-ability one-hot input. CPU fitting completed in 21.98 seconds. Training
point error reaches 3.24 tiles, but held-game error worsens from 35.66 to 36.26
for Lyra and 37.22 to 38.45 for Huski. Point-only error also worsens on both;
alliance accuracy declines. The declared comparison gate fails. This artifact's
extra input schema is experimental and incompatible with the current live decoder.

Raw mode accuracy improves, but the native ability catalog already restricts
many mode choices. `mode-audit.json` applies those actual restrictions: Lyra
complete mode accuracy rises from 89.77% to 93.57%, and Huski from 79.02% to
80.33%. Among commands with multiple legal modes, the corresponding changes are
80.11% to 87.50% and 65.78% to 67.91%. No teacher mode falls outside catalog rules.
This limited gain does not fix the large location errors or justify live promotion.

The authorized Astra adviser recommends stopping head ablations and testing
corpus coverage with architecture held fixed. Current training is five games of
one player in TvP/Z; both other-player diagnostics are TvT. Player and matchup
therefore change together. Screen a bounded additional block crossing those
combinations, retain whole-replay splits including both player views, and preselect
fresh evaluation games before fitting. Assess full decoded commands and combat
strata rather than point error alone. Existing Lyra/Huski games remain diagnostic
validation. Professional replay reconstruction remains a separate unmet requirement.
Human imitation comes first; no further RL is running or authorized for this stage.

### Bounded corpus coverage screening

`corpus-crossed-screen-01.json` records ten additional public human replay
sources, their content hashes, native metadata and names, totaling 899,068 replay
bytes. Only 51957 and 51959 match installed Base75689. Replay 51957 is Mez's
Terran mirror win against Butte; reserve the whole replay for candidate training.
Replay 51959 is Mez's Terran-versus-Zerg win against Provornuk; reserve both views
for a fresh held game before fitting. Reconstruction of 51957 is supervised,
fog-enabled and CPU-only, with a 300-second wall limit.

Cody (51955) and CyberManiac (51954) supply the missing other-player TvZ sources,
but both require Base75025. ProbyTheProb (51952) also requires that engine.
The remaining candidates require Base75025 or unavailable Base75800. They remain
excluded from native teaching until their exact engine can reconstruct them.
No candidate is claimed to be a verified professional. A partial same-player
coverage addition cannot establish the proposed crossed-player experiment; keep
that limitation explicit rather than silently changing its acceptance conditions.

Replay 51957 reconstruction completed in 135.13 wall seconds: 13,540 consecutive
observations, 121 sampled quiet states and 897 native gameplay commands, with fog
of war enabled and zero untranslated commands. Its issued-event audit retains
326 commands in 324 teaching rows, excludes 571 engine repeats and explicitly
records six unresolved events out of 332 human command events. Those unresolved
events do not become labels. The native Victory is the recorded human's result,
not a learned bot victory. Reconstruction of reserved replay 51959 follows;
no model has been fit on either new replay.

The first 51959 reconstruction terminated with an importer error after 118.97
seconds: `ReplayExamples.push` encountered an action unsupported by
`Command.from_proto`. It has no completed dataset receipt and is excluded from
teaching. `replay-51959-diagnostic-01.py` repeats the exact replay in a separate
output and captures the offending protobuf action before re-raising, preserving
the failure rather than silently dropping potentially important gameplay.
The action's actual payload must determine the eventual fix and regression test.

### Timestamp-only native replay records

The diagnostic reproduces the 51959 failure in 117.29 seconds and captures the
exact unsupported action: `{"game_loop":12580}` with no payload fields. Original
replay events around that loop contain command-target and command-manager state
updates, not an issued SCmdEvent at loop 12580. Do not fabricate a command label
or claim a specific native event-to-placeholder mapping from this evidence.

`ReplayExamples.push` now separately counts records whose only present protobuf
field is `game_loop` as `empty`. Known unsupported payloads and entirely fieldless
actions still reject. The regression first reproduced the original failure,
then verifies both same-packet gameplay preservation and fieldless rejection.
The independent runtime reviewer found no actionable concerns. All 170 tests
pass in 9.73 seconds (`unittest-twentysecond.log`), Ruff passes changed files,
and diff whitespace checks pass. Complete native reconstruction into
`human-51959-fixed-01/` is the remaining verification of the original symptom.

The fixed native replay completes in 126.80 seconds: 12,999 consecutive
observations, 117 sampled quiet states, 1,007 gameplay commands and exactly one
separately counted timestamp-only record. Fog is enabled and no untranslated
commands are reported. `issued-51959-held-01/` retains 439 human commands in
437 rows, excludes 568 engine repeats and explicitly records six unresolved
human events out of 445. Native completion verifies the original import failure
is resolved. The source SHA, fog, count reconciliation and preselected held role
were checked against the corpus contract. Both sides of this replay stay out of
training. It is now a ninth reconstructed named-human game, not professional
corpus acceptance or evidence of improved learned performance. All verification
and reconstruction jobs for this fix are terminal.

### Fixed-epoch matchup coverage comparison

`arguments-matchup-coverage-01/` adds only Mez's 51957 TvT teaching game to the
original five-game argument fit: 2,325 commands, unchanged base-relative inputs,
32-hidden architecture, seed 5001, equal-replay weighting and 600 epochs.
Fitting/evaluation finishes in 25.03 CPU wall seconds. This is fixed epochs,
not compute-matched: the additional game increases optimizer minibatches.
Both player views of each evaluation replay remain outside the training split.
The new 51959 TvZ game is a fresh test; Lyra and Huski remain reused diagnostics.

The declared gate assesses decoded arguments, with the actual human ability and
actor group supplied equally to both models. It requires exact unit target or
point within two tiles, correct absence/presence of targets, queue and autocast,
using native catalog mode restrictions and the same live decoder. It does not
assess ability choice, actor selection, timing or complete command imitation.
The gate requires improvement on both TvT diagnostics, no decline on fresh TvZ,
and no decline in enemy-unit argument fidelity. It **fails**.

All-command argument fidelity changes from 35.38% to 35.09% for Lyra, 25.90% to
28.52% for Huski and 28.02% to 29.38% for fresh TvZ. Attack fidelity changes from
0/52 to 0/52, 0/55 to 1/55, and 0/104 to 2/104 respectively. Enemy-unit fidelity
remains zero on both TvT games and changes from 0/28 to 2/28 on TvZ. Meanwhile,
mean raw target distance improves from 35.66 to 32.16, 37.22 to 32.18, and 38.48
to 29.05 tiles. The disagreement between distance and argument fidelity shows
why location-error improvements alone cannot support imitation competence.
Target-alliance accuracy also falls on both TvT games. Training error is 4.96
tiles; the held gap remains substantial even for a new game of the same player.

The independent runtime reviewer verified the oracle decoder comparison and
identified missing before-fit extracted-artifact/code bindings. A separate
`integrity-audit.json` binds 41 current files, including teaching data, static
catalogs, checkpoints and imported source, then exactly reproduces all held
metrics and decoded comparisons with unchanged before/after hashes and no fit.
This is post-run evidence; it cannot retrospectively supply missing pre-fit
hashes. Future experiments must bind actual dataset files and source before use.
Preserve this failed experiment; no live promotion, longer sweep, RL restart or
full crossed-player coverage claim follows. Other-player TvP/Z and verified
professional examples still depend on resolving exact native-engine availability.

### Attack failure components and available spatial cues

`attack-failure-diagnosis-01.json` separates attack argument failures without
fitting. Both models receive the human ability and actor group. On Lyra, Huski
and reserved TvZ, baseline queue accuracy is 78.8%, 81.8% and 97.1%; coverage-model
queue accuracy is 90.4%, 89.1% and 99.0%. Mode accuracy is a separate problem,
especially Huski/TvZ (baseline 61.8%/64.4%, coverage 60.0%/54.8%). Location errors
remain large even among predictions decoded as point commands: baseline median
37.57/24.34/42.69 tiles, coverage 32.47/25.96/22.91 tiles. Point predictions within
two tiles number 0/51, 0/33, 0/53 for baseline and 0/46, 1/33, 0/45 for coverage.
The unit-target attacks match 0/8 and 0/24 at baseline, versus 0/8 and 2/24 after
coverage expansion. Thus queue handling alone cannot explain the failed attacks.

Human point attacks total 52, 47 and 80. A currently visible enemy lies within
five tiles of the human target in 24, 23 and 47 respectively (94/179 overall).
These are player-observable units, not hidden opponent state. Remembered enemies
supply additional candidate locations but must retain stale/uncertain semantics.
This supports investigating point selection conditioned on local spatial relations,
not simply more epochs of the base-relative regressor. It does not prove that a
nearest-enemy rule is the human strategy, nor that every attack targets an enemy.
General map-point choices and noncombat commands must remain available.

A useful next bounded supervised experiment can reuse the existing terrain and
candidate-position features for a point scorer, with a full-map candidate grid,
currently observed unit relations, chosen human ability and group. Bind dataset
files/code before fitting, declare candidate quantization coverage and failure
gates, retain whole-replay separation and compare decoded point fidelity rather
than raw distance alone. Start as an explicit component experiment; no live
promotion, complete imitation claim or RL follows without subsequent full-command
and native evidence. Professional and crossed-player corpus requirements remain
open independently of representation experiments.

### Full-map attack point scorer experiment

`attack-point-scorer-01/` fits one fixed supervised point-component experiment,
with human Attack ability, actor group and point-mode supplied to both models.
It retains all map positions on a two-tile grid; it does not script an enemy
choice. Inputs reuse terrain and currently observed unit/candidate relations,
frozen macro context, and a training-derived selected-actor type vocabulary.
Six teaching games supply 365 point commands. Positives are nearest grid points;
64 global/local/actor-near negatives per command are class-balanced then weighted
equally per replay. Code, actual dataset files and frozen checkpoints are hashed
before fitting and checked unchanged afterward. All three evaluation games are
now reused diagnostic validation. No game is described as a new untouched test.

One 100-epoch CPU fit and full-grid diagnostic evaluation finish in 11.28 seconds.
Mean error drops from 39.70 to 17.20 tiles on Lyra, 32.42 to 16.50 on Huski, and
45.78 to 12.54 on TvZ. The two-tile fidelity changes from zero on each game to
2/52 (3.85%), 5/47 (10.64%), and 5/80 (6.25%). All 179 teacher points have a grid
candidate within two tiles, so quantization does not explain these misses.
The predeclared gate requires at least ten percentage points higher fidelity and
ten percent lower mean error on each game; it **fails**. This supports a spatial
representation direction, not live competence, full-command imitation or RL.
The point artifact is an absolute-grid scorer, not a replacement for the live
base-relative coordinate decoder. It remains experimental and unwired.

The independent reviewer found a tied-distance edge case in local-negative
sampling: `argsort(d)[1:65]` need not remove `argmin(d)`. A separate no-fit audit
reproduces the defect on a synthetic point at (1,1), and verifies that explicitly
filtering the positive index removes it. Replaying all actual seed-5007 draws
finds zero positive-in-local-pool cases and zero conflicting labels across all
365 commands. Thus this run is not invalidated by that edge case, but its sampler
must not be reused without explicit positive-index exclusion. Preserve original
source and its pre/post hashes rather than changing a completed experiment.

`training-and-sampler-audit.json` also evaluates full-map training predictions:
only 58/365 (15.89%) fall within two tiles, with per-game mean error 5.57–10.04
tiles. Even training examples are not reliably copied by this scorer. Coverage,
representation and ranking objective/capacity remain distinct unresolved issues;
the result does not justify assigning all failures to inadequate replay count.
No larger epoch sweep or native promotion follows this failed fixed experiment.
All fit/evaluation/audit jobs are terminal; no GPU, large download or further RL
was run. Exact-engine recovery for professional and other-player TvP/Z examples
still awaits the previously requested bounded-download authorization.

### Ability identity audit across reconstructed human games

`issued-ability-audit-01.json` binds the nine games' replay, raw reconstruction,
issued examples, static catalogs and receipts, then derives 93 event-ability
mappings only from single-human-event loops with a unique native target/queue
match. Native ability aliases are compared via each game's catalog remapping.
No mapping conflicts appear. One accepted command's target-only event pairing is
ambiguous in this first audit. These same-corpus mappings alone are not independent
proof of label identity and must not become a hardcoded cross-version protocol table.

`issued-ability-audit-crossgame-01.json` excludes the entire replay being checked
from its reference mappings. It checks 3,394 labels against other games with no
ability mismatches. Seventeen labels have no independent reference and remain
explicitly unverified by this audit. Seven target-only ambiguities resolve via
ability identity, including the ambiguity in the first audit; none remain among
the independently checked labels. Bound source data are unchanged throughout.
This is evidence against widespread ability-label corruption causing the failed
imitation results, not proof of a complete authoritative protocol decoder.
No dataset is relabeled and no further fit, native simulation or RL follows.
Future alignment can use verified same-build ability identity to reject/resolve
ambiguous matches, while retaining explicit unsupported cases and version scope.

### Bounded old-runtime asset recovery, offline preparation

`src/learning/casc_asset.py` extracts a requested physical CASC record from a
caller-supplied encrypted ZIP prefix. It caps input and retained content at
250 MiB and drains decoded output in chunks of at most 1 MiB. Verification
checks the physical key, framed BLTE header/chunk hashes, decoded size and content
key. Unsupported frame formats fail explicitly. It does not verify the whole
ZIP CRC, install assets or perform network requests.

Eight regression tests cover bounded reads, high-expansion skipped prefixes,
corrupt content and oversized compressed frames. The complete suite passes
178 tests (`unittest-twentyfourth.log`); Ruff passes the module and tests.
`old-casc-probe/casc-asset-offline-prefix-check-02.json` recovers and verifies the
already cached encoding record from 37,748,736 encrypted bytes and independently
verifies the cached root record. Both match previous verified content; this
check uses no network and completes in 12.25 seconds.

The ignored one-off `old-casc-probe/recover_assetsproduct.py` defaults to offline
cache reads. Any authorized online attempt reserves its entire requested range
before HTTP in a locked, atomically written, plan-hash-bound shared ledger.
Reservations survive failed/interrupted attempts and new output directories.
Exact 206/Content-Range checks precede bounded body reads. Its `network_bytes`
counts completed returned body reads only; it is not an exact count after an
interruption. `reserved_network_bytes_cumulative` is the conservative enforced
bound. `recovery-budget-audit-01.json` reproduces a mocked interruption, rejects
a second attempt before HTTP at the cumulative limit, and confirms offline
refusal without HTTP. An independent reviewer confirms the accounting repair.
No actual asset prefix download or installation has occurred. The requested
large-download authorization remains unanswered, and professional replay
playback remains unverified. Further RL remains held pending competent imitation.

### Categorical map-location training-copy diagnostic

`attack-listwise-sanity-01/` tests whether the sampled binary candidate objective
contributes to the poor training fit. One predeclared CPU fit uses exactly sixteen
teaching Attack point commands: first three in each of the first four teaching
games and first two in each of the last two. Human ability, actor group and point
mode remain supplied. The same fog-safe candidate features and two-tile full-map
grid feed a 32-hidden-unit scorer. Categorical cross entropy compares every map
candidate within each command; it does not sample negatives. Seed 5010, learning
rate .001 and 100 epochs are fixed before fitting. No validation games or live
policy are used, and this checkpoint has no live decoder integration.

The fit completes in 2.38 seconds. Training-copy accuracy within two tiles is
10/16 (62.5%), compared with the prior binary model's 3/16 (18.75%) on exactly
these sixteen commands. Mean error falls from 9.80 to 2.31 tiles. The predeclared
90% training-copy gate **fails**. This is a small diagnostic comparison of two
checkpoints with different training-set sizes and objectives, not a controlled
objective-only ablation: the old model fit 365 commands, the new one sixteen.
It motivates testing categorical location prediction on the real corpus; it
proves neither held-out generalization nor full-command competence. Source,
datasets and frozen checkpoints listed in the contract retain identical pre/post
hashes. The recorded inventory is not a complete transitive dependency manifest.
No epoch sweep, native promotion or RL follows this failed sanity gate.

The reviewer independently recomputes all sixteen new/baseline predictions from
saved checkpoints and confirms the failed gate and correct softmax/tanh/Adam
math. `dependency-audit.json` additionally binds the two consumed reports and
five omitted imported helpers at audit time. Six of those seven additional
files match bindings from the original completed candidate experiment; the new
report has no inherited earlier binding. This does not retroactively establish
complete pre-run provenance for the new diagnostic. The comparison remains
confounded by sixteen-command specialization versus the 365-command baseline.

### Categorical location prediction on the full teaching corpus

`attack-listwise-corpus-01/` applies the same categorical location experiment to
all 365 teaching Attack point commands from the previous binary scorer's six
games. A pre-fit contract fixes 32 hidden units, seed 5010, learning rate .001,
100 epochs and the full two-tile candidate grid. All consumed helper source,
reports, datasets and frozen checkpoints are bound before/after. The three
separate games are reused diagnostic validation, not fresh tests; the separate
whole-replay hash audit confirms no teaching/diagnostic game overlap.

The CPU-only fit and evaluation complete in 133.72 seconds. Teaching accuracy
within two tiles improves from 58/365 (15.89%) to 240/365 (65.75%); mean error
falls from 8.77 to 2.35 tiles. On diagnostic Lyra, accuracy is 1/52 versus 2/52
and mean error 15.64 versus 17.20 tiles; on Huski, 5/47 versus 5/47 and 23.77
versus 16.50 tiles; on Mez TvZ, 2/80 versus 5/80 and 13.14 versus 12.54 tiles.
The declared training-accuracy and per-game diagnostic gate **fails**. Better
training fit does not transfer to these separate games. This result separates
an optimization/training-fit improvement from unresolved generalization; it
does not establish that data count, representation or player differences alone
cause the failures. It still supplies human ability/group/mode rather than
measuring complete commands. No live decoder promotion, native game or RL ran.

The comparison uses the same teaching commands but differs in normalization,
full-grid versus sampled objective, update count and replay weighting (uniform
command updates versus equal replay weight). Therefore it is not a controlled
objective-only ablation. The new scorer avoids the earlier negative-sampler
tie defect because it uses no sampled negatives. One measured host process
sample shows approximately 190% CPU in per-core units (about 6% of the known
32 logical CPUs) and 1.01 GiB resident memory; two BLAS threads were configured.
All fitting is terminal, and there was no GPU or large download.

An independent reviewer reconstructs all 544 saved new/baseline predictions
(365 teaching plus 52/47/80 diagnostic), confirms every point/error/count and the
failed gate, verifies all 39 pre/post bindings and final checkpoint hash, and
checks actual replay hashes and whole-game split. No material objective,
gradient, prediction or provenance defect is found. The failed generalization
result remains authoritative. The next proposed bounded supervised test is
actor-linked prior-command destination history, rather than further optimization
or RL; its causal history and changed-destination behavior must be audited.

### Causal overlapping-actor command-history diagnostic

`attack-history-persistence-01.py/.json` preserves Astra's unfitted diagnostic:
reuse the latest earlier-loop Attack point destination sharing at least one
currently selected actor. Simultaneous commands across all rows are excluded;
within an earlier-loop burst the final recorded command wins ties. Previous
human commands are teacher-forced, not autonomous agent history. Categories are
same destination (within two tiles inclusive), changed destination and first
command without relevant history. First commands have no persistence prediction
and count as misses in overall accuracy. This is permitted own-command memory,
not hidden enemy information or knowledge of future commands.

The three reused diagnostic games have same/changed/first counts 10/35/7 for
Lyra, 7/36/4 for Huski and 8/68/4 for Mez TvZ. Their persistence overall hits are
10/52, 7/47 and 8/80, versus the no-history categorical model's 1/52, 5/47 and
2/80. This identifies useful omitted information but remains weak and cannot
replace strategy learning with repeating orders. Source, comparison report and
all nine datasets retain identical pre/post hashes. An independent reviewer
reconstructs all 544 teaching/diagnostic history records from raw examples and
confirms exact command mapping, actor overlap, prior-loop ordering and categories.
Every actual prestate is one loop before its corresponding action.

`attack-history-listwise-01/contract.json` fixes one supervised test adding six
candidate features: previous destination relative x/y and distance, availability,
log elapsed age and selected-actor overlap. The existing 32-unit hidden layer
learns their contribution; current command destinations and same/changed/first
categories are not input features. Training commands, seed, 100 epochs, grid and
uniform command weighting match the preceding categorical experiment. The gate
requires each diagnostic game's changed-destination accuracy to improve at least
ten percentage points and overall accuracy to exceed both frozen no-history and
persistence baselines by ten points. Teacher-forced history, new normalization
and initialization remain explicit limits. A future live implementation must
record the bot's own issued commands; this experiment has no live integration.

The history fit and evaluation finish in 173.24 seconds, CPU-only. Teaching
within-two accuracy is 268/365 (73.42%), versus the frozen categorical model's
240/365; mean error is 1.85 versus 2.35 tiles. Diagnostic overall hits are 1/52
versus 1/52 for Lyra, 4/47 versus 5/47 for Huski, and 5/80 versus 2/80 for Mez
TvZ. New/baseline mean errors are 22.76/15.64, 29.06/23.77 and 12.28/13.14 tiles.
Changed-destination hits are 1/35 versus 0/35, 3/36 versus 3/36 and 5/68 versus
2/68. Same-destination hits are 0/10 versus 0/10, 1/7 versus 2/7 and 0/8 versus
0/8. First-command hits are 0/7 versus 1/7, 0/4 versus 0/4 and 0/4 versus 0/4.
All three games remain below unfitted persistence's overall 10/52, 7/47, 8/80.
The declared per-game changed/overall gate **fails**. More reliable training fit
has again not established useful transfer across these games. Prior history is
measurably relevant, but this encoder/objective/corpus combination does not learn
it adequately. No live checkpoint, further fit, native game or RL follows.

The saved report treats missing persistence predictions as infinite error for
all-command miss accounting. Its persistence mean with first commands is thus
undefined/infinite and should not be interpreted as a finite distance metric;
no gate uses that mean. Category counts and model means are finite. Complete
command prediction, autonomous-history behavior, stronger independent teaching
players and professional replay reconstruction remain unresolved.

The independent final-output review recomputes every one of the 544 saved
predictions from final checkpoint arrays and the frozen no-history baseline,
confirms exact chosen points/errors/history/categories and all counts, verifies
43 pre/post artifact/code/data hashes plus checkpoint integrity, and independently
recomputes the failed gate. No material correctness concern remains beyond the
stated teacher-forcing, reused-diagnostic and changed-initialization limits.

### Additional compatible human-source screening and fourth player

`pro-date-filter-audit-02.json` checks three date formats with Terran and pro
filters and gets the same two replay links. Both are already screened games
whose professional participant is not the Terran teacher. This bounded search
is not evidence that no compatible professional Terran replay exists anywhere.
Do not infer professional teaching quality from an opponent or site-level tag.

`stronger-source-window-01.json` and `stronger-source-narrow-01.json` retain
bounded search responses. The two metadata screens examine 16 and 24 candidates,
including cached files. New replay bytes total 3,345,243 (about 3.19 MiB).
`stronger-source-audit-01.json` independently rechecks each local replay SHA.
The wider sample's sixteen games all require Base75800. The narrower sample
contains fifteen Base75025 and nine Base75689 games. Seven of those compatible
games are newly screened here; the other two are existing 51957 and 50925.
These are modest human examples, not a substitute for professional provenance.
Six new compatible games are additional Mez examples; the seventh adds Rom.

Rom's replay 51482 is a 4.10.0.75689 Acropolis Terran mirror, player 1 rated 4,678,
winning against Mez rated 4,568. The player name/race/MMR/outcome are verified
from both replay metadata and native engine replay info. The whole replay SHA is
99927f978ee5999ef4702ea7db448b0efd7e71017b8db5d5d9b7b5e004b93572.
`human-51482-rom-01/` reconstructs fully in 36.225 seconds with 5,244 consecutive
fog-enabled observations, 47 retained quiet-frame states and 299 native gameplay
records; no untranslated gameplay actions occur. `issued-51482-rom-01/` matches
180 of 181 human events in 180 rows, excluding 119 engine repeats. The remaining
point event at loop 4825 has no native candidate and is retained in the audit,
not silently relabeled as wait or claimed covered. Rom is a fourth named human
Terran player in the reconstructed corpus, with no verified professional claim.
This is a short game and does not establish broad teaching strategy coverage.

`compatible-expansion-split-01.json` assigns whole-game roles before model use:
Rom is a candidate teaching game; 51886, Mez versus a 4,580-rated Zerg, is reserved
fresh validation; the other new games are unassigned. Roles cover both player
views, so an opponent view cannot cross the split. No model fits or predictions
are run on these new games in this acquisition step. Old-engine recovery still
awaits the previously requested capped prefix-download authorization.

The reserved validation reconstruction completes in 176.393 seconds:
`human-51886-reserved-01/` has 14,746 consecutive fog-enabled observations,
132 retained quiet states and 1,062 gameplay records in 1,060 rows; no untranslated
gameplay occurs. `issued-51886-reserved-01/` aligns 388 of 392 human events in
388 rows, excludes 674 engine repeats, and audits four unresolved events. Neither
player view is fitted or evaluated by a model in this acquisition step, so its
fresh-validation role remains intact. The native corpus now contains eleven
source-labelled games across four named Terran teachers, still no verified pro.

The reviewer finds a concrete cadence-label issue in the original Rom issued
artifact: the row at loop 4819 reports delay 23 to the next matched command at
4842, skipping an unresolved human event at 4825. The regression test reproduces
that error before the fix. `issued_rows` now masks a delay to None whenever an
unresolved human event falls strictly between its current and following matched
command. Existing training consumers already map None to ignored delay label -1;
command identity/target labels remain usable. Events at interval endpoints do
not invalidate the interval. The audit reports how many timing rows were masked.
This is uncertain-timing supervision, not an invented wait or resolved action.

`issued-51482-rom-masked-01/` retains Rom's 180 matched commands and masks the
one crossing interval; original acquired data remain immutable.
`issued-51886-reserved-01/` has four masked intervals.
`mask_legacy_cadence_01.py` creates corrected copies of all nine older issued
datasets under `issued-timing-masked-01/`, masking 51 crossing intervals while
binding and verifying unchanged source files. Use those corrected variants for
future cadence training; completed experiments retain their original data and
are not retrospectively treated as corrected. No new fit follows this fix.
The full suite passes 179 tests in 9.704 seconds (`unittest-twentysixth.log`),
and Ruff passes the modified production module and regression test.

The independent final review confirms strict interval boundaries and verifies
None becomes delay -1, skipping only the delay gradient while preserving other
gameplay labels. It independently passes 17 issued-command/imitation tests,
compares all nine legacy copies and confirms only the 51 uncertain delay values
change, verifies unchanged original hashes and Rom's single mask, and reconstructs
all 388 reserved-validation rows/audit fields from the actual replay protocol.
No material correctness concern remains. The missing commands themselves are
still unreconstructed; timing masking does not imply complete action coverage.

### Native replay legality and full-command imitation audit

Saved human examples previously lacked the engine availability input used by the
live controller. `capture_replay_legality_01.py` attempts to query that input at
Rom's exact pre-command times. Jumping directly between command loops fails
exact own-unit-state matching at loop 4049. The independent diagnostic copy
`replay-legality-rom-02/state-mismatch.json` identifies only position differences
for three Reapers, approximately ten tiles apart. The cause is not established;
this does not prove different underlying combat outcomes. Neither failed capture
is treated as a complete sidecar for the saved observations.

The per-frame capture `replay-legality-rom-03/` succeeds for all 180 saved command
states in 36.015 seconds. A stronger per-frame capture `replay-legality-rom-04/`
checks exact player economy and every visible unit, including own units, against
the saved observations; all 180 states match in 35.854 seconds. Its native query
uses only known own-unit tags, with resource requirements enabled and fog intact.
`equivalence-audit.json` verifies all 180 availability records are identical across
the two successful captures. The records expose ability availability, not full
target/placement validity or guaranteed command execution. Of 180 teacher
commands, 179 have their ability available for every actor in the prestate query;
one SCV-training command at loop 787 is absent. That limitation is retained;
no future-state mask or teacher-ability bypass is introduced.

`full-command-audit-rom-01/` evaluates frozen prefix-240 macro, actor-membership
and argument checkpoints against Rom with the native masks. No human ability,
actor group or target is supplied. All those choices come from predictions;
engine target-mode rules constrain decoding. It remains conditional on human
event times and previous human command history, with no autonomous scheduling,
quiet-frame coverage or spatial-placement postprocessor. Rom is the teaching
candidate, not the still-reserved 51886 validation game. No fitting occurs.

Only 2/180 commands match ability, exact actor set, queue/autocast and target
(unit tag exact or point within two tiles) together. Individual field hits are
88/180 ability, 33/180 actor set, 23/180 target-point field, 124/180 target-unit
field, 168/180 queue and 180/180 autocast. Target-field scores include correctly
absent targets, so they are not spatial/targeted-command accuracy. Delay-bucket
hits are 35/178 known timing labels; masked and terminal timing are excluded.
The game has no multi-command rows in this selected dataset. Evaluation completes
in 0.705 seconds; code, datasets, captures and checkpoints listed in the contract
retain identical pre/post hashes. These scores establish poor joint imitation,
not autonomous competence, and do not justify RL or checkpoint promotion.
Further isolated target fits cannot establish full-command learning by themselves.

The independent reviewer reproduces every saved prediction, field comparison and
count for all 180 commands without fitting or output modification. It verifies
capture04 source/data bindings and digest and confirms its 180 masks are exactly
identical to capture03. The greedy macro→actor→argument decode matches the live
component path before placement/execution; human history is updated only after
predicting each current row. No blocking defect is found. Exact actor/target
copying is a stricter metric than strategically equivalent behavior; these scores
are fidelity measurements, not game-outcome measurements or an acceptance gate
for Hard opponents. The reserved validation replay remains untouched by models.

### Isolating complete-command failures during human imitation

RL remains held. `command-stage-diagnosis-rom-01/` repeats the frozen command
pipeline on the same 180 Rom commands, then supplies the correct teacher ability,
and finally supplies both the correct ability and selected units. These teacher
fields are deliberate diagnostic interventions, not learned decisions. Every joint
prediction exactly reproduces the previous full-command audit using capture04's
stronger state-aligned native availability masks.

| Supplied teacher fields | Original prefix argument model: complete hits | Existing full-five-game argument model: complete hits |
| --- | --- | --- |
| None | 2/180 | 3/180 |
| Ability | 22/180 | 24/180 |
| Ability and selected units | 33/180 | 40/180 |

The second column of models is measured in
`command-stage-diagnosis-rom-fullargs-01/`; it changes only the argument checkpoint,
keeping macro and actor checkpoints fixed. That checkpoint already exists and
was trained on 1,999 commands from five complete Mez games, with the same macro
checkpoint hash. No new fitting occurs. Different earlier training duration/data
means this comparison does not isolate a single training-method effect.

There are 105 commands with an actual point target and 37 with an actual unit
target. Even with correct ability and actors, the original model hits 0/105 point
targets within two tiles and 3/37 unit tags; the full-game argument model hits
1/105 and 1/37. Mean point error when a point is actually predicted is 51.04 tiles
for the original model (91 predictions) and 55.72 tiles for the full-game model
(100 predictions). Missing/wrong-mode points are failures, not included in those
conditional means. These counts exclude shared null targets and expose poor
spatial transfer independently of ability and membership mistakes. One teacher
ability is unavailable in the native prestate mask; the ability-and-group oracle
intentionally bypasses that restriction and must not be read as executable play.

`command-label-roundtrip-rom-01/` passes teacher labels, ability and actors through
the same base-relative, canonical-sign coordinate path and live command decoder.
All 180 commands reconstruct correctly, all 37 unit targets are present in current
entities, and maximum point-coordinate error is zero. This uses synthetic ability
availability and does not prove native legality or placement. It rules out a
label/decoder representability failure on this particular game; it does not rule
out other games' label errors or prove adequate sensory information.

All three reports bind their scripts, checkpoints, datasets and learning source
files before and after; `command-stage-diagnosis-integrity-01.json` recomputes every
reported field/count and verifies all bindings against disk. These are local
checks, not an independent model-quality review. The next representation/data
change must address target prediction as well as action and actor choice and be
measured on complete commands, rather than promoting an isolated head score.
Rom remains reused diagnostic/candidate teaching data. Reserved 51886 is unused;
no live game, model update, RL, or promotion occurs in these checks.

### Command-wise supervised unit-target objective

`TargetPolicy` in `src/learning/target_selection.py` reuses the existing CPU
network, predictor/checkpoint format and Adam optimizer, replacing only its loss
with a categorical choice among the current command's visible candidates. The
score is binary-logit difference; probabilities normalize across candidates for
that command, not across yes/no examples for each candidate. Other heads receive
zero gradients. Training labels are local candidate indices with contiguous row
ranges; optional weights apply to whole commands. Use `TargetPolicy` explicitly
for further fitting of this objective; ordinary `FactorPolicy` loads are suitable
for inference, but their training loss is different.

Three new tests first fail because the new policy is absent, then pass with the
implementation: finite-difference gradients for input/hidden/output parameters,
variable group sizes and permutation-stable target identity, checkpoint/prediction
persistence, sparse-column equivalence and zero loss/gradient for one candidate.
All 182 tests pass in 9.712 seconds (`unittest-twentyseventh.log`); Ruff checks of
the changed module/test pass. This establishes optimizer mechanics, not imitation
quality. There is no live integration or checkpoint promotion.

The fixed `target_listwise_human_01.py` experiment completes in
`target-listwise-human-02/` in 7.930 seconds: 150 epochs, seed 5004, 16 command
minibatches, rate .001, five full Mez training games, corrected timing datasets.
It uses inverse replay-command-count weights normalized within each minibatch,
not exact equal aggregate replay weighting. Lyra, Huski and Rom are reused
whole-game diagnostics; both player views remain disjoint from training. Human
ability/group and unit-target mode are supplied; it does not choose complete
commands. The first output directory was an empty failed attempt caused by a
wrong Huski dataset path, before the contract, collection or fitting; it is not a
successful batch or an alternative model.

Training copies 152/289 target identities (52.60%), below the declared 90% sanity
gate. Diagnostic exact identities, new listwise scorer versus frozen earlier
binary scorer trained on the same five games:

| Diagnostic | Listwise | Earlier binary |
| --- | --- | --- |
| Lyra | 12/51 | 12/51 |
| Huski | 12/56 | 16/56 |
| Rom | 12/37 | 16/37 |

Enemy-Attack target copying also declines: Huski 3/7 versus 4/7, Rom 7/22 versus
10/22 (Lyra has no such examples). The declared +10 percentage point improvement
on every diagnostic and nondecreasing enemy-Attack accuracy fails. Batch/update
structure differs from the binary fit, so this does not isolate the loss alone
as the cause. Keep the failed checkpoint as evidence, not a gameplay default.
`integrity-audit.json` recomputes every stratum's command/hit counts and verifies
all listed source/data/model hashes and checkpoint identity against disk. No
professional-data claim follows from these Masters-level examples, and reserved
51886 remains unused. RL remains held. Repeated failures justify consulting the
user-authorized Astra adviser about a systemic observation/teaching change before
another target-head experiment.

The independent runtime reviewer passes the three new tests and reproduces every
saved training/diagnostic target prediction without refitting. It verifies all 57
source/data/model bindings, normalization and checkpoint identity, and 2,850 Adam
updates (150 × ceil(289/16)). The grouped score-difference gradients and inherited
optimizer/checkpoint state are correct; no actionable implementation defect is
found. This validates the failed experiment's accounting, not its quality.

The Astra adviser recommends auditing complete-command reconstruction on all five
teaching games, split before/after 240 seconds, before another fit. Macro and actor
checkpoints were fitted only on prefixes while the argument checkpoint used whole
games. Unmasked reconstruction must be labelled explicitly where native ability
sidecars do not exist. Poor teaching-game joint fidelity would justify rebuilding
the components on consistent full-game inputs; strong teaching copying but poor
other-player copying would instead support widening teacher diversity. Neither
outcome would itself establish autonomous competence or permit resuming RL.

### Teaching-game reconstruction identifies a prefix/full-game mismatch

The advised audit completes in `command-stage-teaching-01/`, 85.654 seconds,
using the five original Mez teaching games and corrected timing datasets. It
freezes prefix-240 macro and actor checkpoints plus the existing full-five-game
argument checkpoint. It conditions on human event times and prior human history,
without fitting. Native availability is **not** supplied: raw macro argmax is
used, every known own actor is synthetically eligible, and engine target-mode
rules still govern decoding. Therefore these are unmasked reconstruction scores,
not executable-command rates or live-game evidence.

| Teaching period | Commands | Joint complete | Correct ability supplied | Correct ability and actors supplied |
| --- | --- | --- | --- | --- |
| Through 240 game seconds | 494 | 278 | 279 | 290 |
| After 240 game seconds | 1,505 | 2 | 11 | 851 |

Joint ability copying declines from 491/494 (99.39%) to 144/1,505 (9.57%). Exact
actor-set copying declines from 480/494 to 6/1,505; even with teacher ability it
reaches only 14/1,505 later actor sets. With teacher ability and actors, argument
reconstruction reaches 81/255 actual point targets within two tiles and 61/91
actual unit targets in the prefix; after 240 seconds it reaches 253/845 and
136/198 respectively. These targeted-command counts exclude shared null targets.
Exact coordinate copying remains limited even on teaching games; the all-fields
complete score is stricter than equivalent useful strategy.

The aggregate and every per-game/per-stage count are recomputed from saved records
in `integrity-audit.json`, and all listed source/model/dataset bindings match disk.
This is a concrete component-training mismatch, not evidence that another target
loss alone will solve full-game imitation. Stop transfer-only target sweeps. The
next fit must rebuild macro, actor and argument components using one consistent
full-game teaching set and frozen shared representation, then repeat this joint
teaching audit before spending fresh validation data. Broad independent-player
and verified professional teaching remain required after this sanity check; this
Masters corpus is not a substitute for the requested professional corpus. No
native game, RL or checkpoint promotion occurs, and reserved 51886 remains unused.

### Consistent full-game supervised rebuild

`consistent_fullgame_pipeline_02.py` completes `consistent-fullgame-02/` in
834.238 seconds. All three components use the same five corrected full-game Mez
sources (1,999 commands; maximum event time 919.64 seconds). The 10,000-second
collection bound therefore includes every teaching command. Macro: 600 epochs,
seed 4000; actors: 350 epochs, seed 5000; arguments: 600 epochs, seed 5001.
The new frozen macro supplies both later models' shared context. Its checksum
`08aecdafb1b9fe5239c9014afac7cc05e42ea4d8f91e0e8643a2ff8548e05afa`
matches both component contracts. No replay/player crosses the training split;
Lyra is reused diagnostic validation, and reserved 51886 remains unused.

The first attempt (`consistent-fullgame-01/`) failed before fitting because the
launcher resolved the virtual-environment executable symlink to system Python,
which lacked SC2 imports. The corrected runner retains the absolute virtual-env
executable path. That failure has no completed stages or fit evidence. Every
successful stage uses a fixed epoch budget and subprocess timeout; errors stop
the pipeline, with no automatic extra fits. Training uses two BLAS threads and
NumPy, no GPU. A sampled actor stage used approximately 5% of total 32-thread CPU
capacity and about 10 GiB RAM; this is a sample, not a constant load guarantee.

The macro copies 1,936/1,999 teaching abilities (96.85%): 477/494 before 240
seconds and 1,459/1,505 afterward. Reused Lyra ability copying is 61/342 (17.84%),
so training recovery is not strong other-player transfer. Actors use 209,690 unit
examples across 1,999 commands and copy 1,523 teacher-conditioned groups (76.19%).
Positive/negative individual-unit recalls are 99.86%/99.47%; small individual
errors can invalidate a whole group. Arguments' teaching mean coordinate error
falls to 1.997 tiles, versus 4.346 for the previous full-five-game model conditioned
on the opening-only macro. Changed context and fits mean this is a pipeline
comparison, not an isolated architecture-effect estimate.

`command-stage-consistent-fullgame-02/` uses the same 1,999 teacher commands as
the previous unmasked teaching audit, with the new three frozen checkpoints:

| Teaching period | Previous joint complete | Rebuilt joint complete | Rebuilt with teacher ability | Rebuilt with teacher ability and actors |
| --- | --- | --- | --- | --- |
| Through 240 seconds | 278/494 | 342/494 | 353/494 | 378/494 |
| After 240 seconds | 2/1,505 | 778/1,505 | 798/1,505 | 1,172/1,505 |

Rebuilt joint actor-set hits are 456/494 and 1,035/1,505. Actual joint point-target
hits within two tiles are 147/255 and 418/845; unit-target hits are 67/91 and
139/198. With teacher ability and actors, point hits reach 159/255 and 555/845,
and unit-target hits 71/91 and 155/198. Null targets do not count as targeted hits.
Native availability, autonomous event scheduling and engine placement/execution
remain outside this audit; previous human history and event times are supplied.

The declared sanity gate requires 95% ability, 90% exact actor sets and 75%
complete-command copying in both periods. Ability passes both; prefix actor sets
pass (92.31%), but prefix completion (69.23%), late actor sets (68.77%) and late
completion (51.69%) fail. This is substantial teaching-data recovery, still
insufficient for promotion or RL resumption. Group/target composition now limits
copying, and independent-player ability transfer remains poor.

`consistent-fullgame-02/integrity-audit.json` verifies shared macro compatibility,
all listed input/source/model bindings, identical old/new teacher rows, every
per-game/stage aggregate and the failed gate. The independent reviewer verifies
all 57 source/data bindings, checkpoint digests, finite tensors/Adam state and
update counts. It reconstructs the complete macro dataset/normalizers exactly,
independently counts all actor rows/groups and recomputes all aggregate scores.
A deterministic 21-command/63-stage prediction subset is exactly reproduced.
The full-forward comparison encountered tuple-versus-JSON-list equality in the
reviewer's harness; full prediction equality is not claimed. No blocking defect
is found, and no native-game/professional-strength evidence follows from these
supervised reconstruction results.

### Frozen-policy functional game exposes interrupted worker construction

A separate, preregistered functional evaluation uses the three consistent full-game
models without updating them: Zerg VeryEasy, seed 115001, installed AcropolisLE,
600 game seconds / 240 wall-second bound, eight-loop steps, deterministic action
selection with waiting for unavailable intent. No initial/idle-worker harvesting
assistance, residual policy or spatial learning checkpoint is supplied. The
existing engine placement primitive still filters requested construction sites.
The first invocation used the replay display name `Acropolis`; map validation
fails before any native game. The corrected basename is `AcropolisLE`, with the
resolved Season2 map path and hash bound in the second contract. This does not
establish identical terrain to each teaching replay.

`consistent-fullgame-live-zerg-02/` finishes in 29.612 wall seconds, native Defeat
at 598.929 game seconds. There are 1,678 frames and 32 model commands: seven SCV
production commands, sixteen Smart commands, two depot builds, one Barracks build
intent, two depot-lower commands, two refinery builds, one Attack and one Command
Center build. Twenty-nine native results are Success; one is
CantTargetInvulnerableUnits and two are NotSupported. The bot completes depots,
a refinery and a second Command Center, but no Barracks is ever observed and army
supply is zero throughout. Native Success acknowledges a command, not completion
of its intended work. The loss is a failed functional check, not promotion or
proof of any Hard-opponent competence. All three models, learning source files
and the map retain their contract hashes; every RL-decision trace field is null.
The native replay is retained and is not shown to the user.

`worker-interruption-audit.json` isolates one early causal sequence. At loop 1312
(58.571 seconds), the model assigns SCV 4350803969 to build a Barracks. At loop
1448 (64.643 seconds), that same SCV still has the Barracks construction order,
but the model sends a nonqueued Smart command to a mineral patch. The next
observation replaces its order with HarvestGatherSCV (295). No Barracks foundation
appears anywhere in the trace. This demonstrates an interrupted construction
intent; it does not prove it is the only failure or that a simple guard makes the
policy competent. Later raw intents repeatedly request unavailable actions,
including Barracks lift (656 frames), MULE (371) and Marine stim (137), under the
explicit waiting mode. There is no paired fallback-control comparison yet.

The counted `trace-audit.json` uses `issued_model_commands` and matches all 32
commands and 1,678 frames against the terminal receipt. An initial audit used the
wrong `commands` field and returned an empty counter; it is retained as
`trace-audit-invalid-01.json` and explicitly superseded, never evidence of no issued
commands. Models/source/map immutability was checked separately against the
preregistered contract.

The next bounded human-imitation diagnostic should examine worker-harvest labels
while a build order is pending, including selected SCV identity and queue flags.
Compare the relevant teacher cases with this failed SCV sequence before changing
execution. Any worker primitive must preserve learned macro choices and explicit
retreat/cancel controls; do not hardwire a build order or silently treat a
construction guard as a learned policy. Improve worker execution from human data
and measure autonomous production again. RL remains held, fresh validation remains
untouched, and professional replay compatibility/teaching is still unmet.

### Human worker labels distinguish queued harvesting from interruption

Three frozen diagnostics follow the native Barracks interruption without fitting
models, running another game or using reserved 51886. They cover the five Mez
teaching games and the reused Lyra, Huski and Rom diagnostics. Checksums bind the
inputs, scripts and checkpoints before/after; production code remains unchanged.
`worker-harvest-diagnosis-01/` audits Smart/Gather commands targeting observed
mineral patches, conditioned on the teacher ability with all known own actors
synthetically eligible. These are actor diagnostics, not native legal selections.

Across 68 mineral commands, the actor model copies 29 complete groups. There are
167 SCV candidate occurrences whose first order is a catalogue Build ability; humans select
44 of them, 33 with queued mining and 11 without queueing. The model selects 34
builders, including six teacher-negative candidates. All six false positives are
in reused Lyra/Huski diagnostics; none occur in these five teaching games. Merely
seeing a Build order is insufficient reason to prohibit a harvest command.

`worker-build-progress-01/` locates current visible own buildings of the expected
type within one tile of the build order's target. It does not inspect future
states or establish the player's intent. Of 167 candidate cases, 36 have no
visible foundation, 130 have unfinished foundations and one has a completed
building. All 26 human-selected builders without a visible foundation are queued.
These counts are occurrences across commands, not unique workers.
The 11 selected builders with nonqueued mineral commands have visible unfinished
foundations, with progress from 4.62% to 98.31%; they are not uniformly almost
finished. Native handling and the reason for these commands remain unverified.
Do not interpret them as proof of intentional cancellation or mining success.

`worker-queue-diagnosis-01/` supplies teacher ability and exact actor groups to the
frozen argument model. It copies queue flags for 57/68 mineral commands. The 26
selected builders without foundations occur across 19 commands, all human-queued;
the model queues 14/19. This is 11/11 in teaching games and only 3/8 in reused
other-player diagnostics. Copying training cases therefore does not establish
transfer of the worker/queue relationship.

At native loop 1448, the worker's Barracks order is present in its actor feature
one-hot, so this signal was not missing from the observation. Its actor selection
margin is +3.200527; every other SCV has a negative margin (next highest -9.126947).
The build target has no visible Barracks foundation, and the worker is 5.436 tiles
away. Using the actual issued group and traced model history, the argument head's
queue margin is -5.301648, reproducing the nonqueued command. The live report's
`correct` field means agreement with that recorded model-issued flag, not correct
human behavior. Both heads participate in the failure; adding worker-order
visibility alone cannot repair it because that order is already encoded.

An independent reviewer reproduces all three diagnostics and verifies the input
bindings, discrete labels, choices, counts and foundation descriptions. A one-thread
BLAS reproduction changes some actor margins by at most 0.000031, with no selection
changes; the live actor margin and queue decision are reproduced. No material bug
is found. The visibility, synthetic eligibility and occurrence-count limits above
remain part of the evidence.

The next imitation change should explicitly connect an SCV's pending build target
with its visible foundation/progress and supervise actor/queue choices together
on broader human examples. Existing inputs expose building information globally,
but the per-worker encoder has no direct matching-foundation/progress feature.
This is a hypothesis to test against unchanged baselines and independent-player
examples, not a demonstrated fix. Preserve humans' queued harvest and explicit
cancel/retreat actions rather than installing an unconditional builder guard.
Professional teacher extraction remains open, and no checkpoint is promoted or
RL resumed from these diagnostics.

### Opt-in worker construction cues: fixed argument experiment fails transfer gate

`actor_selection.py` now optionally appends five per-worker cues: a pending Build
order, a known order target location, a currently visible matching foundation,
its progress and worker-to-target distance divided by 32 (capped at two).
The target-location flag does not imply visible terrain: a known order point is
causal information even when terrain there is unseen. Foundation matching uses
currently observed/display-visible own units of the product type within one tile
of that target. Enemy units, snapshots and owned memory cannot create a foundation.
The cue covers an SCV's first order only; it does not restrict allowed actions.

Product types come from Terran Build entries in the extracted engine catalogue.
`actor_train` and `argument_train` enable the feature only with
`--worker-construction`, require consistent source catalogues and persist
`worker_construction_products` in checkpoint evidence. Live actor and argument
encoders independently read their own checkpoint metadata. Missing/None metadata
retains the old dimensions and values. Group inputs average the selected actors'
cues, as with their other features. No old checkpoint is rewritten or made the
default. Five tests first fail for the missing API, then pass with the minimal
feature implementation; the full 187-test suite and Ruff pass. Independent source
review finds no material defect and confirms training/runtime consistency,
compatibility and observation limits.

`worker_construction_pipeline_01.py` completes `worker-construction-arguments-01/`
in 116.787 seconds: argument fit 28.324, queue audit 1.918, full teaching audit
86.490. Its fixed bounds are 300/60/300 seconds. Only the argument model is refit:
the same five complete Mez games, 1,999 commands, 600 epochs, seed 5001, equal
replay weights and unchanged hidden architecture. Macro and actor checkpoints
remain frozen. The extra input dimensions also change initialization, so this is
a model comparison, not an isolated estimate of the cue's effect. Training uses
two BLAS threads, no GPU; a process sample is 187% of one core, roughly 5.84% of
32-thread capacity, about 193 MiB RSS during evaluation.

The new argument checksum is
`0b133aa976363d8e27bf3f46aa93311b0b1112ef9f18683a426f168a89ae21f8`.
Mean teaching target error is 2.061 tiles, compared with baseline 1.997. Queue
copying remains 57/68 mineral commands and 14/19 commands selecting builders
without foundations. The latter still splits 11/11 teaching and 3/8 reused
other-player diagnostics. Model-queued commands change from 22 to 24 overall;
that count alone is not an accuracy gain.

`worker-queue-construction-01/` evaluates the traced native loop 1448 without
executing a command. The new model queues mining with margin +1.656872, versus
baseline -5.301648. This is a frozen counterfactual, not demonstrated preservation
of the Barracks or improved gameplay. Its `correct:false` means disagreement with
the recorded old model's nonqueued flag, not evidence that queueing is wrong.

`command-stage-worker-construction-01/` evaluates all 1,999 teaching commands with
human times/history, as in the previous staged audit. Joint complete copying is
334/494 in the opening, down from 342, and 778/1,505 later, unchanged. Macro ability
and actor selection counts stay identical. The preregistered gate requires
other-player no-foundation queue copying at least 6/8, teaching 11/11, total queue
copying at least 57/68, and no decrease from either joint teaching baseline.
Diagnostic transfer and opening nonregression fail. No functional game is run,
checkpoint promoted or RL resumed. Reserved 51886 remains unused.

The independent reviewer checks all 52 pipeline bindings, shared macro/five-game
source identity, model digest, update counts and terminal bounds. It reproduces
all 68 queue predictions exactly, every saved staged aggregate, and a deterministic
21-command/63-stage prediction subset exactly with two BLAS threads. Full staged
forward reproduction is not claimed. No blocking correctness issue is found.

The cue remains available for broader human supervision, off by default. One
improved traced decision does not justify further isolated tuning or a competence
claim. Prioritize obtaining compatible independently sourced professional teaching
and defining whole-game splits before the next larger fit. Reused Lyra/Huski
diagnostics can become teaching only through an explicit split-role change; their
subsequent copying must then be reported as training, not independent transfer.

### Professional runtime asset: archive-range and identical-content routes exhausted

The next investigation targets the exact missing 75025 content, not another
imitation fit. `old-casc-probe/archive-index-local-search-01.json` scans 370 cached
CDN indexes (57,492,600 bytes) for EKey
`31271d461c33eda86a4723e3cbdd8038`. It finds the primary archive index
`8cae1b7aac0ede723affeeccc63689e9.index` and the current archive-group index. The
primary entry at byte 38,040 is page/entry aligned and declares a 24,624-byte BLTE
object at archive offset 17,619,227. Its footer checksum is independently checked
before using the entry; this is not complete index-page or archive authenticity.
Any recovered object must still pass the exact BLTE/chunk/CKey verification.

`fetch_asset_archive_01.py` preregisters only two exact range attempts, at most
49,248 reserved response-body bytes total, on the two previously used official
CDN hosts. Both return HTTP 404 for the archive object. The terminal receipt is
`asset-archive-range-01/receipt.json`, status `unavailable`; zero asset-body bytes
are retained and nothing is installed. The budget tracks reserved body reads,
not HTTP headers/error traffic. No retry or larger ZIP-prefix read follows.
The synthetic 30-byte wrapper in the unreachable decode branch is only an
adapter to the existing verifier, not a claimed physical archive record.

The user-authorized Astra adviser rejects speculative arbitrary ZIP-position
probes: the password alone cannot initialize ZipCrypto's evolving state at a
later byte, and DEFLATE also needs a block boundary/dictionary. A content digest
does not reconstruct those states. See the
[ZIP specification](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT)
and [DEFLATE specification](https://www.rfc-editor.org/rfc/rfc1951).
The adviser instead recommends searching every already available encoding
manifest for the identical old CKey, potentially under another EKey. This would
reuse identical decoded content, not substitute a newer product manifest.

`current_content_key_probe_01.py` reads the installed 75689 manifest directly from
its local physical record, never writing to the installation or using network.
It verifies the config-bound EKey, framed BLTE hashes and full decoded CKey:
44,888,032 decoded bytes, 6,539 page hashes and 699,614 encoding entries. The
required CKey `1566ae22ab93ec0f9e246c9efbc7fec4` is present with decoded size
264,581, but has only the original missing EKey; no alternative representation
is listed. No active local index resolves it. A separate read-only check of all
32 local index generations also has no matching prefix. The report is
`current-content-key-01/report.json`, status `exact_content_unavailable_locally`.
Together with the previously verified old manifest, this exhausts the two locally
available old/current manifests, not every possible external encoding manifest.

`orphan_record_probe_01.py` then checks whether an exact old record remains
physically present despite being omitted from indexes. It scans all four current
physical archives, 3,595,659,840 bytes, with a 32 MiB buffer and a 120-second bound;
completion takes 3.760 seconds. The reversed 16-byte EKey has no candidate matches.
Archive size/mtime remain unchanged, and no network is used. This scan does not
recover arbitrary alternate encodings; it rules out this specific physical header
in these four files. `orphan-record-01/report.json` records the terminal result.

Independent review exactly reproduces the current-manifest lookup and verifies
the primary index/footer/entry, two-attempt reservation arithmetic, four archive
coverage sizes and scan boundary handling. It does not repeat the full orphan
scan. The receipts initially omit executing-script/imported-verifier hashes;
`asset-alternative-source-bindings-01.json` explicitly records these retrospectively
alongside terminal receipt hashes. This is current-code provenance, not a claim
of pre-execution frozen source bindings. Size/mtime stability is weaker than full
archive digests. No result-changing parser or budget defect is found; absence and
404 conclusions remain scoped to these inspected files and two URLs.

Professional replay reconstruction remains incomplete. The bounded old-ZIP prefix
retrieval still requires the earlier pending user approval, or the exact verified
record must come from a matching existing installation. Neither guarantees that
this is the last missing startup asset. Do not claim a professional teaching
corpus, silently substitute current content, resume RL or keep guessing CDN hosts
from these results. No model/checkpoint/default changes occur in this investigation.

### Native Terran control census: engineering coverage only

`logs/roadmap/terran-native-inventory-05/` records a bounded native interface
check, not training. All 52 explicitly curated Terran unit/state names are
observed, with 121 unique queried ability IDs and 283 successful synthetic
command serialization roundtrips. Queries cover every current owned unit at
game loops 4 and 80, both with and without resource checks. The scene uses debug
resources, bypassed technology requirements, fast construction and upgrades;
even queries with resource checks therefore do not represent ordinary ladder
conditions. Synthetic roundtrips do not establish valid targets or successful
execution of every ability.

Seven fixture construction commands return native success. The subsequent state
also verifies six distinct parent buildings linked to completed Barracks,
Factory and Starport Tech Labs and Reactors, plus Supply Depot lowering that
preserves the depot tag. These commands create the test scene; they are not
learned gameplay. Direct debug spawning of building-specific add-ons normalizes
them to generic add-ons, so the successful fixture constructs them through their
parent buildings instead.

The run binds 32 source/map files before and after execution, uses AcropolisLE,
seed 115010 and SC2 4.10.0/Base75689/DataVersion
`B89B5D6FA7CBF6452E721311BFBC6CB2`. Supervision completes in 7.183 wall seconds.
The requested game cutoff is six seconds; replay metadata reports nine seconds.
Independent review reproduces the inventory, grammar coverage, bindings and
physical add-on/depot relationships without rerunning the game. Earlier fixture
attempts retain their terminal receipts: three fail on helper type/attribute
errors, while one completes with only 43 of the requested states. These are
fixture corrections, not evidence of production policy improvement.

Context-dependent abilities involving loaded cargo, ammunition, cooldowns,
orders and ordinary prerequisites still need coverage. Learned selection and
physical execution beyond representative command families remain open. No
model is fitted or updated here, the reserved human validation game is untouched,
and this result does not complete the action-space milestone. Human imitation
remains the next learning phase; RL, including micro RL, stays on hold until
human-trained behavior works competently in actual games. Professional replay
reconstruction and broader human-data transfer are still unresolved.

### Human-only corpus expansion: three audited full games, two pending

On 2026-10-06, `logs/roadmap/expand_human_corpus_01.py` starts native extraction
of five previously downloaded, compatible games: 51572, 51685, 51885, 51754 and
51483. Roles are assigned as candidate teaching before extraction; no model is
loaded, fitted or evaluated, no RL runs and no assets are downloaded. All five
observe human Terran player 1, Mez. They add map/opponent examples, not another
teacher or verified professional. Reserved validation replay 51886 is excluded.

Three full reconstructions and their human-event alignment are terminal:

| Replay | Map | Consecutive fog-enabled observations | Matched human commands | Unresolved events | Masked timing rows |
| --- | --- | ---: | ---: | ---: | ---: |
| 51572 | Cyber Forest LE | 8,480 | 217 | 1 | 1 |
| 51685 | Kairos Junction LE | 13,121 | 345 | 2 | 2 |
| 51885 | Thunderbird LE | 14,738 | 375 | 9 | 8 |

These datasets contain 937 matched commands in 936 decision rows, retaining the
single simultaneous-command burst. Every engine loop is retained, including
quiet moments. `audit_human_expansion_completed3_01.py` verifies all retained
observation timestamps, visible-unit serialization, causal command/memory times,
strict pre-command state alignment, command grammar roundtrips, human-event
accounting and every masked timing gap. It verifies bound sources against the
pre-extraction contract and current files, and every terminal output digest
against a retained progress snapshot. This is an audit of these three datasets,
not closure of the running five-game batch or independent proof of every fog
pixel. Its receipt is `human-corpus-expansion-01/integrity-audit-completed3-01.json`.
The initial audit invocation omitted PYTHONPATH and failed before reading data;
the corrected invocation uses `PYTHONPATH=.` and completes.

Replay 51754 reaches the first attempt's 300-second wall limit without a terminal
dataset receipt. Its partial output is excluded from teaching. Only after
`human-51754-expansion-01.supervision.json` reports `wall_timeout` does
`retry_human_51754_02.py` start a fresh output under a 600-second native bound,
preserving the first attempt. Replay 51483 continues in the original batch under
its 300-second bound. Neither pending game is counted as complete here. Subsequent
agents must inspect their process/terminal receipts before retrying or auditing.
The original batch handle is 47205; the separate 51754 retry handle is 91704.

A small in-memory compression probe checks a 16 MiB decoded prefix from 51572.
Compression plus decompression verification takes 0.034–0.110 seconds across
levels 1/3/6/9, producing 458–581 kB. This does not locate the full extraction
bottleneck or prove an end-to-end speedup; defaults remain unchanged. The report
is `human-corpus-expansion-01/compression-probe.json`.

No checkpoint/default changes occur. The usable human data increases, but model
competence, professional replay reconstruction and the eventual all-race Hard
goal remain unproven. Human imitation remains the learning priority; RL stays
held. The pending native jobs only reconstruct recorded human games.

### Fourth complete human game and expanded macro fit

The original five-attempt extraction batch is now terminal `incomplete` after
1,028.459 seconds, with unchanged bound sources. Both 51754 and 51483 hit their
300-second native limits; those partial outputs remain excluded. Replay 51754's
fresh 600-second retry completes in 382.069 seconds. Its terminal datasets are
`human-51754-expansion-02/` and `issued-51754-expansion-02/`: 23,995 consecutive
fog-enabled observations, 607 matched commands in 602 rows, 609 original human
events, two unresolved events and one masked timing interval. Retry source and
output hashes are recorded in `human-51754-retry-02-receipts/`.

`audit_human_expansion_completed4_01.py` verifies the fourth game's source/output
bindings, full observation continuity, event accounting, pre-command alignment,
causal histories, serializer roundtrips and timing masks alongside the original
three. Independent review exactly regenerates the fourth's issued rows from
actual replay init/game events and reproduces its audit entry. The four-game
total is 1,544 matched commands and 60,334 observations. The receipt's
`whole_batch_terminal: false` refers to the planned five-game expansion; the
original first-attempt subprocess is separately terminal `incomplete`.

Only after 51483's terminal timeout does `retry_human_51483_02.py` start its fresh
600-second retry. Output goes to `human-51483-expansion-02/` and
`issued-51483-expansion-02/`, with receipts in
`human-51483-retry-02-receipts/`. Its live handle at this snapshot is 97005.
Do not restart from the old timeout or assume the retry is complete.

`project_actor_memory_01.py` measures actual candidate-unit counts for the old
five teaching games and first three new games: 2,936 command groups and 275,609
actor examples. At the existing 11,745 float32 columns, one dense feature matrix
needs 12,948,110,820 bytes; retaining the list of dense rows while stacking needs
at least 25,896,221,640 bytes, excluding objects, groups and normalization/training
temporaries. These are arithmetic lower bounds, not a measured process peak or
the size of the subsequently expanded nine-game set. The previous actor fit used
only 339 varying columns. Before enlarging the actor fit, test compact temporary
storage against dense feature/prediction/update parity while preserving the full
saved/live input vocabulary; do not drop human examples or gameplay controls to
avoid memory use. No production collector change has occurred yet. The report
is `actor-memory-projection-01/report.json`.

`expanded_human_macro_01.py` starts one supervised macro fit on nine complete
games: the original five plus 51572, 51685, 51885 and verified 51754 retry, totaling
3,543 human commands. Settings match `consistent-fullgame-02`: 600 epochs, seed
4000, global decisions, ability balancing, whole-game 10,000-second inclusion
bound and two BLAS threads. Reused Lyra is diagnostic validation only. No GPU,
RL or native bot evaluation runs. All teachers in this fit are Mez; it adds
examples, not professional or cross-player teaching coverage.

Before the fit starts, its contract changes 51483 from candidate teaching to
`reserved_fresh_expansion_validation`. Its human states are not loaded by the
fit; this deterministic last-pending-game choice is not a randomized benchmark.
Reserved 51886 remains untouched. The macro fit freezes its actual local source
dependencies and training/diagnostic artifacts in
`expanded-human-macro-01/contract.json`; its live handle is 23482. Inspect the
terminal report before claiming a saved fit. The actor and argument components
still need consistent expanded-data fits using this same frozen macro before any
combined native evaluation. Do not mix it with old components and call that a
trained full policy or resume RL.

### Five-game data closure and same-cohort macro result

Replay 51483's fresh retry completes in 478.051 seconds, with unchanged bound
sources. It retains 26,064 consecutive observations and 685 matched commands in
681 rows; 14 of 699 human command events are unresolved and 12 timing intervals
are masked. `audit_human_expansion_completed5_01.py` completes the final integrity
audit without loading any model: five games, 2,229 matched commands and 86,398
observations. Four games are teaching candidates; 51483 is reserved fresh
expansion validation under the role assignment made before fitting. The original
first-attempt batch remains historically incomplete, while the combined retry
workflow is terminal. All native extraction handles above are now terminal.
The final receipt is `human-corpus-expansion-01/integrity-audit-completed5-01.json`.

The nine-game macro fit completes in 149.769 seconds, 600 epochs and 16,800 updates,
with unchanged bound sources. The checkpoint SHA-256 is
`7991636bb52049099825b7baccc4167cbaf01a9ecf39c4823af0bc5eb5b88cce`.
It copies 93.56% of training command abilities; the reused Lyra diagnostic is
56/342 (16.37%), versus 61/342 (17.84%) for the five-game baseline. This does not
demonstrate better independent-player transfer. Different training cohorts make
the two reported training percentages unsuitable as a direct comparison.

`compare_expanded_macro_01.py` therefore evaluates both frozen macros on the same
teaching examples, with prior human history and event times:

| Common cohort | Commands | Five-game baseline ability copying | Expanded macro ability copying |
| --- | ---: | ---: | ---: |
| Original five teaching games | 1,999 | 96.85% | 92.95% |
| Four added teaching games | 1,544 | 23.06% | 94.37% |
| All nine teaching games | 3,543 | 64.69% | 93.56% |

The frozen comparison completes in 6.246 seconds with unchanged source/model/data
bindings and exactly reproduces the baseline original-cohort and expanded
whole-cohort counts. It confirms learning of the added human situations alongside
some loss on the old ones. These are conditional macro-head predictions, not
exact complete commands, native wins or a promoted policy. Neither reserved game
is predicted or fitted. The comparison receipt is
`expanded-macro-comparison-01/report.json`.

Independent review exactly regenerates the fifth game's event/timing audit,
verifies final corpus/role/source/output bindings, and reproduces every macro
comparison metric and training-only normalization value using two BLAS threads.
It checks the fit's 42 bindings and comparison's 35 bindings. Exact ability hits
are 1,936 to 1,858 on the original five, 356 to 1,457 on the added four, and 2,292
to 3,315 over all nine. The expanded fit has 16,800 updates versus 9,600 for the
old fit: matching epochs is not matching compute. Added-game accuracy is training
reconstruction, not fresh validation or isolated proof of a data-only causal effect.

The user-authorized Astra consultation recommends one jointly trained entity-based
command model as the next architecture experiment. Its source inspection finds
that 32 commands are stored, but the ordinary global encoder reads only the last
two ability IDs; optional semantic encoding reads four richer commands. This is
confirmed directly in `global_imitation.global_features`, and must not be described
as learning from all 32 stored commands. Per-type summaries also discard individual
relationships, and frozen 32-value contexts separate actor and queue/target
learning. The traced builder interruption is a coordination failure even though
the pending construction order is already available to the learner.

The proposed experiment shares a compact entity encoder across ability, actor,
target and queue prediction, with argument losses updating the shared representation.
It uses entity pointers for unit targets and candidate scoring for spatial targets,
preserving the broad native command vocabulary. Fix one configuration/update budget;
compare complete commands and actor/ability-oracle diagnostics before native play.
Use the nine teaching games and reused diagnostics first. If teaching reconstruction
remains poor, investigate representation/optimization; if it improves without
other-player fidelity, prioritize more independent-player teaching. Do not invent
recovery labels by substituting student histories beneath unchanged human commands.
Both reserved games remain closed until a complete candidate/protocol is frozen.
This is a next-step recommendation, not implemented or accepted architecture.

The expanded macro is not combined with old actor/argument models or promoted.
All jobs described in this section are terminal; no RL resumes. Professional
reconstruction, complete-command competence and all-race Hard wins remain open.

### Joint entity model: shared encoder core verified

The implementation plan is
`docs/superpowers/plans/2026-10-06-joint-entity-imitation.md`. Task 1 adds
`src/learning/entity_encoder.py` without changing the old model or play defaults.
Compact numeric features combine with learned type/order embeddings; scene
context combines entity pooling and all 32 chronological history slots. Individual
entity embeddings remain available to later actor/target heads. One backward
interface propagates downstream context/entity gradients into shared projection,
type, order and history parameters, accumulating repeated categorical IDs correctly.
Row-shape guards prevent NumPy from silently broadcasting one entity/history role
over multiple rows.

Five missing-encoder test failures are observed before implementation, followed by
two failing row-alignment tests before their guards. Seven targeted tests pass:
finite-difference gradient checks, entity permutation, empty-state handling,
oldest-of-32 history sensitivity and row alignment. The full suite passes
194 tests in 9.769 seconds; modified files pass Ruff and diff checks. The suite
receipt is `logs/roadmap/unittest-twentyninth.log`.

`entity_encoder_smoke_01.py` uses the installed catalogue's complete 1,970 unit
slots and 3,801 ability slots with synthetic 200-entity inputs. It completes
1,000 forward/backward calls in 0.163 seconds including postchecks, with unchanged
parameters/source hashes. Encoder parameters occupy 881,536 bytes; this synthetic
numeric entity payload occupies 25,600 bytes plus 3,200 categorical bytes. These
are encoder-only sizes/timings, not full-model memory, actual human training or
native simulation speedups. No optimizer, GPU, replay prediction or RL runs.

This completes only the encoder implementation task. The complete command heads,
semantic example conversion, spatial candidate coverage, shared queue/target-loss
checks, human fit and opt-in native integration remain. The old macro still uses
its old history encoding; no joint policy or improvement is claimed, and both
reserved games stay closed to model prediction/fitting.


### Shared entity command model: implementation and real-label coverage

The compact shared encoder now has jointly trained full-vocabulary ability,
variable-size actor membership, group-conditioned mode/queue/timing and unit/point
target heads. Point targets use map-wide cells plus continuous offsets. Queue and
target losses numerically backpropagate into the same encoder; this remains an
imitation architecture, with every RL path held.

The causal converter preserves all 32 command-history slots and entity references,
exact integer tags, simultaneous command bursts and masked unresolved timing.
Enemy memory exposes only known identity/position, with no hidden attributes or
unit-target eligibility. Own remembered entities remain actor candidates. A missing
human target is explicitly excluded without dropping later commands or inventing a
sensor input.

`logs/roadmap/entity-examples-real-audit-02.json` checked all nine Mez teaching games:
3,542/3,543 commands roundtrip through complete labels and raw grammar. The excluded
command is 51754 loop 3480, Attack 23 targeting 4367319041, absent from the recorded
pre-command visible target candidates. Source/input bindings are unchanged; reserved
51483/51886 remain unopened. Conversion coverage does not measure learned accuracy.

Thirteen new targeted tests and the whole 207-test suite pass (9.796 seconds), with
Ruff/diff checks green. Numeric entity payload for these nine games is 268,004,904
bytes and model parameters are 1,447,856 bytes; these are not full trainer RSS or
native throughput measurements. There has been no joint model fit or native game
with this model yet. Next: freeze one supervised configuration/update budget, fit
these human commands and audit complete predicted commands before native play.


### Joint human fit: terminal reconstruction results and next bottlenecks

The first fixed shared-model fit completed all 200 epochs / 44,400 updates on the nine
Mez teaching games. It used a fresh seed 7000/7001 checkpoint, hidden 32, batch 16,
rate 0.001, uniform shuffled commands and two CPU threads. A one-epoch throughput
smoke chose the budget; no architecture/rate sweep or RL was run. Fit time 483.316s,
total 502.466s; final joint loss 0.970165. All input/code/checkpoint bindings remain
unchanged. Report: `logs/roadmap/joint-entity-fit-01/report.json`; checkpoint SHA256
`e0cd9737fccf466c3b683bfc343b311c605b457e05f70ea4155ddf3f712541aa`.

| Human-state reconstruction | Teaching 9 games | Reused Lyra/Huski diagnostics |
| --- | --- | --- |
| Ordinary ability |3540/3543 (99.9%)|189/647 (29.2%)|
| Ordinary exact actor group |1563/3543 (44.1%)|138/647 (21.3%)|
| Ordinary complete command, one-tile point tolerance |628/3543 (17.7%)|11/647 (1.7%)|
| Complete with human ability and actors supplied |1679/3543 (47.4%)|165/647 (25.5%)|

The frozen 95% ability / 90% actors / 75% complete teaching prerequisite fails. No native
play, fresh 51483/51886 prediction, professional coverage or playing-strength claim
follows from this result. The model sees actual human histories here, not the
histories its own mistakes would create in a game. Known timing matched 3101/3493
teaching commands; complete-with-timing 612, reported separately from untimed totals.
One unseen-target label remains explicitly excluded but in the 3543 denominator.

Reloaded verification independently regenerated ordinary field counts and checked
the complete update budget plus source/checkpoint bindings:
`logs/roadmap/joint-entity-fit-verification-01.json`. Actor selection fails on 472
oversized groups, 510 undersized groups and 998 groups with the right size but wrong
members. With the human ability/group supplied, spatial cells match 1567/1970
(79.5%), while continuous offsets fall within one tile only 304/1970 (15.4%) even
when supplied the human cell. These are explicitly oracle diagnostics.

Two implementation choices are likely contributors to test next: actor loss is
averaged over eligible entities, which can weaken exact-set supervision, and the
spatial residual head learns offsets that wrap at cell boundaries without being
conditioned on the chosen cell. The audit does not establish those choices as the
sole causes of the errors. The next experiment should strengthen actor ranking and condition residual
positions on the chosen cell with a loss in physical tile units. It should retain
broad controls, jointly trained shared features, the same fixed source split and
an honest full-command audit. Repeating the same fit longer is not the chosen next
step. Native play and every RL path stay held until reconstruction improves.

The independent whole-candidate reviewer found no actionable code defect and ran
27 focused tests. The full suite passed 214 tests in 9.756s, with Ruff/diff checks green.
A one-second whole-machine CPU sample during the live fit was 6.575% on 32 logical
CPUs; this is not a peak-load measurement. All training/audit handles are terminal.


### Refined actor/spatial fit: material teaching gains, no cross-player gain

The fixed refinement fit completed all 200 epochs / 44,400 updates in 518.106
seconds of fitting (537.437 total). It held the nine teaching games, seed, width,
batch size, learning rate and budget constant; the selected-set ranking and
cell-conditioned physical-tile loss changed together. Checkpoint SHA256:
`95167fc48ca862eca5b118bc106fc20bdb20a0e7e51bec785e12ce4052a4924e`.
Both saved checkpoints regenerated their entire ordinary/oracle audit exactly;
comparison receipt: `logs/roadmap/joint-refinement-comparison-01.json`. Input/code/
checkpoint bindings were unchanged at fit and comparison completion. Historical
source hashes are not claimed unchanged after the later timing-validation fix.

| Ordinary human-state reconstruction | Baseline | Refined |
| --- | --- | --- |
| Teaching ability |3540/3543|3532/3543 (99.7%)|
| Teaching exact actor group |1563/3543|2033/3543 (57.4%)|
| Teaching complete command, one-tile tolerance |628/3543 (17.7%)|1495/3543 (42.2%)|
| Reused Lyra/Huski ability |189/647|174/647|
| Reused Lyra/Huski exact actor group |138/647|89/647|
| Reused Lyra/Huski complete command |11/647|9/647|

With human ability/actors supplied, teaching complete commands improve from
1679 to 2542/3543. With the human cell supplied explicitly, offsets within one tile
improve from 304 to 1754/1970 (15.4% to 89.0%). Correct cells fall from 1567 to
1224/1970 (79.5% to 62.1%). These are oracle diagnostics, not ordinary inference.
Oversized actor groups rise from 472 to 1000, undersized groups fall from 510 to
368, and correct-size/wrong-member groups fall from 998 to 142. The combined
change improves exact members and fine geometry while leaving group-size and
coarse-cell errors; separate component causality is not established.

The frozen teaching gate still fails. Reused other-player results deteriorate;
there is no promotion, native game, fresh reserved prediction, RL or Hard claim.
The next priority is broader human teachers with this architecture held fixed.

A diagnostic input-selection mistake was corrected after both jobs ended: Huski
used an older file with seven unmasked uncertain timing gaps. The corrected file
has identical observations/actions/arguments; only those seven delays become
unknown. Training and every non-timing comparison remain unchanged. Corrected
known timing is 633/647, with ordinary delay matches 143 baseline / 114 refined;
complete-with-timing remains 2 / 3. Receipt:
`logs/roadmap/joint-refinement-timing-diagnostic-correction-01.json`. Original
reports are preserved as historical outputs; the correction supersedes their
diagnostic timing counts. A tested source validator now rejects such gaps before
future fitting. Full suite: 225 tests in 9.815 seconds, Ruff/diff checks green.

A prospective source-only diversity audit binds eleven teaching games from three
players: Mez 3543 commands, Lyra 342, Huski 305 with corrected timing; total 4190,
4189 complete representable labels. Rom's 180-command game stays diagnostic.
Previously reused Lyra/Huski diagnostics explicitly become teaching before any
new fit; this is not randomized fresh acceptance. No model has fitted/predicted
this new split in the audit. Bindings:
`logs/roadmap/multiplayer-teacher-split-contract-01.json` and
`logs/roadmap/multiplayer-teacher-split-audit-01.json`. Professional teachers remain
zero, and reserved 51483/51886 stay closed. Freeze the next update budget before
fitting; the full professional/micro/native/Hard/higher-difficulty roadmap is open.


### Three human teachers: added players learned, aggregate gate still fails

The frozen169-epoch fit completed44278updates /707941command presentations. Reloaded checkpoints reproduced the complete reports exactly, with source/code/checkpoint hashes unchanged. Receipt: `logs/roadmap/diverse-human-fit-comparison-01.json`; checkpoint SHA256 `87d3d072ed92b7525c2e43775d467c0ad36e7d2ca4a0049f5d9da581e60f3feb`. On the same expanded4190-command teaching cohort, complete commands fall1504->1418 (33.8%), while ability rises3706->4162 and exact groups2122->2232. Mez complete1495->1173/3543, Lyra6->125/342, Huski3->120/305. Lyra/Huski are now teaching, so their gains are reconstruction, not generalization. Separate Rom diagnostic complete6->7/180, exact groups63->45; this is not meaningful independent-player competence.

The actor diagnostic `logs/roadmap/actor-cardinality-audit-01.json` compares the existing cutoff against supplying human ability and human group size. Highest-ranked K actors recover3545/4189 exact teaching groups (84.6%), versus2238/4189 (53.4%) with human ability and the normal cutoff. Diagnostic Rom61->102/180 with these oracles. This isolates considerable ranking-versus-size error without changing inference. Next investigate a learned context-conditioned cutoff with no fixed group cap. Coarse spatial cells also remain weak1031/2302 even with human ability/group supplied; offset accuracy with human cell supplied is1955/2302.

Both fit/comparison and actor-audit handles are terminal. The teaching prerequisite fails. All RL and native promotion remain held; professional teachers remain zero and reserved51483/51886 remain closed. The whole roadmap remains active and incomplete.


### Spatial observation gap confirmed during the cutoff fit

A source-bound preprocessing audit inspected all 4164 teaching observation rows (4190 commands, including same-frame bursts). Every row carries visibility and creep grids; 458 have nonempty effects. All eleven games carry static terrain-height, pathing and placement grids. The compact `state_inputs` conversion does not read those grids, effects or radar contacts, and point candidates currently contain only normalized coordinates. Isolated mutations of map/effect/radar fields leave every model input identical. Receipt: `logs/roadmap/spatial-sensor-gap-audit-01.json`; audit handle25032 ended successfully with code/source bindings unchanged. Radar contacts were empty in this teaching corpus; no empirical radar-learning claim is possible here.

This confirms an observation limitation, not a proven cause of reconstruction errors. Extraction retains the data, so no replay rerun is needed to add spatial sensing. After the frozen cutoff experiment completes, address fog-safe spatial candidate/context features using the saved grids and visible effects. Do not mask away human target cells based on terrain; legitimate attack, movement, construction and air commands have different constraints. Preserve full-map candidate coverage and physical point round trips. Existing compact imitation is a first experiment, not the final sensory interface. Native/RL remain held.


The follow-up spatial-target audit reused the existing `decode_terrain` implementation (native y,x indexing, MSB-first packed bits). Across all 2302 teaching point targets, visibility pixels are 1912 visible, 225 fogged and 165 hidden. Static grid samples mark 168 target pixels non-pathable and 332 non-placeable. These are descriptive samples across different command families, not proofs of command illegality or build-footprint validity. Receipt: `logs/roadmap/spatial-target-audit-01.json`; handle90868 terminal, source hashes unchanged. Do not introduce a universal visible/pathable/placeable target mask: it would discard real human labels. An additional decoder would duplicate existing code; reuse it for spatial input integration.


### Learned actor cutoff and spatial connection

The controlled cutoff fit completed169epochs /44278updates and regenerated both checkpoint reports exactly with stable bindings. Teaching complete1418->1447/4190, exact groups2232->2268, ability4162->4167; Rom complete7->5/180. The teaching gate still fails. Receipt: `logs/roadmap/human-cutoff-fit-comparison-01.json`; checkpoint `c01f4bba26298a3c7cfc26d769f95c530081ca733c997cfe0b9c7ee343ddc557`. This is a small reconstruction gain without independent-player improvement. All fit04/comparison handles are terminal.

Opt-in spatial imitation now consumes every pixel of each eight-tile terrain/pathing/placement/visibility/creep patch and explicit edge padding. Learned spatial embeddings contribute to both global command context and target ranking; no visibility/pathing target mask is introduced. The previous checkpoint regenerates its complete reports exactly with spatial mode disabled (`spatial-legacy-compatibility-01.json`). Full suite237tests, including numerical global/point/shared gradient checks; independent review found no actionable defects. The isolated profile estimates3.18GBof teaching feature payload, not RSS or total training memory. No spatial model has been trained yet. Effects/radar, professional corpus, native competence, micro transfer and Hard/higher difficulties remain open; RL stays held.


### Spatial imitation: better teaching targets, transfer still weak

The spatial fit completed169epochs /44278updates in673.285fitting seconds (712.458total). Both checkpoint reports regenerated exactly with stable source/code/checkpoint bindings; `human-spatial-fit-comparison-01.json`. Teaching complete1447->1896/4190 (45.3%), exact groups2268->2420, targets2328->2935; all three teaching players improve. Oracle correct map cells1051->1797/2302, while fine offsets with supplied cells1904->1885. Separate Rom complete5->4/180 and ability92->80. No independent-player gain or passed teaching gate. Checkpoint SHA256 `4ee4968232482ce75c9d93dfcb2b6de26df89e75fa181d4e485e32b9050f4210`. Fit60586/comparison18788 are terminal.

The shared model now has a native execution path (`python -m src.learning.entity_play`) using the same fog-safe inputs, exact raw command decoder, model-owned issued history and learned cadence. Native replay/trace output and schema checks are implemented without scripted assistance or learning updates. Full suite241tests and independent review passed. Artificial SCV-command checkpoints, with spatial inputs disabled/enabled, each completed a30-second plumbing fixture:672frames,21commands,6successes/15resource rejections, nonempty replay and causal trace. The learned checkpoints have not been evaluated natively through this adapter; these fixtures establish only SCV command plumbing. Replay viewers are not opened. All RL stays held, and professional data, broader sensory fields, same-loop action batching, native learner competence, micro transfer and Hard/higher-difficulty acceptance remain open.


### Frozen human-policy execution diagnostic

Bounded learned native diagnostics are now permitted while imitation promotion and RL remain held. The first 60-second episode used the completed spatial human checkpoint without updates: 13 commands, 11 native successes, two unavailable-command rejections. The Barracks decision preceded Supply Depot completion (92.7% progress); the next decision tried lowering the unfinished depot. These were availability failures, not proven location failures.

An opt-in generic availability check now reobserves and reconsiders with the unchanged model when its selected ability is unavailable. Unissued intentions enter neither history nor learned-delay scheduling. It does not replace actors/abilities/targets or provide a build order; trajectory can change as the model sees new observations. Same checkpoint/map/seed/duration comparison: 48 decisions, 35 withheld intentions, 13 issued commands all accepted. Every decision reproduces exactly from the frozen checkpoint and causal history. The completed depot is lowered; Barracks (31.8%) and Refinery (47.1%) are under construction at the 60-second cutoff. There are 15 workers, zero army, zero damage and no win claim.

All paired checkpoint/code/source bindings remain unchanged, and replay/trace are retained without display. Receipts: `logs/roadmap/joint-frozen-native-wait-contract-01.json`, `joint-frozen-native-wait-verification-01.json`. The full professional imitation, sensory completeness, learned micro transfer, reliable all-race Hard and higher difficulties remain incomplete.


The follow-up frozen 180-second episode completed its planned cutoff (4033 observations): 19 issued commands, all accepted; 1914 unavailable intentions withheld. Native observed state confirms a completed Barracks and Refinery, Orbital Command, 18 workers and one Reaper, with a second Reaper command issued near the cutoff. No combat occurred. The refinery has one of three workers. All 1879 blocked Reaper intentions occur below 50 gas (1831 select Barracks only, 48 incorrectly include an SCV). Minerals accumulate to 1630. This demonstrates physical construction/army production and a resource-management failure, not playing strength. Checkpoint/source/code bindings and causal issued-only history verified; receipt `logs/roadmap/joint-frozen-native-wait-verification-02.json`. Native handle12910 is terminal with exit0; no training or RL ran.

A source-bound teaching audit locates 47 human SCV-to-refinery commands across all eleven current teaching games. Frozen prediction gets ability47/47, exact actors5/47, target30/47, complete5/47. Human group sizes: two26, one13, three5, four1, five1, eight1. Predicted sizes: one43, two1, six1, thirty1, thirty-five1; correct size13/47. Thus exact identity ambiguity alone cannot explain these errors: the model often learns the wrong number of workers. `logs/roadmap/human-gas-worker-audit-01.json` retains every human/predicted command and source bindings. This is existing teaching reconstruction, not fresh generalization. Next intervention should learn variable group size/selection from human labels, preserving arbitrary group coverage; avoid scripted gas saturation or resumed RL.


### Explicit human group-size supervision

An opt-in log-count head now predicts the number of selected actors from shared context and the predicted ability, then selects that many highest-ranked own units. Squared human log(K) supervision backpropagates through the shared encoder/ability. Native inference uses neither human group size nor a fixed cap: count is rounded and limited only by currently eligible own units. The original cutoff path/checkpoints remain default-compatible. Four new tests were observed RED before implementation and then passed; full suite247tests in9.919seconds, Ruff/diff clean. Independent read-only review found no concrete defects and passed28focusedtests. This verifies implementation, not a learning gain.

Controlled fit06 adds this head/loss to the same11teaching games/three humans, spatial/refinement/cutoff architecture, seeds7000/7001/7002,169epochs/batch16/rate.001/hidden32,1500fitwall/1650callerwall as fit05. Frozen contract/argv: `logs/roadmap/human-group-count-fit-contract-01.json`, `human-group-count-fit-argv-01.json`. Corrected live handle55880: all source roles and code hashes checked against actual configuration. No native games or RL during this fit. A first incorrectly launched job repeated nargs `--train`, retaining only the last305-command dataset; it was explicitly terminated (handle27451 exit-15) and retained under `joint-entity-fit-06-invalid-launch`, excluded from comparisons. The corrected job uses a single training flag containing all11paths.


### Group-count experiment: larger gas groups, weaker complete copying

Fit06 completed169epochs /44278updates /707941presentations,714.244fit seconds /753.365total; handle55880 terminal0. Checkpoint SHA256100297bd29db3b96520061f910c9dbfcbfaf7f9196590bd71ec8afd406076cdb. Exact saved-model regeneration of both whole reports succeeded with unchanged source/code/checkpoint bindings (`human-group-count-fit-comparison-01.json`, comparison69558terminal0). Teaching ability4171->4163, exact groups2420->2193, targets2935->2873, complete1896->1804/4190 (43.1%). Mez complete1558->1501, Lyra171->163, Huski167->140. Rom complete remains4/180, exact groups42->24. Teaching group-size matches2654->2441/4190, with more under-selection559->816. Thus adding a log-count loss is not an aggregate improvement. Baseline05 is retained; no promotion or RL.

On the original47source-bound SCV/refinery commands, correct group size13->27 but exact actors remain5, targets30->26 and complete remains5. A broader initially reconstructed subset included two remembered-refinery commands (49ratherthan47); two failed verification attempts caught this denominator difference. Final comparison explicitly matches original dataset/loop/raw-command identities and reproduces the47case baseline. Historical partial/failed outputs are retained and superseded. `gas-worker-actor-ranking-audit-01.json` supplies human ability and size solely diagnostically: exact groups6->8/47, selected human workers22/97both, with non-SCVs selected in7->11cases. This confirms substantial ranking/identity error even with size supplied; exact identity alone can overstate practical error when another worker performs the same function.

One frozen candidate native diagnostic is therefore authorized under the existing diagnostic ruling, same AcropolisLE/VeryEasyZerg/RandomBuild/seed130001/180gameSec/120wallSec/availability-retry as baseline05. Contract `joint-frozen-count-native-contract-01.json`; live handle33360. Inspect actual gas staffing, building completion, army and engine results. No model updates, human oracles, macro recipes, promotion, strength or fresh-human validation claims. Professional corpus, full sensory/action coverage, learned micro transfer, all-race Hard and higher difficulties remain open.


The candidate native diagnostic33360 is terminal0 and confirms regression: 180.045game seconds,9issuedcommands all accepted,3119withheld SCV-production intentions. Final state has15workers,15supply,1955minerals,0gas,2idleworkers and no Depot/Refinery/Barracks/army. Supply-cap deadlock prevents progress. All checkpoint/code/source bindings, exact issued-only causal history and nonempty replay verified (`joint-frozen-count-native-verification-01.json`). Count06 is a failed candidate; previous05 remains retained. No optimizer, RL, promotion or strength evaluation occurred. More exact copying of group size alone cannot repair intent/actor/target choices or recover from divergent states. Next investigate compatibility for professional teachers and legal-action/state coverage, preserving broad raw controls and human-first training.

### Professional observation databases: bounded compatibility probe

Human imitation remains the current stage; RL is stopped. A public preconverted tournament database offers a route around the unavailable Linux build76052. Primary sources are [sc2-serializer dataset documentation](https://5had3z.github.io/sc2-serializer/replay_data.html), [published tournament observations](https://bridges.monash.edu/articles/dataset/Tournament_Starcraft_II/25865566), [converter source](https://github.com/5had3z/sc2-serializer), and [original tournament replay archives](https://zenodo.org/records/14963356). Probe artifacts are under `logs/roadmap/pro-preconverted-probe-01/`; these are candidate data, excluded from training.

Downloaded metadata `gamedata.db` matches publisher MD5 `5c9603fed8a5179aadc0671bc0e44ca5`. Original WCS Fall replay samples identify Clem as winning Terran player1 against Scarlett/Zerg, Harstem/Protoss and a Terran whose raw alias is BackupI (archive path says Future; preserve both labels). All require4.10.2.76052, unavailable locally. Three independently compressed observation records were retrieved through exact HTTP206 ranges, without downloading the full1.62GB partition or91MB raw archive. Conservative reservation12,638,633bytes remains within the16MiB small-sample transfer contract. The separate250MiB legacy-client asset request remains unanswered and was not executed.

A format correction matters: the published offset table contains1200 eight-byte offsets, while the inspected current Linux C++ `std::streampos` layout led the initial prefix probe to use16bytes. Earlier guessed record indices were doubled and are superseded. The corrected complete table is saved and bound by SHA256. The database's filenames/hashes differ from those in the raw archive; direct hash matching did not establish identity.

Corrected candidates are idx294 (Clem versus BackupI/Future, duration12815),774 (Clem versus Harstem,9526) and870 (Clem versus Scarlett,19383). Header duration, race, result and APM match the original replay. Decoding scalar/image/action blocks succeeds with bounded lengths; unit blocks remain undecoded. These records contain1060,584 and1899 converted commands respectively, including engine repetitions. Exact issue-loop and target-type/target matching against original player0 SCmdEvents yields641/654,386/402 and1154/1173 unique matches:2181/2229 total. Player0 maps to working-set slot0/player1 in each replay's initData. Integer-truncated points and lower32 target-unit tags are compared; ability and actor identity are not used in this preliminary matching. The resulting replay ability-link/command-index to converted ability mapping has no conflicting IDs across these matched commands, but this is not an independent ability verification. Receipts: `clem-record-retrieval.json`, `clem-raw-samples.json`, `fall-actions-{294,774,870}.json`, `command-alignment-{294,774,870}.json`, and `professional-command-alignment-summary.json`.

The original events can supply exact point precision and queue flags for uniquely matched commands. No missing field is filled with an assumed value. Remaining gates before any training: independently verify abilities and selected actors; reconstruct unit blocks and confirm that observations precede command effects; verify fog safety; account for absent upgrade observations, truncated unit orders/buffs and128x128 minimap resolution; handle unknown autocast/action modes and ambiguous/repeated commands explicitly. Metadata plus target matching is substantial correspondence evidence, not a complete professional teaching corpus. Professional training-eligible games remain0, Hard wins remain unproven, and the full roadmap stays open.

### Professional unit-block and selection checks

The three candidate records now decode through the end of both flattened unit blocks, with exact byte consumption and no trailing data. Era source `17da32ba4501b8ff43d8f899e3899c1244cc6e0a` defines each unit field vector plus contiguous observation-index ranges; all field lengths, range totals and bounds match the1900/581/1061 observation counts. Unit/neutral sample counts are265186/320128 (idx870),46065/99646 (774),81461/181741 (294). All3543converted commands select actors present as Self units in their paired observation. Each initial observation contains13Self units,50minerals and a CommandCenter with empty orders; its paired first command is ability524/TrainSCV at the exact human issue loop12,21or15. This corroborates pre-command state for those first decisions, not every later command. Receipts: `unit-block-audit-{294,774,870}.json`, `historical-unit-source-bindings.json`; bounded local probe consumed no game CPU or optimizer.

Enemy visibility enums include visible and snapshot units, plus8Hidden samples in idx870. Hidden/snapshot dynamic fields cannot be admitted as current observations. Cross-checking128x128 visibility pixels with full map coordinate scaling improves after y inversion, but some visible units still map to hidden pixels. A square maximum-dimension scaling candidate performs worse. The correct native feature-minimap transform (including playable rectangle, pixel-center/radius effects and padding) is not yet established; neither candidate is a verified importer transform. Retain both diagnostic outputs rather than treating disagreement as proof of fog leakage or proof of safety.

Independent selection-event reconstruction uses original SCmdEvents, SelectionDelta and ordinary control-group events. The [upstream SelectionTracker source](https://github.com/ggtracker/sc2reader/blob/upstream/sc2reader/engine/plugins/selection.py) supplies reference semantics, but its OneIndices branch does not use its mask data and its ordinary group handlers do not establish steal behavior; do not copy these blind spots into training. The bounded audit invalidates such states until a clear reset. Of2181target/loop-matched commands,1382have reconstructed known selection,1039have all converted actor tags within that human selection and905exactly equal it. The remaining343known-selection disagreements and799unknown selections are unresolved, not valid actor labels. Mixed-subgroup dispatch and ordering require stronger checks. Receipt: `professional-selection-audit.json`, reference hashes in `selection-reference-bindings.json`. No imported professional example or model fit is promoted; training eligibility remains false. Next resolve map transform and selection/ability semantics, then implement a source-bound importer with explicit missing-field masks and meaningful fixtures.

### Corrected selection masks and exact replay maps

The previous selection totals are superseded by a verified decoder correction. Official s2protocol `_bitarray` returns `(length, packed integer)`, not a Boolean list. Its big-endian read groups bits across byte boundaries; simply iterating the pair or shifting the returned integer is not equivalent to SC2 selection-mask ordering. Installed sc2reader1.8.0 already parses the wire masks into Boolean arrays; the revised probe pairs every selection/control-group event by original frame, group and mode, and uses those arrays. Its generic SelectionTracker is not used: the audit implements OneIndices removal rather than the reference plugin's ineffective branch and handles steal-set/add with subsequent recorded automatic cleanup events. Of696mask events,280normalized packed masks differ from naive integer shifting. Source/probe bindings are saved; no installed package was modified or added.

Final source-bound selection audit03: all641matched Future/BackupI commands and386Harstem commands select actors within the independently reconstructed human selection. Scarlett has1007corroborated,39known-selection disagreements and108unknown selections among1154matches. Total2034/2181actor-membership corroborations,1377exact whole-UI-selection matches. Exact UI equality is not required for commands dispatched to capable units within mixed selections, but unsupported/disagreeing groups remain excluded. Earlier masks/ordering candidates are diagnostic failures, not training labels. Receipt `professional-selection-audit-03.json`; bounded helper `selection_probe.py`, bindings `reconciliation-code-bindings-03.json` and installed-reader bindings02.

Independent replay data-pack ability names were compared with the previously extracted native75689 ability catalog. Of2181matched commands,1708names agree (including explicit RightClick/Smart equivalence),1699also match link index. Unknown aliases are not automatically accepted. This corroborates many ability labels but does not establish the complete76052catalog or every command mode. Receipt `independent-ability-name-audit.json` binds the native catalog and installed parser version.

Two converted map headers are wrong: idx294reports192x168for DiscoBloodbath; idx870reports200x184for Acropolis. The exact original maps were retrieved from Blizzard's current map depot using each replay's last map cache handle, bounded to existing16MiB probe contract. Acropolis1059342bytes SHA256 `30770d8ce03908498e085a7e8ccb6c2b09d0379fc06d5a2921b353689c19a0e9`; Disco836797bytes SHA256 `fedc709fae1bbc0904c8b97f1f58efd8ab65636d4e6afd13e8b6e94e3219aca2`. Hashes match the original replay cache handles exactly. Installed MapInfo parser independently confirms176x184and200x184. Local preexisting maps had different hashes and were only provisional geometry evidence. Receipts `exact-map-retrieval.json`, `exact-disco-map-retrieval.json`; maximum conservative total reservation16,057,271bytes below16,777,216cap. No legacy-client asset prefix or large archive download occurred.

PySC2's primary transform source flips y in world coordinates before uniform scaling by the largest map dimension, then floors to pixels. Combining that transform with exact original map dimensions places4035/4266,5661/6358and35026/38281Visible enemy samples on Visible center pixels (idx294/774/870). Snapshot/Hidden values remain distinct. Pixel-center visibility is not equivalent to full unit footprint visibility, so residual disagreements require footprint/native feature checks; do not infer global fog disabling or admit hidden dynamic fields. Full unit-block receipts03 now bind exact map bytes/dimensions. Next implement a bounded professional importer using exact-map geometry, verified command details and explicit unknown-field masks, recover player-owned upgrades from replay events, and test native compatibility before fitting. RL remains stopped; professional training-eligible corpus remains0 until those checks pass.

### Tested production tournament wire decoder

`src/learning/tournament_record.py` now decodes the bound May2024 Windows Action record schema without executing converter source or installing dependencies. It reads scalar observations,128x128byte/MSB-packed grids, raw converted actions, flattened unit/neutral field arrays and their observation ranges. Numeric arrays use bounded memory views where possible. Queue/autocast fields remain absent, point targets remain integer-valued, snapshot/hidden visibility remains explicit, and header map dimensions remain the original encoded values for later exact-map reconciliation. This module is not a native demonstration importer and does not grant training eligibility.

Five independent wire-fixture tests cover uint64tags, structured orders, positions, packed image bit order and absent command details; malformed scalar/unit lengths, unknown targets, truncated/trailing records, huge vector counts, invalid observation ranges and zero-length ranges are rejected. Tests were observed failing before implementation. Independent read-only review found that accepting many zero-length unit ranges could amplify allocations; a dedicated fixture reproduced the issue, then passed after rejecting such ranges before expansion. The reviewer rechecked the fix and reported no remaining concrete issues in scope.

Final decoder verification02 reproduces all3543commands exactly across the three real source-bound records, with expected unit/neutral sample counts and preserved visibility. Combined final decode/comparison time0.221seconds, CPU-only. Receipt `logs/roadmap/pro-preconverted-probe-01/production-decoder-verification-02.json` binds code, tests, records and full-suite log. Full252tests pass10.052seconds (`logs/roadmap/unittest-tournament-decoder-02.log`); focused5tests, Ruff and diff checks pass. Earlier receipt01 uses pre-review code and is superseded.

An additional original tracker-event probe recovers14player1completed upgrades by exact native catalog name (Stimpack, ShieldWall, weapons/armor and other Terran research). All opponent tracker upgrades are excluded. Unmatched own event names are GameHeartActive, RewardDanceMule and SprayTerran; these are not guessed into native upgrade IDs. Receipt `own-upgrade-recovery-audit-01.json`. An importer must gate each completed upgrade by observation loop, retain unresolved names explicitly, restore only corroborated human command details and use verified original-map geometry. Professional imported/training-eligible games remain0; no optimizer, native match, RL or promotion ran in this decoder work. The full Terran roadmap remains active.

### Native fog projection for partial professional observations

`src/learning/tournament_observation.py` projects decoded fields through the same `PlayerView` used in native play. Visible entities retain known fields; snapshots/hidden units never supply health, energy, orders or other dynamic state, and blips retain contact positions only. Exact original map dimensions are caller-supplied,128x128grids remain labeled feature-minimap data with their world transform, and native grid precision is not fabricated. Player food_used/idle/army counts, missing world effects/radar sweeps/death events/history, truncated orders/buffs and other unavailable unit fields remain explicit in `unknown_fields`. Caller-omitted upgrades are unknown; importer-provided completed own upgrade IDs remain known. `state_inputs` now rejects partial states until an explicit missing-field encoder exists, preventing silent zero filling in the current learner. Existing complete native inputs are unchanged.

Independent review exposed a genuine upstream field bug: both current and bound historical17da `observer_utils.cpp` assign `dst.energy = src->energy_max`. All13255energy-capable samples across these records equal capacity. The historical implementation is now cached and hash-bound (`historical-observer-implementation-binding.json`); current energy is omitted and declared unknown, while verified capacity is retained. A regression fixture failed before the correction and passes after it. Hidden nonfinite dynamic fields are not read or validated, ensuring invisible values cannot change projection behavior. Reviewer rechecked the fix and reported no remaining concrete issues in scope.

Final projection verification02 processes all3542observations across the three records,476061visible unit rows (102468/59279/314314respectively). Every returned entity is Visible/non-blip; enemy memory contains identity/position/last-seen only; current energy is absent; missing player fields stay absent and all upgrades are gated by original completion loop. Runtime28.80seconds CPU-only, no native simulation or optimizer. Receipt `logs/roadmap/pro-preconverted-probe-01/partial-observation-verification-02.json` binds adapter, native fog filter, encoder guard, upgrade source and verifier. Receipt01 predates the energy correction and is superseded. Focused4tests and full256tests pass9.945seconds (`logs/roadmap/unittest-tournament-observation-02.log`); Ruff/diff checks pass. Still no professional dataset is training-eligible: command/ability/selection reconciliation, original-map resampling, chronology/death handling and missing-field model inputs must be completed before fitting. RL remains stopped and the full roadmap remains active.

### Missing-field inputs for professional imitation

Added opt-in `state_inputs(..., missing_fields=True)`: numeric entity and scene
inputs carry matching availability bits. Missing player values, unknown current
energy, resource contents, remembered unit dynamics, truncated order counts and
imprecise order coordinates are zeroed and marked unavailable. Unknown command
history cannot supply actor/target references. Default inputs retain the original
94 entity features and scene dimensions; the opt-in format uses188 entity
features and doubles the scene width. This is preparation for human imitation,
not a fitted policy or resumed RL.

The new format still needs checkpoint/trainer/native-agent configuration and
correct handling of coarse source grids before professional examples can be
promoted into training. Command reconciliation and competent imitation remain
open. Full260tests pass (`logs/roadmap/unittest-missing-fields-01.log`). The bounded
real-record check and code hashes are in
`logs/roadmap/pro-preconverted-probe-01/missing-input-verification-01.json`.

### Missing-field checkpoint and spatial inference compatibility

The trainer now exposes `--missing-fields` and records the input format in both
its experiment configuration and checkpoint. Native inference automatically uses
the checkpoint's format and still validates the full unit/ability/upgrade
vocabularies. Checkpoints without the flag retain legacy behavior. Masked policy
dimensions are checked before use.

With both spatial and missing-field inputs enabled, map patches add ten source
resolution values (world units per pixel for each plane) and five availability
bits, for401point features. Feature minimaps are sampled at world-tile centers
using the verified world-y flip and uniform scale; native grids preserve their
original values. Absent/unverified planes are explicitly unavailable and their
bytes are not read. This permits partial replay sensory information without
representing missing terrain as observed flat terrain.

Verification:270tests pass, including native-agent/trainer input parity,
checkpoint round trips, legacy checkpoints, source-grid transforms and unavailable
planes (`logs/roadmap/unittest-missing-runtime-geometry-01.log`). A separate probe
projected all observations and checked36sampled professional states through
spatial inputs, saved/reloaded random policies and raw command serialization
(`logs/roadmap/pro-preconverted-probe-01/missing-runtime-verification-01.json`).
No optimizer, gameplay episode or RL ran. These records remain ineligible for
training pending command reconciliation. Height-map source audit confirms the two
Disco games have identical height pixels despite different header dimensions;
the observer copies height from the first feature observation separately from
GetGameInfo. Independent comparison to the original map remains open, and this
probe marks height unavailable.

Independent read-only review found no other concrete checkpoint/native/geometry
issue and reproduced the remaining partial-source history boundary: enabling
`--missing-fields` does not make incomplete command history trustworthy. A second
partial demonstration row is rejected once teacher reconstruction adds history
that the source still declares unknown. A regression assertion now preserves
that rejection. The professional importer must explicitly reconcile history
quality before those rows become eligible; silently removing this guard would
fabricate complete history. This is still an open importer requirement.

### Professional command identity reconciliation

Added `src/learning/tournament_commands.py`, which requires same loop and target,
independent ability name/index agreement, original human selection membership,
supported regular command flags and mutual one-to-one correspondence. Accepted
labels retain full native actor/target tags, original queue flags and precise
original target points. Unmapped names, unknown selections, unsupported flags and
ambiguous repeats remain explicit exclusions; they cannot silently become labels.
Unknown events also reserve possible converted identities, preventing another
event from claiming an action they might own.

The real three-game probe verified1482commands:467Future/BackupI,292Harstem,
723Scarlett;747original commands remain excluded. The final bound receipt is
`logs/roadmap/pro-preconverted-probe-01/command-reconciliation-03.json`. Receipt01
predates mixed-ambiguity fixes and is superseded; probe02 computed the same counts
but failed during source-binding serialization and produced no receipt. All277
unit tests pass (`logs/roadmap/unittest-tournament-commands-02.log`), and an
independent read-only review confirmed both ambiguity fixes.

Chronology probe:159worker-training commands across the three games; none
introduced a new training order at the command loop when the preceding recorded
building state was idle.61had empty orders both before and at that loop. Later
observations commonly showed the training order and resource deduction. This is
supporting evidence, not yet proof for every command/observation pair. Bound
artifacts: `command-state-timing-audit-01.json` and
`command-state-timing-bindings-01.json` in the same probe directory. Blizzard's
[protocol](https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/sc2api.proto)
provides executed-loop timestamps on observed actions; the preconverted database
omits them. No fabricated loop shift has been introduced.

Some installed historical replay ability names are incompatible with current
native catalog names (including clearly unrelated names on later abilities).
Those mismatches are excluded. Exact version-specific mapping, full chronology,
causal partial-history handling and the actual professional demonstration importer
remain open. No optimizer, native match, fitting or RL ran in this stage.

### Issue-loop observation timing contract

A bounded installed-client replay probe recovered301consecutive observations from
an existing teaching game (51574/Mez; reserved games untouched). All five observed raw actions through loop300were echoed one loop after their
issue timestamp. Four match original human commands; the fifth is an engine
echo without a matching original SCmdEvent. At loop23the CommandCenter was idle with50minerals;
loop24echoed TrainSCV(issue23), showed the order and0minerals. The second train
command at249similarly added its queued order in observation250.

The cached historical `ActionConverter::OnStep` explains the professional rows:
it copies newly received actions into the preceding observation buffer, locks
that row, then copies the current observation into a new buffer. Thus a stored
observation at original issue loopL is a pre-effect state; it is not a fabricated
L-1 timestamp. Source logic, native phase and the159professional worker-command
checks support an explicit `state_at_issue_loop_before_effect` importer contract.
The previous native extractor deliberately uses the more conservative L-1
format; these two source formats should remain distinguishable.

Bound evidence: `logs/roadmap/pro-preconverted-probe-01/issue-loop-phase-verification-01.json`
and `native-issue-phase-01.json`. The native build is75689, not the professional
76052build, and the exact compiled producer revision remains unknown. This
resolves the converter-buffer timing interpretation; it is not a claim that the
professional games were directly reconstructed on the native client.

A fresh bounded official-package index check confirmed the complete4.10Linux
archive lists Base75689only; Base76052is absent. Guessed4.10.1/4.10.2URLs returned
404. Total archive metadata downloaded:3,592,190bytes under a4MiBcap; executable
and asset downloads:0. Full directory/receipt:
`linux-archive-full-directory-01.bin` and `linux-archive-full-index-01.json`.
The earlier512KiBdirectory probe stopped at its cap and was superseded by this
explicit metadata-only contract. No pending legacy asset download executed.

Next importer work: represent verified subsets of human history without claiming
complete history, apply only player-owned causal death/upgrade events, emit source
alignment/provenance receipts, and mask delay labels crossing unresolved commands.
Professional fitting and RL remain stopped.


Professional event-history progress: original SCmdEvents now retain one causal
history slot each. Identity-verified commands preserve their exact details and
original unit-target snapshot position; unreconciled events keep only timestamp
and an explicit unknown marker. Unknown slots mask actor/target references and
command-role values rather than inventing actions. The next-action timing label
is withheld when the immediately following original event is unknown. Source
histories require one demonstration row per original event, including same-loop
events; native complete-history burst behavior remains unchanged. Independent
review identified the grouped-row snapshot problem; a failing regression test
confirmed it and the single-event guard fixes it. Fresh suite:283tests pass;
changed Python files pass Ruff.

Local three-game verification is terminal with no optimizer updates:1482verified
commands retain causal event slots;1421currently have representable labels,
1476rows include unknown history and451timing labels are masked. The61target
exclusions are all Smart unit-target commands.60original target positions each
match exactly one currently visible neutral mineral patch (54type665,6type666),
but the converted neutral tag differs from the original command tag. Cached
converter `source/include/observer.hpp` explains this: `updateResourceObs` replaces
resource tags with their first remembered ID when visibility changes. The last
excluded target is a unit seen11loops earlier. Do not drop harvesting capability
or substitute point commands: reconcile source-normalized mineral identities
with explicit provenance, keeping native tags and fog filtering intact. The
remaining remembered-unit target needs a separate legality/representation check.

Evidence: `logs/roadmap/pro-preconverted-probe-01/target-exclusions-audit-01.json`,
`target-exclusions-history-01.json`, `target-exclusions-position-01.json`, and
`logs/roadmap/unittest-event-history-02.log`. These are local representation
checks, not a training-eligible professional corpus or learned competence. The
actual professional importer, own causal deaths/upgrades, source map inputs,
training eligibility and human imitation fit remain open. RL remains stopped.


Professional demonstration files are now implemented by
`python -m src.learning.tournament_import <job.json>`. The job binds local
record/replay/map/catalog/reconciliation/phase paths, record_index and a new
output directory. Import verifies reconciliation hashes, converted record
SHA256, original replay/catalog identity, native phase proof and exact original
map cache hash. It emits static.json, examples.jsonl.gz (one original event per
row) and dataset.json; original commands remain alongside translated labels.
Outputs remain explicitly training_eligible=false until the trainer supports
and verifies this separate partial source alignment.

Neutral resource labels translate only when the original tracker supplies the
same native resource type, original target ownership is neutral, and exactly
one visible source resource has the exact original target position. Native
commands never use this translation. Prior verified history references are
translated only through mappings established causally. This restores all60
mineral commands (17Future,16Harstem,27Scarlett) without converting them to
point commands or altering actor/queue arguments.

Own deaths and completed upgrades consume only original tracker events strictly
before the decision loop. Actual source evidence shows a command-induced Depot
change logged at965 but observation965 still raised; another autonomous add-on
change at4778 already appears in observation4778. No universal inclusive phase
is claimed. Same-loop previous/new type IDs are used only for vocabulary checks;
features retain the actual observed type. Over311209own type samples match
verified original tracker/native names. Opponent death/upgrade events do not
enter model inputs. Unmapped own upgrades remain causal metadata; known upgrade
ones retain availability1 and uncertain absences availability0. Independent
review found this partial-upgrade boundary and the new red/green test fixes it.

Actual corpus: `logs/roadmap/pro-demonstrations-04/{294,774,870}`. Training reader
checks with spatial/missing inputs produce467/467,292/292,722/723representable
commands respectively. All representable labels round-trip exactly to their
source command, all features are finite, histories remain causal and input/code
bindings verify. The one excluded command is Smart targeting an Infestor seen
11loops earlier; its original identity is sound and present in enemy memory.
Investigate native remembered-target legality before changing the model mask.
Final evidence: pro-preconverted-probe-01/imported-examples-verification-04.json
and unittest-professional-import-02.log (292tests pass). Partial import artifacts
01/02failed safely on type-boundary checks;03predates the upgrade absence fix
and is superseded. No optimizer, professional fitting or RL ran. Next connect
this explicit source alignment/availability contract to trainer eligibility,
form whole-game splits and start bounded human imitation evaluation; retain the
full micro/Hard/higher-difficulty roadmap.


Professional supervised training is now connected to the explicit partial-source
contract. The trainer accepts issue-loop pre-effect rows only with --missing-fields,
requires_missing_fields=true, training_eligible=true, professional teacher kind,
source/producing-code/output hashes, original replay SHA identity and a bound
native/converter phase proof whose supporting bindings also verify. Partial
receipts cannot bypass these gates by claiming the legacy L-1 alignment. Native
complete sources retain their old default behavior. Independent review's two
provenance defects were reproduced with failing tests, then fixed. Full293tests
and changed-file Ruff checks pass.

Fresh `pro-demonstrations-05/{294,774,870}` artifacts were regenerated with the
new eligibility/output bindings. Whole-game split:294Future and870Scarlett teach;
774Harstem is kept out of optimizer updates. No reserved51483/51886games were
opened. `professional-fit-source-validation-01.json` records validated sources.

Actual first professional fit: `logs/roadmap/joint-professional-fit-01/`.
CPU-only, OPENBLAS/OMP2threads, seed8100, hidden32, batch16, rate0.001, refinement,
actor cutoff, spatial+availability inputs,50epochs with600optimizer-wall-second
cap. Terminal training shell handle81483 exits0. The run used1189representable
teaching commands for59450presentations/3750updates;50epochs finish60.35optimizer
seconds and79.14total seconds including collection/audit. One remembered enemy
label remains excluded. Mean loss falls to2.4404. There were no RL updates,
simulated training games or native strength tests.

Verified reconstruction:435/1190complete teaching commands (36.6%),12/292complete
commands on the withheld game (4.1%). Ability1142/1190teaching versus132/292withheld;
exact actors619/1190versus45/292; targets765/1190versus68/292. Complete with timing
206/822known-timing teaching versus2/208withheld. On the withheld first minute,
13/18abilities and10/18exact actor groups match; first SCV commands do reconstruct
correctly, while worker targets/build locations already diverge. Mean predicted
point error is7.39tiles teaching and67.51withheld. This is failed generalization,
not competent imitation or readiness for RL. Harstem is now a reused diagnostic,
not a future untouched acceptance set.

Bindings and checkpoint SHA are reverified after terminal completion in
`logs/roadmap/joint-professional-fit-verification-01.json`; source/config/code
and evaluated checkpoint remain unchanged. Report's oracle actor/ability metrics
are diagnostics only. No professional checkpoint replaces the retained native
baseline or earns a strength claim. Next improve teaching coverage and spatial/
actor generalization, including native/professional input coverage, using bounded
human-only fits; retain RL hold and the full micro/Hard/higher-difficulty goals.

Two further supervised comparisons completed without RL or native games.
`joint-professional-fit-02` combined the eleven existing native human teaching
files with the two professional teaching games. The same fifty epochs now meant
268900 presentations and16850updates, rather than equal training compute.
Terminal handle44714 exited0 in310.95total seconds. Complete teaching copying
was460/5380(8.55%); Harstem diagnostic copying was9/292(3.08%). Adding this
particular mixed-source teaching corpus did not improve diagnostic copying.
It is a failed candidate, not a reason to start RL.

An optional `--role-pooling` encoder now keeps separate summaries for observed
owned units, observed enemies, observed neutrals and remaining remembered/other
entities. Each summary has its own mean learned embedding and log count. This
prevents neutral patches from directly diluting the owned-unit mean, without
removing actions or adding observations. Checkpoints preserve this mode;
default initialization, forward outputs and gradients reproduce the previous
encoder bitwise in independent review. Five focused tests cover role/count
behavior, finite-difference gradients, permutation/checkpoint behavior, empty
groups and float32 preservation. Full298tests pass, with changed-file Ruff clean.

`joint-professional-fit-03` used this mode on the same two professional teaching
games and Harstem diagnostic, with the fit01 fifty-epoch controls. Terminal
handle74574 exited0:1189usable teaching commands,3750updates,62.42optimizer
seconds,81.35total seconds. Complete teaching copying improved to487/1190(40.9%),
but diagnostic copying was11/292(3.77%), compared with12/292before. Diagnostic
point error remained61.79tiles, or55.23tiles with true ability/actors supplied
as an oracle. The new architecture changes random initialization as well as
pooling; this single comparison is not a causal attribution or strength result.
No checkpoint is promoted. Source/code/checkpoint bindings and saved mode verify
in `joint-professional-fit-verification-03.json`.

The actor diagnostic `joint-professional-actor-roles-01.json` also finds incorrect
unit types and counts, not merely alternative interchangeable worker tags:
fit01 matches exact actor-type counts on15/51townhall-only,17/66worker-only and
22/175other diagnostic commands. Repeated poor new-game copying calls for a
focused architecture/data diagnosis before another fit. Astra consultation is
within the user's explicit conditional authorization. Harstem remains a reused
diagnostic; reserved51483/51886 remain untouched. Human imitation must establish
competent play before RL resumes. Micro transfer, reliable all-race Hard wins
and higher-difficulty evaluation remain open.

Astra's focused diagnosis finds no concrete gradient defect, but a missing
explicit candidate-to-selected-actor relation and severe two-game data scarcity.
283/292diagnostic commands use abilities already present in teaching; novelty
alone cannot explain the failures. An opt-in --actor-relative-points residual
now learns from dx/dy and squared displacements from the selected group centroid,
scaled by32world tiles. Every map candidate remains. The shared argument encoder
receives its loss gradients; ordinary inference supplies its own predicted actors.
It starts at zero without changing RNG draws or initial default scores, and
checkpoints preserve the flag. Five tests cover gradients, translation of the
residual, entity/candidate permutation, zero/default parity, empty candidates and
checkpoint persistence. Full303tests pass; independent review finds no blocker.

One predeclared human-only fit04 completes50epochs/3750updates in84.50seconds.
Terminal source/code/checkpoint validation succeeds. Complete copying459/1190
teaching and11/292diagnostic fails the required24diagnostic matches. Scoring the
point head on every gold point command, including mode mistakes, finds a useful
limited mechanism: true-ability/actor mean error56.13to33.64tiles(40.1%lower),
p95126.17to116.50,within-two-tiles1to4. Ordinary mean worsens68.13to72.13;
wrong actor/ability choices still dominate. The overall gate fails; this model
is not promoted and RL stays stopped. Next acquire a bounded, more diverse
professional teaching corpus instead of continuing architecture/optimizer sweeps.
The optional residual remains available for future frozen comparisons.
See `superpowers/plans/2026-10-06-actor-relative-points.md` for thresholds and
receipts. No native match, reserved-game evaluation or large download occurred.

Professional data expansion now uses a separate32MiB exact-range transfer cap.
Nine originals/candidate records cost12,759,289reserved bytes, without full
archives, installers, GPU or large asset downloads. Existing map cache hashes
match exact local Acropolis/Disco files. Eight candidates match all13initial Self
native types and ownership;910has zero matching types and17identity failures,
so is excluded. Reconciliation recovers4180/5777issued commands for8games, preserving
unsupported events as unknown history. Teaching candidates955,887,839,991,920,851,
523add3323decisions from HeRoMaRinE,uThermal,TIME,SpeCial and BackupI/Future.
HeRoMaRinE848is reserved for later frozen evaluation, not optimizer/model input.
Current Harstem774diagnostic and reserved51483/51886 retain their roles.

This expansion exposed a real importer assumption: player1need not be replay
user0, because tournament observers occupy lobby user slots. The importer now
resolves details workingSetSlotId through the unique assigned initData lobby slot,
requires reconciliation player/user agreement, filters commands by resolved user,
and tracks ownership/upgrades for the actual player. Known foreign-only Self tags
reject; unknown ownership stays unknown; exact same-loop owner alternatives permit
the documented phase uncertainty without injecting tracker boundary data into
observations. Independent review found the ownership gap; reproduced failing tests
cover it and the same-loop-only case. Full309tests pass, Ruff clean. Actual legacy
294reimport07 preserves all467example rows/labels exactly with verified bindings.
Actual955imports681commands forplayer2/user3with160730own-type checks. Remaining
corpus07imports are sequential and their terminal/source validation is the next
gate. No new professional fitting, model predictions, native matches or RL ran.
See superpowers/plans/2026-10-06-professional-corpus-expansion.md and
logs/roadmap/pro-corpus-expansion-01/ for exact receipts. Full roadmap remains open.

The remaining imports are now terminal and source-validated: corpus07contains
9teaching games/4513commands, reused diagnostic774/292commands and reserved848/
857commands, with1,202,029own-type checks. Whole-replay SHA splits are disjoint;
producing-code/input/output/phase bindings verify. Verification receipt:
pro-corpus-expansion-01/corpus-verification-07.json. Original051history is retained;
07regenerates the existing Clem sources under the new importer. Next one fixed
human-only fit05uses unchanged fit04architecture/seed/batch/rate,50epochs,
600optimizer seconds andCPU2threads. Larger data also means more presentations;
this is not equal-compute attribution. No new reserved-game predictions or RL.

Human-only fit05 is terminal: 50 epochs, 14,100 updates, 225,500 command
presentations, 233.56 optimizer seconds and 288.60 total seconds. Teaching
complete-command matches are 825/4513 (18.28%); reused Harstem diagnostic matches
are 6/292 (2.05%), below the predeclared 24/292 progress gate. Ability prediction
alone reaches 149/292, but actor matches are 53/292 and target matches 62/292.
Actor errors include wrong unit types/counts, not just interchangeable worker
tags. All-gold point-head diagnostic mean error is 60.80 tiles ordinarily and
34.88 with true ability/actors; neither gets a target within two tiles. No
competence or promotion is established. Receipt:
`logs/roadmap/joint-professional-fit-verification-05.json`. RL stays stopped;
human imitation is the current learning phase. A frozen gameplay test would
measure inference without optimizer updates, not start RL.

A teaching-only numeric-input audit finds 6/188 entity, 566/618 scene and 1/9
history-role columns always zero. Their corresponding weight rows receive no
data gradient and retain random initialization. Five previously recorded native
frames each activate 284 never-taught scene columns; clearing those rows changes
the internal context, including one predicted ability. This establishes an
unlearned-input influence, not improved play. It does not explain the poor
professional diagnostic results, whose inputs share the teaching representation.

`JointEntityEncoder.clear_unseen_inputs` explicitly zeros only those numeric
weight rows using teaching support. No input, command or roster is removed;
future nonzero inputs still receive gradients. Defaults remain unchanged. A
separate frozen derivative is saved at
`logs/roadmap/joint-professional-fit-05-supported/policy.npz`, SHA256
`ee78b58788436c527f19544a09f513fb8f79723edc64b864d5e1eb2a2fa38482`.
The bound `verification.json` confirms all 4513 teaching commands' exact encoder
output parity, unchanged supported parameters, save/load parity and unchanged
parent checkpoint. The helper recomputes support using only the nine teaching
games and verifies their source hashes. No optimizer, diagnostic/reserved data,
native match or RL is used to derive it. This correction covers numeric rows;
unused categorical embeddings are not changed. Three focused tests and the full
312-test suite pass; Ruff is clean. Independent review finds no blocker.

Next diagnose the remaining imitation errors before another fit or promotion.
Reserved professional 848 and original 51483/51886 remain excluded from model
predictions and optimizer input. Learned micro transfer, reliable all-race Hard
wins and higher-difficulty evaluation remain unproved. The full goal remains
active.

Read-only bottleneck audit `professional-encoder-saturation-01.json` uses fit05's
teaching sources and reused diagnostic only. It compares the trained encoder
with its same-seed initialization, without another fit. Mean fraction of context
coordinates with absolute value above 0.95 increases from 0.19% to 70.72% on
teaching rows, and from 0.26% to 68.87% on diagnostic rows. Mean history contribution
norm increases from 1.89 to 17.88 on teaching; scene from 0.91 to 5.72 and pool
from 2.45 to 10.51. Entity saturation remains about 10%. This supports examining
the context bottleneck; it does not prove saturation causes the learning failure
or that normalization improves copying. A focused follow-up consultation with
the previously authorized Astra advisor is pending. Do not infer an approved
experiment, competent imitation or RL readiness from this measurement.

The authorized advisor recommended one fixed context normalization comparison;
plan `superpowers/plans/2026-10-06-context-normalization.md` is now executed.
Optional fixed LayerNorm before context tanh has correct derivatives through
all branches, no new parameters/initialization draws, absent/false checkpoint
compatibility and a bound CLI flag. Five tests observed failing then passing;
full317tests pass. Independent review exhaustively checks role-pooling and
nearly constant context derivatives plus actual old checkpoint parity. No blocker.

Fit06 completes the matched50epochs/14100updates in239.69optimizer seconds,
294.95total seconds, with the exact same source hashes and configuration except
normalization. Checkpoint SHA256:
`9f53942db2c9905dc7a6c5a0b4625e547e3a4a00906fbc6c612a1d0548a6e92e`.
Complete copying825to879/4513teaching and6to14/292diagnostic remains weak.
Diagnostic ability153/292,actors68/292,target66/292. Frozen total teaching loss
4.26069to3.93665 (7.61%lower), with actor/target/offset loss improvements but
slightly worse ability loss. Only6of9teaching games improve complete copying.
Loss reduction, teaching completeness, per-game coverage and diagnostic
completeness gates fail. Receipt `professional-context-comparison-01.json`
verifies terminal/code/source/checkpoint/matched configuration and update count.
No promotion, native game, reserved prediction or RL. No extension/sweep follows.
Context saturation falls70.72%to6.56%teaching and68.87%to6.54%diagnostic; this
mechanical improvement establishes no competence. Geometry still has zero
ordinary point targets within two tiles among158gold point commands.

The initial loss-comparison helper omitted construction_products supplied by the
trainer; the verifier caught per-game totals disagreeing with terminal reports.
Those helper01loss/per-game receipts are explicitly invalidated in
`professional-context-loss-audit-01-invalid.json`. Corrected helper02 uses
`entity_train.collect` directly. Every representable command's component sum
matches loss_and_gradients; every aggregated teaching field matches each
terminal report exactly. Relative/absolute binding-key spelling is canonicalized
to absolute paths, while source hashes and ordering remain required to match.
The training runs themselves were never changed or repeated.

Earlier independent point-head helper01 and actor-role helper05 also omitted
construction products. Their auxiliary metrics are superseded, not production
trainer metrics. Corrected geometry receipt
`professional-point-heads-corrected-02.json` binds each checkpoint's own sources
and uses collect. Fit03-to04 oracle mean55.945to33.635tiles still supports the
limited relative-geometry mechanism (39.88%reduction); ordinary67.708to71.405
worsens. Fit05ordinary60.197/oracle34.725tiles; fit06ordinary58.025/oracle32.120,
oracle within-two-tiles0to5. None supports promotion. Use these corrected values
instead of earlier auxiliary point summaries. The construction-feature support
and saturation audits already supplied construction products and remain valid.
The full human-imitation/micro/full-game/Hard/higher-difficulty roadmap is open.

The next diagnostic uses the exact trainer.collect inputs and groups every
representable command by native ability, including explicit ability/actor and
gold-cell oracles. Receipt `professional-command-failures-01.json` binds fit06,
configuration and helper. Teaching Smart2103+Attack1232/4510 (73.95%) dominate.
Diagnostic ability choices miss all11SupplyDepots,4Barracks and12Marine production
commands, despite105/26/233teaching examples respectively. Correct-ability actor
type/count matches improve for construction, but exact worker choice and target
generalization remain weak. SupplyDepot correct-cell offset mean0.78tiles teaching
versus3.32diagnostic. This is evidence of several failures, not just action rarity.

[TStarBot-X section4.4](https://arxiv.org/pdf/2011.13729) reports improvements from
ability importance weighting: reduced Smart contribution and bounded increases
for seldom demonstrated abilities. It also preprocesses context-dependent Smart
semantics and uses recurrent trajectory sampling. Our bounded adaptation preserves
the raw native command labels and independent causal32-command histories; it does
not reproduce that full method or guarantee its Zerg results. No source download.

Plan `superpowers/plans/2026-10-06-ability-importance.md` adds optional full-command
loss/gradient weights using only representable teaching examples. Smart rawweight
0.25; other max(1,teaching_replays/count), capped10before globalmean1. All commands,
labels, action vocabulary, shuffle order and unweighted defaults remain. CLI and
configuration bind rule/counts/weights before fitting. Four focused tests first
fail then pass. Independent review catches a vocabulary/count variable overwrite;
a real tiny-dataset main-path test reproduces the zero-row embedding failure,
then passes after renaming the counter. Full322tests pass, Ruff/diff checks clean.
Review finds no other blocker or minor. No re-review is needed for the reproduced
fix. Next one fixed fit07 uses fit05architecture (context normalization false),
same nine teachers/774 and50epochs/14100updates/600optimizer-second cap. Macro
and micro guardrail gates are frozen before fitting. No reserved/native/RL work.

Fit07 is terminal: 50 epochs, 14,100 updates, 331.97 optimizer seconds and
387.11 total seconds. Complete copying rises from 825 to 892/4,513 teaching
commands and 6 to 11/292 diagnostic commands, below the required 24. Diagnostic
ability choice is 130/292, macro choice 13/91 and Smart/Attack 117/198. Supply
Depot choice improves to 2/11 but correct actors and targets remain zero;
Barracks is 0/4 and Marine production 0/12. Five of six frozen gates fail.
Natural-frequency teaching loss worsens from 4.260686 to 4.750104; weighting
changes the objective, so its training loss cannot be compared directly.

`professional-importance-comparison-01.json` binds the checkpoint, matched
configuration, source/code hashes, exact updates, weight counts and per-ability
audits. Its diagnostic field sums reproduce the trainer report. The separate
`professional-importance-loss-01.json` uses exact trainer.collect inputs; every
component sum matches loss_and_gradients and teaching totals match the report.
No model is promoted. This bounded experiment ends without a sweep or extension.
The user's clarification is explicit: current training is human imitation;
RL remains stopped until useful human copying and live competence are proved.

Next diagnostic is `superpowers/plans/2026-10-06-human-small-set-check.md`:
can the unchanged architecture learn a small, varied set of human teaching
commands? At most two commands per demonstrated ability, chosen deterministically
from the nine teachers, receive one fresh 200-epoch / 120-optimizer-second run.
Source/code and selected row indices are bound before fitting. This separates
basic fitting limitations from cross-game generalization; passing would only
prove memorization. It changes no gameplay controls and introduces no scripted
strategy, diagnostic/reserved predictions, native games or RL. The full roadmap,
learned micro transfer and reliable all-race Hard/higher difficulties remain open.

The small-set diagnostic is terminal: 62 selected commands cover all 33 teaching
abilities; 200 epochs / 800 Adam updates take 11.98 optimizer seconds. Ability,
mode and queue are 62/62; timing is 43/43 known labels; targets are 59/62 and
actors 46/62. Complete copying is 44/62, below the frozen 56 threshold. With
human actors supplied explicitly, complete copying reaches 59/62. All 23 point
commands have ordinary mean target error 0.084 tiles. The model can fit small-set
command choices and geometry; unit membership remains a major fitting failure.
This diagnoses training behavior and establishes no cross-game competence.
Contract, selected row indices, code/source hashes, saved policy and terminal
report are in `logs/roadmap/professional-small-set-01/`. Bindings are unchanged.
Next a read-only audit separates membership threshold errors from actor ranking
using human group size only as a named diagnostic oracle. No fit extension or
promotion follows; RL and native simulations remain stopped.

Frozen small-set actor diagnosis narrows the interpretation: correct group size
and type/count composition are both 59/62, while exact tags are 46/62. Supplying
human group size to top-K ranking reaches only 47/62. All 16 failures have one
human actor; 13 select another same-type single actor, including 11 construction
SCVs. Three select multiple same-type production/research buildings. Improving
count alone would barely help. An alternate SCV is not automatically a failed
gameplay decision; the next actor investigation must distinguish functional
execution/travel/order constraints from exact human unit identity. Exact copying
gates remain unchanged and failed. No equivalence or live competence is claimed.
Receipt `professional-small-set-01/actor-diagnosis.json` binds exact selected
teaching rows and reproduces the terminal actor total. No extra fit or other
replay predictions occurred. Current full-game ability generalization also
remains poor (fit07 130/292); neither small-set success nor a possible equivalent
worker selection establishes readiness for RL.

Frozen selected-state context audit shows 7 of 11 construction substitutions
are over two Euclidean tiles farther from the human target; several differences
exceed 20 tiles. One is over two tiles closer. Six of 13 same-type single-actor
substitutions have different first orders. Observed positions and first orders
are available, but original-engine ability availability is not, so neither
equivalence nor illegality is established. The audit reconstructs exact trainer
inputs and matches all terminal integer fields. Its initial full-dict equality
stopped on point means differing by 1.39e-17 due to row reduction order; only
mean comparisons now allow 1e-10 tolerance. No training/data change or receipt
was produced by the failed helper. Evidence: `professional-small-set-01/actor-context.json`.

Plan `superpowers/plans/2026-10-06-actor-geometry.md` implements an opt-in learned
actor score residual from relative dx/dy and squared displacements, scaled by
32 world tiles around the eligible-actor centroid. It uses ability-conditioned
context and player-known positions; no human target/actor is supplied at ordinary
inference and no closest-worker rule is imposed. Zero-initialized coefficients
preserve default parameters/scores/RNG draws. Save/load and trainer flags are
bound. Four tests first fail then pass; an added interior-unit ranking check
brings five focused tests. Full 327 tests pass in 10.06 seconds, Ruff/diff checks
pass, and independent review finds no Critical, Important or Minor findings.
No learning outcome or promotion is established by these code checks.

The fixed actor-geometry small-set run completes200epochs/800updates in12.17
optimizer seconds. Initial predictions exactly match the baseline and all62
selected rows/source bindings match. Exact actors improve46→52, complete
commands44→51, targets59→60; all62abilities/modes/queues and43known timing labels
remain correct. Complete and actor gates fail the56threshold; ability and target
gates pass. Checkpoint, source/code hashes, terminal status and exact update
schedule verify. Frozen actor diagnosis reports60/62correct count/type groups
and54/62exact with human count supplied. Eight remaining failures choose another
single SCV; two select multiple same-type production/research buildings. This is
a bounded fitting improvement, not cross-game competence. No extension, sweep,
cross-game fit, native game, reserved prediction, promotion or RL follows.
Artifacts: `professional-small-set-actor-geometry-01/{contract,report,actor-diagnosis}.json`.

A narrow read-only runtime inventory finds installed PyTorch2.13.0+cu130 in
`/home/sam/repos/hobby-repos/exoplanet/.venv`. A CPU tensor/backward smoke verifies
two threads and no CUDA initialization with CUDA_VISIBLE_DEVICES empty. Receipt
`installed-torch-cpu-probe-01.json` records its module/version. This offers a
possible CPU framework for richer learned unit relationships without downloading
or installing a package. It is not a declared SC2 dependency or implemented new
model; any prototype must explicitly bind its runtime and preserve NumPy/native
interfaces. Human imitation remains the only active learning stage.

[SCC section4](https://proceedings.mlr.press/v139/wang21v/wang21v.pdf) motivates
learned relationships among units rather than independent encodings followed
only by averages. A bounded adaptation now adds an optional CPU-autograd encoder
with one residual self-attention block; it is not SCC's grouped architecture or
data-scale reproduction. The existing heads, broad raw controls, causal inputs,
spatial sensing and NumPy Adam stay in use. Query/key/value projections and a
learned squared world-distance coefficient form attention; output projection and
distance coefficient start at zero. Ordinary decisions receive no human targets
or actors. Last-seen memory remains last-seen, with no hidden-state augmentation.

`entity_torch_encoder.py` retains the parameter/forward/backward interface while
using CPU autograd. Default NumPy and legacy checkpoints remain available. The
opt-in CLI binds backend/version/two threads and the new source; save/load binds
backend and relational flag. No framework installation or GPU use occurs.
Initial four tests RED→GREEN, plus complete-command-loss/Adam and real CLI-path
checks: six explicit CPU tests pass in0.80s. Default suite runs333tests in10.06s,
passing with six optional-framework tests skipped; those six pass separately in
the verified CPU environment. Independent review finds no actionable issues and
independently passes four mathematical/parity/checkpoint tests. Ruff/diff clean.

The mixed-environment broad run is not green: its existing test hardcodes a
Python3.11 subprocess, which inherits the temporary Python3.12 site-packages
path and cannot import NumPy's C-extension. A direct interpreter/import probe
reproduces the cause without updates. Temporary environment variables are
command-scoped; no global environment was changed. This neither invalidates
default-suite verification nor proves all tests work in the mixed environment.

Plan `superpowers/plans/2026-10-06-relational-human-encoder.md` freezes a matched
CPU-backend baseline/attention comparison on the exact62selected teaching rows:
same200epochs/800updates and120optimizer-second cap each. Actor geometry stays
disabled to isolate attention. No diagnostic/reserved replay predictions, native
games, promotion or RL. Fitting and then cross-game/live competence still need
evidence; code verification alone establishes no learning improvement.

The relational comparison is terminal: baseline15.78seconds and attention24.17
seconds, each200epochs/800updates. Both initial audits are exactly equal, and
both schedules/code/contract/checkpoint bindings verify. Attention improves
complete commands44→47/62, actors46→47 and targets59→62; abilities/modes/queues
remain62 and all43known timing labels match. Actor/complete56gates fail;
ability/target gates pass. This experiment ends without extension, broader fit,
promotion, native game or RL. Evidence:
`professional-small-set-relational-01/{contract,comparison}.json`, plus each
run's report and policy. The framework baseline reproduces the NumPy field
totals; this is no evidence that using a framework alone improves learning.

Frozen attention actor diagnosis verifies runtime/source/code/checkpoint and
the same62selected teaching rows. It finds47exact,56correct count/type groups,
and52exact when human cardinality is supplied only as a diagnostic oracle.
Fifteen failures remain: nine SCV ranking errors (one also selects extra workers),
one wrong same-type TechLab, five human actors ranked first with extra units
selected. Targets are fitted but selection is unresolved. Exact tag mismatches
alone do not establish that another worker is functionally unusable. Receipt:
`professional-small-set-relational-01/attention/actor-diagnosis.json`.

A second frozen audit checks whether those wrong top choices are indistinguishable
in the actual inputs. All ten wrong-ranking pairs have the same type and first
order, but none have identical numeric features. Seven pairs (six SCVs and one
TechLab) differ only in their two position columns. For these, base embedding
distances are0.00468–0.01536 and relational distances0.0349–0.1310. All ten human
and alternative base embeddings have no coordinates above0.99absolute activation;
this does not support dead/saturated per-unit features as the explanation.
Attention increases distinction without learning the correct ranking. It does
not prove that more attention, extra epochs, or functional equivalence will fix
the errors. These are same-state input comparisons, not hidden information or
execution evidence. Source/code/runtime/checkpoint bindings verify; no updates.
Receipt: `professional-small-set-relational-01/attention/actor-representation.json`.

The user-authorized Astra consultation inspected the actor loss and preserved
a frozen geometry-checkpoint gradient diagnostic on the same62teaching rows.
Parent verification confirms receipt SHA, checkpoint/current-code/source hashes
and evaluated-source hash. Mean actor BCE is0.00942 and ranking loss0.43394;
the eight wrong SCV choices retain ranking losses0.986–2.489. Aggregate mean
shared-encoder actor-gradient norm is0.04025 versus0.11569 for other losses,
with cosine−0.08965. These are raw gradients, not Adam-preconditioned updates;
they do not prove that loss interference causes the failed selection. Singleton
BCE/ranking both teach the human actor, and teacher-forced actor→target is a
valid factorization. No broken-gradient or mathematical-incapacity claim follows.
Receipt: `professional-small-set-actor-geometry-01/astra-gradient-diagnosis.json`.

Next concrete hypothesis is an opt-in nonlinear candidate/context actor-score
residual on the best geometry architecture, with unchanged losses and encoder.
The plan `superpowers/plans/2026-10-06-nonlinear-actor-scoring.md` freezes code
checks and a matched small-set budget/gates. It is proposed, not implemented or
accepted learning improvement. Human imitation remains active; RL is stopped.

Nonlinear scoring is now implemented and independently reviewed: four new tests
RED→GREEN; full default337tests pass in10.02seconds (six optional-framework skips),
Ruff/diff pass. Review finds no actionable issues and checks old checkpoint and
nonlinear-without-geometry compatibility. The optional flag persists through
CLI/config/checkpoints. Default scores and initialization retain exact parity.

The fixed matched run completes200epochs/800updates each, baseline12.95seconds
and nonlinear14.26seconds. Source/code/contract/checkpoint bindings, identical
initial audits and schedules verify. Both give actors52, targets60, complete51,
all62abilities/modes/queues and43known timing labels. The residual lowers last
epoch's mean minibatch loss0.64441→0.57684 but leaves complete and actor totals
unchanged, failing the56gates. Ability/target gates pass. No extension, wider
fit, promotion, native game, diagnostic/reserved prediction or RL follows.

Frozen matched actor audit reproduces52exact,60correct count/type groups and
54exact with human count supplied. It resolves870:437 but newly misses294:462;
eight SCV ranking errors and two extra-building errors remain. Margins are
recorded for every singleton teaching label. This is no demonstrated selection
gain and no reason to resume RL. Artifacts:
`professional-small-set-nonlinear-01/{contract,comparison}.json`, both run
reports/checkpoints and `nonlinear/actor-diagnosis.json`.

A frozen linear separability diagnostic now distinguishes score-family support
from training failure. For each of62teaching rows, an independent diagnostic
query separates human membership from other eligible actors; all solvers finish
optimally, minimum directly verified signed margin0.000925, no opposite-label
feature collisions. More consequentially, one shared score on the frozen
conditioned-context × [entity, geometry, cutoff]features also separates all62.
Its31.03second solver returns optimal with direct margin0.015785843624879448 and
coefficients bounded[-1,1]. Original actor logits reconstruct before probing;
source/code/checkpoint bindings pass. These label-assisted probes are not a
deployed policy, ordinary held-out predictions or strength evidence. No policy
updates/native games/RL. Artifacts:
`professional-actor-separability-01/{contract,report}.json`.

This supports testing selection-head optimization with the representation
frozen, rather than claiming missing information or impossible scoring. Plan
`superpowers/plans/2026-10-06-convex-actor-heads.md` specifies a same-objective,
same-initial-weight Adam/L-BFGS comparison on62human rows, with fixed budgets and
ordinary complete-command gates. It is proposed; no acceptance follows from LP.

The frozen-feature optimizer comparison is now terminal. Independent review
first identified missing per-command/reload evidence, configuration binding,
finite guards and direct cached-logit parity; all were repaired before fitting,
and re-review found no remaining actionable issues. Actual preflight verifies
maximum logit discrepancy4.84e-6, gradient8.08e-8 and finite-difference5.39e-11.

Both treatments reach250iterations: Adam250evaluations/0.58seconds, L-BFGS281
evaluations/0.89seconds. L-BFGS stops at its predeclared iteration limit, not
convergence. Actor objective starts0.443365 and ends0.357067(Adam) versus
0.0179665(L-BFGS). Adam gives actors54/complete53; L-BFGSactors61/complete59.
Both retain targets60 and all62abilities/modes/queues/43known timings. L-BFGS
passes all small-set gates, Adam fails actor/complete. Nine baseline actor errors
are fixed with no newly wrong rows;523:513remains. Selection-weight norm grows
8.39→731.75(max164.05), requiring explicit reporting in wider tests.

Unchanged encoder/non-actor arrays and exact per-row checkpoint reload
predictions verify, together with source/code/configuration/checkpoint hashes.
This supports better head optimization on this finite teaching set; it does not
establish generalization or strength. A fresh wider human-imitation comparison
is permitted; native play/RL remain stopped. Whole-host utilization sample during
the run is4.1%CPU/22.7%memory on32logical CPUs; BLAS uses two threads. No GPU,
downloads, other replay predictions or native games. Artifacts:
`professional-convex-actor-01/{contract,comparison}.json` and both run
reports/checkpoints (all62ordinary predictions and actor margins included).

The successful small-set head fit does not transfer in the fixed wider test.
An optional compact fitter caches contexts/candidate features separately rather
than every outer product. Five focused tests pass; full342tests pass10.30seconds
with six optional-framework skips, Ruff/diff pass. Independent review validates
original/dense/factored gradients and optimizer behavior, including optional
SciPy absence. Default joint training/checkpoint behavior remains unchanged.

The full-corpus wrapper binds fit05/configuration/source/code/cache, exactly
preserves every initial prediction when zero geometry heads are added, and
reproduces baseline aggregate fields. Nine games yield4513commands/4510fitting
rows; reused774has292diagnostic rows. Compact cache117.09MB replaces3.52GBdense
outer products. Review's missing whole-host CPU monitor was addressed before
launch with a hash-bound watchdog; re-review has no remaining findings.

Adam finishes250evaluations/19.25seconds, L-BFGS275evaluations/21.34seconds;
both250iterations, L-BFGSiteration-bound rather than converged. Actor objective
0.636428→0.595732(Adam), →0.586038(L-BFGS). Adam teaching actors1946/complete843,
diagnostic actors47/complete5. L-BFGS teaching actors1965/complete853, diagnostic
actors43/complete5/targets61; baseline1869/825and53/6/62respectively. Abilities
stay3814teaching and149diagnostic, row by row. Seven teaching games improve,
but all teaching-size and diagnostic improvement gates fail. No extension or
promotion. Parameter norm14.54, substantially less extreme than the small-set
731.75, is still no transfer evidence.

Encoder/other heads remain byte-identical; every saved/reloaded ordinary
prediction matches. Final source/configuration/code/checkpoint/cache/telemetry
hashes and terminal exit0 verify. HostCPU peaks15.7%, memory31.0%, childRSS5.58GB;
the watchdog does not need to stop the run. Full147.78second comparison, no
native game, reserved prediction or RL. Artifacts:
`professional-wider-actor-01/{contract,comparison,verification}.json`, cache,
both reports/checkpoints and `professional-wider-actor-01.telemetry.json`.

Frozen-cache read-only diagnosis finds zero exactly identical candidate feature
vectors with opposite actor-membership labels across4510teaching rows. Final
gradient norm0.00213145(max0.00048069) does not establish convergence. Lack of
exact collisions is no proof of shared-query separability or raw observation
adequacy. Thus the next decision must address wider fitting/representation and
transfer, rather than another head-optimizer budget extension. Receipt:
`professional-wider-actor-01/frozen-feature-diagnosis.json`.

## Wider selection support and context diagnosis (October 6)

The independent query audit completes in6.53seconds. Every one of4510teaching
rows admits a bounded linear query that selects its human group:2422singletons
and2088multi-unit groups, all solver statuses optimal. The saved wider model
gets1232singletons and732groups right among these representable rows. This
denominator excludes three target-excluded rows; its1964matches are not the
aggregate1965/4513reported above. Parent recomputation verifies every stored
coefficient and margin; minimum margin2.90447e-6, median4.36422, coefficients
finite with maximum absolute value1. These are separate label-assisted oracle
queries, never deployed or supplied to ordinary inference. They establish
candidate support per example, not a learnable shared mapping or strength.
Evidence: `professional-wider-selection-support-01/{contract,report}.json`
and `coefficients.npz`; contractSHA256
`4fe212b26f4b892c4cf32626ff1fe9b0f7aae77f6004ec1511cc254f9eb62d1a`.

A further read-only audit of the bound cache finds4510unique conditioned
contexts, centered numerical rank32/32 and3.25%ofcoordinates with absolute
value>.99. Nearest same-ability context distance has median1.8014and minimum
0.0002925. There are no exact duplicate contexts. This rules out literal
context collapse in this cache; it does not establish that the encoder retains
all relevant information or that nearby decisions are functionally equivalent.
Receipt: `professional-context-mapping-01.json`, source helper
`audit_professional_context_mapping_01.py`. No extra policy predictions,
parameter updates, native games or RL occur in either audit.

Next test the shared context-to-selection mapping with one small nonlinear
residual, preserving the frozen candidates and zero-initialized baseline
behavior. This differs from the failed per-candidate nonlinear scorer. Keep
the previous wider copying/diagnostic gates; no additional optimizer sweep,
native run or RL follows a failed result.

The opt-in context-query policy is implemented with64hidden units and a
zero-initialized entity/geometry/cutoff query residual. It uses a separate RNG,
preserving the old initial parameters and scores. Ordinary selection takes
only legitimate conditioned context and existing candidate features. Save/load
and the training CLI record the option; the default remains disabled.

Four new policy tests are RED on the absent option, then GREEN for default
parity, shared/head finite differences, permutation/checkpoint behavior and
required geometry/cutoff. A fifth test reproduces the old linear fitter silently
accepting the new family, then verifies explicit rejection (RED→GREEN).
Independent review also checks68gradient coordinates (maximum error2.88e-5)
and a genuine legacy checkpoint missing the option; no remaining findings.
The review's full suite overlapped the guard edit and saw an error-string
case mismatch; the fresh final suite passes347tests in10.02seconds with six
optional-framework skips. Ruff/diff pass. No training/native/RL is launched.
The compact nonlinear objective/fitter and frozen full-corpus wrapper remain
to implement and review before testing copying gains.

The compact context-query fitter now shares the existing bounded optimizer
with the linear fitter, preserving its mean per-command selection loss. It
computes context queries and segmented candidate gradients without dense
context-by-candidate outer products. Three new tests cover policy loss/gradient
parity on unequal group sizes, finite differences, nonzero learned residual,
unchanged other heads, immediate wall stop and invalid-family/vector rejection.
The first two are RED on the absent fitter, then GREEN; focused eight tests
pass and the full350-test suite passes10.00seconds with six optional skips.
Ruff/diff pass. The wrapper reuses the hash-bound117MBteaching cache, reconstructs
it exactly and adds post-fit score parity for every4510fitting rows.
Independent fitting/wrapper review and the actual frozen comparison are pending.

Independent fitting/wrapper review reports no blocking findings, eight focused
tests pass and90independent gradient coordinates agree within1.69e-11.
The reviewed wrapper checks all4510post-fit cached logits against the reloaded
policy, ordinary predictions/other arrays, fixed gates and source/control/cache
bindings. CPU-only guard launch is live under execution handle13949; terminal
result and final telemetry binding remain pending. No native/RL is authorized
by this launch. Artifact root: `professional-context-query-01/`.

The frozen comparison completes terminal exit0 in105.75seconds. L-BFGS uses
250iterations/272evaluations and21.38optimizer seconds, stopping on the fixed
iteration bound rather than convergence. Actor loss0.636428→0.403963, selection
parameter norm27.24. Teaching actors1869→2172, complete825→953; all nine
teaching games improve complete counts. Against the frozen linear comparison,
this is1965→2172actors and853→953complete commands. This demonstrates increased
teaching capacity, not successful transfer.

Reused774diagnostic actors53→47, complete6→4, targets62→60. Unchanged ability
predictions remain3814/4513teaching and149/292diagnostic, row by row. The
teaching-size and all diagnostic improvement gates fail; only nine-game gains
and unchanged ability gates pass. No extension, sweep, promotion, native game
or RL. Saved/reloaded predictions all match, other arrays remain unchanged and
all4510cached/policy logits agree (maximum absolute error1.37033e-5).

Parent verification binds final contract/report/checkpoint/cache/control/source
and terminal telemetry. HostCPU peaks10.6%, childRSS5.58GB, no load stop.
Contract SHA256`cc61de886843d754a43e94b225740778fc764b22da03f9b3fd29c7e3b51c363b`,
checkpoint`d65e8c82ca8d236ecde038b597098227dd8bdedf7bd772d325b75c4c4a96c326`,
final telemetry`ae635b0065d5e79a2f5ed161d29eecdb7b4e86b9e0590f7a6af8b76b040eaf84`.
Artifacts: `professional-context-query-01/{contract,comparison,verification}.json`,
`lbfgs/{policy.npz,report.json}` and sidecar telemetry.

Read-only error summaries reproduce report totals: teaching589fixed actor
errors and286new ones, diagnostic17fixed and23new. Correct group cardinality
is2564/4513teaching,158/292diagnostic; both ability and exact actors occur on
2104/4513and38/292respectively. Diagnostic abilities outside three common
commands are mostly wrong, alongside persistent selection/target errors. Thus
another selection-head optimization extension is not justified. A next
experiment must address wider imitation/representation/data transfer; this
result does not prove the existing observations sufficient or missing.

## Cross-game human task audit and Astra advice (October 6)

Under the user's conditional authorization, Astra reviews the stalled wider
imitation evidence and recommends stopping isolated selection-head work.
Parent independently verifies the decisive existing oracle totals: supplying
both human ability and actors yields2040/4513teaching complete commands but
only75/292diagnostic, target76/292. Diagnostic point error averages33.02tiles
even with those two human answers. An actor-only fix cannot address the current
intent/target transfer failures. These oracles are diagnostics, never inference
inputs. The advice proposes causal event-sequence learning that predicts a
target before selecting actors, conditional on an observation/coverage audit;
it is an advisory hypothesis, not an implemented or accepted controller.

Parent applies the advice first through read-only data audits, without new
model predictions. `professional-context-query-01/ability-support-audit.json`
binds the existing report. All19diagnostic abilities appear among33teaching
abilities; no diagnostic rows have an unseen ability label. Marine training
has233rows across eight games,177correct teaching ability predictions but0/12
diagnostic; SCV306/459versus8/38; SupplyDepot58/105versus1/11. Missing labels
alone cannot explain the failures. Ability distribution total variation0.1698
does not establish sufficient state/strategy coverage.

`audit_professional_raw_support_01.py` reads only the bound nine teaching and
reused774datasets. Its first invocation fails on a sample-container type error
before writing evidence; the corrected invocation completes terminal exit0.
The source/report/configuration/helper-bound `professional-raw-support-01.json`
contains27fixed examples (first five per six common command families, only two
CommandCenter examples exist). It decodes saved predictions, checks gold actor
indices against ordinary input ordering, compares actor type/counts and point
errors, and finds nearby same-ability teaching states in explicitly scaled
resources/time/own-unit-count/order/history features. It does not treat nearby
states or interchangeable unit types as acceptance or adequate observations.

This verifies4513retained commands out of6069issued teaching events,1556
unresolved (25.6%). Histories contain32724unknown slots out of140359(23.3%).
The unresolved table retains raw ability-link/command-index/target families,
without inventing native ability identities. Partial source masks remain
explicit, including food used, energy, add-ons/passengers and other fields.
Their causal contribution to failures is unproved.

The opening774TrainSCV state is7.44048e-5from teaching955row0in the declared
interpretable features; only one game loop differs. The saved ordinary ability
is Smart for774andTrainSCVfor955. Opening own CommandCenter locations differ:
774[160.5,64.5]on200×184,955[33.5,138.5]on176×184. Every teaching opening on
200×184starts at[39.5,115.5]; this does not assert identical map identities.
Teaching870also mispredicts its opening worker command, so missing diagnostic
spawn coverage alone is not established as the cause. This supports examining
spatial/context transfer and legitimate canonical geometry before another fit.
No new training, reserved prediction, native game or RL occurs in these audits.

## Goal-first sequence controller implementation (October 6)

Rechecking local compatibility does not reveal a new professional native
source: installed Base75689 maps to4.10.0; existing fuller-observation datasets
are Masters examples, while named GuMiho/Bunny require75025and the professional
tournament cohort76052. Historical failed asset probes are not restarted and
no additional assets/downloads occur. These source gaps remain explicit.

The new declared experiment addresses joint intent/target/selection rather
than continuing the failed selection-head fit. `goal_first_policy.py` is a
separate optional CPU Torch controller using the same raw input and prediction
schema. A GRU processes the32causal event slots, observed ownership groups
provide pooled entities/counts, and ability/mode/target precede actor selection.
Selection receives the proposed target embedding and candidate-to-target
geometry. Queue/delay follow the selected group; autocast and arbitrary groups
remain available. Teacher mode/target/group condition losses only; ordinary
inference predicts each component, without human current selection or recipes.

Four tests are observed RED before the relevant API implementation, then GREEN
for all-head gradient flow, target-dependent selection, permutation/checkpoint,
history order, empty masks and explicitly named ability/group oracles that do
not supply targets. Optional installed Torch CPU runtime passes four tests in
0.55seconds. Default full354tests pass10.03seconds with ten optional skips;
Ruff/diff pass. The production-sized model has766637parameters, two CPU threads,
CUDA uninitialized; construction preserves global CPU RNG.

Independent controller review finds no blocker, verifies all four modes and
six numerical gradients including GRU/target/geometry/refinement, safe NPZ
loading and default imports independent of Torch. Reviewed sourceSHA256
`e053e58052e4fd0548716e78318c553a3b892824674cea170bf92c48584e8523`.
No fitting/native/RL occurs. Trainer, teaching-only input-support neutralization,
corpus integration, frozen reports and prediction-derived history evaluation
remain pending; implementation tests do not establish copying or strength.
Plan: `2026-10-06-goal-first-sequence-imitation.md`, including a single bounded
end-to-end fit and improvement gates for the now-learned ability classifier.

The supervised trainer and teaching-only support neutralizer are implemented.
Support scans numeric entity/scene/history/map inputs and categorical types,
orders, prior abilities and teacher ability. It clears only unused input
weights, not outputs or future gradients. Teacher-conditioned scores remain
exactly equal after clearing; a newly activated cleared feature receives a
nonzero gradient. Bounded Adam applies complete batches only, clips gradients
and reports completed epochs/updates/presentations/loss components. A tiny
fixture learns, immediate stop preserves weights, and inference does not
mutate them; none of these counts as corpus learning evidence.

Prediction-derived history evaluation rebuilds every history-dependent entity
reference and GRU input using only previous model predictions. It consumes
normalized `teacher_states` rows, verifies chronological single-command
alignment, unchanged tags/categorical orders/scene/base features/masks/map
candidates, and retains the unchanged spatial patches. A test proves that the
human actor reference is replaced by the predicted worker reference. The
human game states and decision schedule remain fixed; hypothetical predictions
are not engine-executed and do not establish native closed-loop competence.

Independent trainer/support/history review finds one deadline defect: an
example finishing after the deadline could still trigger an update. The
regression test is RED (`completed` instead of`wall_bound`), then GREEN after
a final pre-update deadline check discards the batch. No other reviewed math,
support or history leakage findings. The wrapper must use normalized
`teacher_states` and bind per-game source/order/reset; it is still pending.
Fresh default359tests pass10.06seconds with15optional skips; nine controller/
trainer tests pass1.04seconds in installed CPU Torch. Ruff/diff pass. No corpus
fit, diagnostic campaign, native game or RL has started.

The frozen corpus wrapper and whole-host watchdog are now prepared and
independently reviewed. A preflight-only pass loaded all4513teaching commands,
4510fitting examples and292reused diagnostic commands, checked source bindings,
teaching-only support and sampled supervised score parity. The support masks
are saved in safe NPZ and hash-bound before fitting; review's missing-support-
binding finding is fixed. Per-family reports retain all command/timing metrics.
Nine optional CPU tests pass1.03seconds; wrapper Ruff/compile pass.

The single supervised experiment was launched on October6 under live exec
handle42188, child PID2360900. Initial whole-host sample is4.1%CPU. It is
reloading the checked corpus before optimizer work; this is not a completed
fit. The watchdog uses the existing installed CPU Torch interpreter, two
threads, no CUDA, at most100epochs/1800optimizer seconds, and stops its own
child after three host samples above80%. No native games or RL run. Helpers
and preflight evidence remain ignored in `logs/roadmap/`; output is
`professional-goal-first-01/`, telemetry is
`professional-goal-first-01.telemetry.json`. Poll the same live handle rather
than restarting. Terminal results and parent verification remain pending.

The same handle42188 is confirmed live after preflight, with host CPU peak12%
and an active two-thread child accumulating CPU time. A separate terminal
verifier is prepared at `logs/roadmap/verify_professional_goal_first_01.py`.
It requires completed watchdog telemetry, verifies source/checkpoint/support
bindings, reconstructs all4805ordinary predictions, exact per-family reports,
teaching support and each game's prediction-derived history, then recomputes
the eight frozen gates. Review caught JSON tuple/list equality mismatches;
normalization fixes them and a small regression reproduces/checks that fix.
Aggregate teaching named-oracle counts and weighted point-error summaries
were added after review identified this coverage limit. Ruff/compile pass;
the terminal verifier has not run. It does not fit, launch native games or
perform RL. Current learning outcomes remain pending.

### Goal-first supervised result (October6)

Handle42188 is terminal exit0:100epochs,28200updates,451000presentations,
1495.83optimizer seconds;334host samples peak13%CPU and no guard stop.
CheckpointSHA256`17af73059ada368db54e782b61bb1cddb660f3bc4a09868d4241aee37d6ca7ef`.
Teaching ability4259/4513,actors2829,target3120,complete2118,complete with
timing1627. All nine teaching games improve complete commands over fit05.
Reused774diagnostic ability157/292,actors52,target69,complete13,complete with
timing1; macro ability6/91. Teaching gates and diagnostic target pass, but
diagnostic ability/actors/complete/macro gates fail. No extension, sweep,
promotion, native game or RL occurs.

Own prediction-history teaching complete98/4513 versus human-history2118;
diagnostic complete3/292 versus13. Both modes retain human states and decision
times; neither establishes native competence. First ability differences appear
within one to six retained commands in each game. A read-only code check shows
the controller history encoder does not consume the absent actor-type metadata
used by a different historical encoder, so that suspected mismatch is not a
demonstrated cause. Prediction errors and omitted unresolved event slots must
be separated before selecting another learning intervention.

Independent verifier handle36834 is terminal exit0, reproducing4805ordinary
predictions, all per-game/per-family audits, teaching-only support and all
prediction-history traces. Aggregate named-oracle counts/point errors match;
all eight gates are independently recomputed. `verification.json` records
`verified_completed_failure`; final telemetrySHA256
`1173f4d1298c0d8c543276f557c9fabc90306dd2adde482d0b60b2b7393161ff`.
Read-only retained-human-history oracle launched under handle24481, two CPU
threads, no fitting/native/RL; its result is pending. It supplies only past
retained human commands after each current prediction, never current/future
labels during inference. Preserve `history-diagnostic.json` and the eventual
`retained-history-oracle.json` alongside original frozen experiment artifacts.

The retained-history oracle handle24481 is terminal exit0. It reconstructs
all4805rows without fitting: teaching ability2724/4513,actors1389,target1027,
complete302; diagnostic ability141/292,actors48,target68,complete10. Teaching
complete thus falls2118→302 even when prior retained human commands are exact,
and falls further to98 with predicted history. This demonstrates sensitivity
to the changed command-history representation as well as prediction error;
it does not prove that any single omitted field/event causes all failures.
All non-history candidates/base fields/orders/scene/map geometry are checked
unchanged; only past commands are inserted after the current prediction.
OracleartifactSHA256`cfe8add992dc7bcd6155988b07bc7a5f7fa9d61a6ced18060e9a340bd0ed557b`.
Next work should align teaching history with history actually available to the
agent, then measure prediction-error sensitivity separately. No second fit has
been launched; the frozen failed trial stays unchanged and the full roadmap
remains incomplete.

Retained teaching-history rebuilding is implemented in `goal_first_train.py`
using shared alignment/non-history invariants with prediction-derived history.
The new test is RED for the absent helper, then GREEN: current/future command
mutation leaves current inputs unchanged, excluded labels still contribute
known past commands, history resets and misaligned/reversed/count-mismatched
rows are rejected. Ten optional CPU tests pass1.04seconds; default360tests pass
10.06seconds with16optional skips; Ruff/diff pass. Independent review finds no
blocker. Professional294parity reproduces all467saved retained-oracle
predictions/audit and the original saved own-history trace exactly; helperSHA
`08e535043ae70fbe6f006f9d4d39e0c39646b2524c9a4ed38e083d02838d415d`.
This changes collection history, not controller architecture/action space or
default NumPy policy. A fresh representation-only fit is planned separately;
its own-history gates are declared before fitting. Previous failed artifacts
remain unchanged; reproduce their original source from the recorded Git
revision rather than treating the changed trainer's SHA as historical code.

Fresh representation-only wrappers `run/watch/verify_professional_retained_history_01.py`
are independently reviewed without blockers. Full preflight handle8698 is
terminal exit0: all4805previous frozen-model predictions reproduce the saved
retained-history oracle, counts remain4513teaching/4510fitting/292diagnostic,
and sampled supervised input-neutralization parity passes. The controller,
losses, optimizer, seeds and bounds are unchanged. Fourteen gates include all
previous copying gates plus own-history teaching complete>=1000 and diagnostic
ability>=170,actors>=73,target>=62,complete>=24,macro ability>=20of91.

The single new experiment is launched under live exec handle27513,
childPID2372207. Initial host CPU peak4%; corpus reload is active before fitting.
Output `professional-retained-history-01/`, telemetry
`professional-retained-history-01.telemetry.json`, preflight receipt
`professional-retained-history-01.preflight.json`. Two CPU threads, CUDA hidden,
existing installed runtime,100epochs/1800optimizer seconds,80%host guard.
Poll the same handle; no second concurrent fit/native/RL. Results and independent
terminal verification are pending. A failure ends this trial without extension.

The retained-history trial is now terminal exit0; independent verification
handle19231 also exits0 and records `verified_completed_failure`. All4805
ordinary predictions, audits and hypothetical own-history traces reproduce;
all fourteen gates are independently recomputed. Teaching complete commands
are1282/4513 with human history and80/4513 with predicted history. Diagnostic
complete commands are8/292 and1/292; diagnostic macro ability is5/91 with human
history and0/91 with predicted history. The overall gates fail. Representation
alignment alone has not solved copying or compounding prediction failures.
100epochs/28200updates/451000presentations take1497optimizer seconds; whole-host
CPU peaks14.4%, below the80%guard. No extension, promotion, native games or RL.
ComparisonSHA256`1d5cc9e53166abcca4a4b63bd983b7034c579bd4d73f89618dc91d0e255df9ac`;
finaltelemetrySHA256`7a000395d2489ad05af61c54ccfecca48306a06bd6ec7d199566d3cb12d2808d`;
checkpointSHA256`d0cf4326d813d5d17ab250f4d46023379bd4445edb92e31ff2d7c0a1b1cc0a58`.

The user clarified that the current stage should train on human runs. This
matches the roadmap: current targets come from human replay commands, and RL
remains stopped. Evaluating past model predictions on unchanged human replay
states is offline imitation evaluation, not reward-driven training or evidence
of actual game competence. The next intervention must address useful human
imitation before proceeding to the roadmap's later experimentation stage.

Read-only retained-history ablation handle60654 exits0 in18.72seconds. On
teaching294completecommands are124with32past human commands,47with8,25with1,
10with none. Reused774completecommands are8,11,8,3 respectively. No weights
change and no games run. Removing history does not rescue copying; this does
not isolate history as the sole cause. Artifact `history-ablation.json` SHA256
`72a268fa24d8e3ebacaa0fb7a06b9a77c0d92ef2f129ee9e187baf1a353d2a10`.

Mixed-history imitation is implemented: human next-command labels remain fixed,
but causal past history can remember the model's hypothetical command. Seeded
probabilities0/1 reproduce own/human history; tests cover resets,32events,
excluded labels and current-command mutation. Trainer refresh occurs under
eval/no-grad, retains one optimizer and teaching count. Review caught a refresh
overrun; a cooperative monotonic deadline now stops generation per row and ends
fitting without updates. Fourteen optional tests pass1.19seconds. Default364
tests pass10.09seconds with20optional skips after an isolated9runtime-test pass
and rerun for one descendant-cleanup timing failure; runtime code unchanged.
Ruff/diff checks pass. Independent implementation/fix reviews find no remaining
blocker. No fit, native games or RL launched by this implementation change.
The next single supervised trial's schedule/bounds/gates are declared in
`docs/superpowers/plans/2026-10-06-mixed-history-imitation.md`.

Final deadline-enabled professional294parity handle17848 exits0: all467own
history trace records reproduce the saved parent records and both probability
endpoints reproduce saved ordinary predictions. Receipt
`professional-mixed-history-01.deadline-parity.json` binds current helperSHA256
`59405eb075c9141c2b5a5bd05689633fcfc4090ca6826ad07b06a8462f75023c`.

Mixed-history run/watch/verify wrappers are independently reviewed without
blockers. Preflight handle84453 exits0 with no optimizer updates or trial
output directory: all4805parent predictions reproduce saved records and the
first mixed teaching refresh supplies4510samples in28.16seconds. PreflightSHA256
`775135b89ad3cd95dbfd432829fdc40946210462917a8f193f53a3195031e6d0`.
Before launch, all preflight bindings still match, prior training PID2372207
is absent, no matching fit/watch process is live, and whole-host CPU is1.1%.

The one authorized supervised trial is launched under live exec handle73442,
childPID2384922. Initial watchdog samples peak4.4%whole-host CPU; no guard stop.
Corpus reload is active. Output `professional-mixed-history-01/`, telemetry
`professional-mixed-history-01.telemetry.json`. Parent weights are preserved at
initialization; descriptive teaching support is not reapplied to weights.
Fresh Adam.0003/batch16/50epochs/1200seconds including refresh, shuffle8143,
human probability.5 for first20epochs then0, teaching refresh every5epochs,
two CPU threads/CUDA hidden/80%host guard. Snapshots and input digests allow
independent reconstruction of each recorded refresh. Final own-history
evaluation regenerates history from the final policy rather than the fitting
cache. All14gates remain unchanged. Poll this same handle; no concurrent fit,
native games or RL. Terminal results and independent verification are pending.

Mixed-history trial handle73442 is now terminal exit0. All50epochs complete,
14100updates/225500presentations,1185.78seconds including all10history refreshes,
within the1200second bound. Total load/fit/evaluation1389.73seconds;280host
samples peak11.1%CPU with no stop. Producer reports all14gates failed: teaching
human-history complete387/4513 versus parent1282, own-history193 versus parent80;
reused774complete2/292 with human history and3with predicted history. Diagnostic
macro ability3/91 with human history and2/91 with predicted history. No native
games, RL or promotion. This trial ends without extension. These are producer
results, not yet independently verified.
ContractSHA256`1f6df5f6047c6f216dd4e75d78600b3ade66ef7630ac4686451ce3a17830636a`;
reportSHA256`9668099b8347c5156a6c1e03b6148f7dd7fc7ed041062be877640a1683d6ed47`;
checkpointSHA256`d421803ff94c667d9a0824a3f12e2ab07788e654c4670b892acc23b242222600`.
Independent verifier is live under handle87351. It reconstructs all10recorded
refresh inputs from snapshots and independently reproduces final ordinary,
oracle and own-history reports. Poll that verifier rather than restarting fit.

Read-only native-path inspection confirms `entity_play.py` loads
JointEntityPolicy and validates its NumPy encoder fields; GoalFirstPolicy is
not yet wired to that runner. A tested adapter is still needed before native
evaluation of a useful new controller. No native competence is inferred from
offline copying results, and the full roadmap remains incomplete.

User-authorized Astra consultation challenges repeated failed imitation fits.
Parent independently counts mixed774own predictions:243Smart(ability1),
45Attack(3674),4TrainSCV(524), no other abilities; human Smart count157of292.
Thus160correct abilities barely exceed the Smart-frequency baseline, and
ownmacro2/91cannot be explained only by exact worker/target tolerance. The
advisor recommends one game-held-out state-vs-human-history-vs-both ability
probe on the nine teaching games, with fold-only preprocessing, a300second
combined bound and explicit macro false positives/absent classes. Frozen empty
history ablation is distribution shift, and corrupted command histories on
human states are not environment-consistent rollouts. These are diagnostic
hypotheses, not competence claims. Advice is applied in the next probe plan
`docs/superpowers/plans/2026-10-06-intention-sufficiency-probe.md`; no new fit
is launched before current independent verification finishes.

Mixed-history verifier handle87351 is now terminal exit0:
`verified_completed_failure`. All10saved teaching refreshes (45100inputs) and
all4805final ordinary predictions reproduce independently; complete reports,
oracles, hypothetical own histories and all14failed gates agree. Final telemetry
SHA256`8ed30837212c7a49240629d717d3de457b9ff89230a83637b876b45a0d6939f5`;
comparisonSHA256`7c111b3b38d5be102957cfc82b79f51692a840e88112e9c1086ac207201b7d3b`;
verifierSHA256`d1ebf455ca0efd923d3db379933aeb40787b78ffa539c6678ddfc401d9368d37`.
No fitting or native/RL process from this trial remains active.

`intention_probe.py` implements the next optional-SciPy diagnostic: masked
current scalars/upgrades and native type/order counts separate from causal
human event history; no labels/actor tags/current targets enter features.
Training-fold-only sparse RMS/column/class statistics and bounded regularized
multinomial fitting. Exact macro recall, family recall, false positives and
absent-class errors are separately reported; cross-entropy floors probability
at1e-12. Four tests observed missing-interface RED then GREEN0.13seconds,
including independently calculated metrics and deadline expiry. Independent
implementation review finds no blockers; existing SciPy is available, with no
install. No corpus fit has run yet; wrapper/deadline/independent result checks
remain required. The fixed solver settings are declared in the probe plan.

Full default suite now passes368tests in10.08seconds with20optional skips;
Ruff/diff checks pass. Source/test implementation review is clean. No diagnostic
corpus predictions or optimizer run has occurred at this milestone.

### October6: closed intention diagnostic and live goal-first adapter

The intention probe is terminal and independently reconstructed: all4513rows,
fold-only scales/classes, predictions and metrics match. It took42.70seconds,
peak wholeCPU7.2%. All9fits hit100iterations without convergence, so the signal
result is inconclusive, with no positive gate. Fixed first3state-arm macro
mistakes per held game are18TrainSCVand9SupplyDepot, all predictedSmart.
Read-only saved-model objective/gradient reconstruction finds state teaching
macro recall4–7%, history80–84%, both92–94%, versus weak held-game results.
Producer orders/resources/counts are available in these opening source rows;
missing food_used cannot be claimed as the sole cause. No fits were extended.
See [results](superpowers/plans/2026-10-06-intention-sufficiency-probe-results.md).

The native adapter gap described above is now closed: `entity_play` explicitly
accepts `--controller goal-first`, while the default remainsjointwith no Torch
import. Native vocabulary/history-role/point-layout guards run before command
execution; shared decoding/spatial masks/issued-only history are preserved.
372normal tests pass (23optional skips),14focused optional tests pass, Ruff and
independent review pass. One installed-engine15second wiring smoke completed
336frames/11successfulSmartcommands; all11decisions/delays/history independently
reproduce from the immutable checkpoint. Replay saved, not displayed. CPUpeak6.1%.
This is a deliberately truncated wiring proof, not a useful macro policy or
full-game competence. No training/RL process is active. See
[adapter verification](superpowers/plans/2026-10-06-goal-first-native-adapter.md).

Next model work should investigate truthful current-state representation,
including unit-type-specific producer status instead of ownership-only means,
and explicitly test teaching fit plus whole-game generalization. The closed
linear probe does not prove nonlinear signal absent. RL, micro transfer,
reliable all-raceHard and higher difficulty gates remain open.

### October6: type-specific status intervention ready

`entity_type_status` preserves current own native-type counts and known
build/queue/progress/idle/unfinished status, explicitly masking unavailable
values and keeping memory count-only. GoalFirstPolicy optionally adds a
zero-initialized learned projection; all existing base initialization and old
checkpoint predictions are preserved. Its full raw action grammar is unchanged.
Tests observed missing-interface RED then GREEN:375normal tests pass (24optional
skips),21focused optional-runtime tests pass, Ruff/diff checks pass. Independent
implementation and paired-wrapper reviews found no blockers.

Prefit handle47560 is terminal exit0:6teaching games3400rows/3398complete labels,
3held development games1113rows; source validation, teaching-only support and
initial base-weight/prediction parity pass with zero optimizer updates. No774or
reserved inputs/predictions were used. Frozen paired run is prepared under
`logs/roadmap/run_type_status_imitation_01.py` and matchingwatchwrapper; plan is
[here](superpowers/plans/2026-10-06-type-status-imitation.md). It has not yet fit at
this source milestone. The prior diagnostic remains closed. This intervention
needs actual independently verified comparative results before any strength
claim or broader native/RL work.

The paired run is now confirmed live under watcherhandle28403, childPID2407534,
with baseline fit started (766637parameters). Latest sampled wholeCPU6.5%,
peak8.9%; no resource stop. Source/plan/wrappers remain frozen. The prepared
`verify_type_status_imitation_01.py` independently checks initial parity/support,
all9026ordinary and2226held own-history predictions, metrics and five gates;
read-only review finds no blockers. Run it only after confirmed terminal
comparison/telemetry; no success or failure gate is available yet.

- Frozen paired contract SHA256`331cf3086562300d0efdf02507f0ab6e2d4e99aa618285adce63c56d3fe9ee88`.
- Prepared verifier SHA256`4bc6758357b5af33d7c70d8ef36ee6c5d091f1478224a3a61029b995347c7c18`.

### October6: opt-in native stepping during learned waits

Native execution accepts `--max-game-step` (default1) to cap advancement at
the model's next scheduled decision; due/unissued retries stay1loop. Recorded
selected-step counts are explicit. Review and376normal/26focused optional
tests pass. One cap32opening smoke reduces callbacks336to14while exactly
matching11command loops/arguments/delays/results and final own state of the
retained15second cap1opener. Independent model/history reproduction passes;
replay saved. This is a limited wiring/performance observation, not general
fog-memory/strength equivalence, and the one-loop default stays unchanged. See
[verified limits](superpowers/plans/2026-10-06-adaptive-imitation-stepping.md).

Paired imitation handle28403 remains live: baseline completes30epochs, held
macro27/262(10.3%),31/1113complete commands; own-history macro10/262(3.8%).
These are provisional until the full comparison independently verifies. The
type-status arm has started (2027437parameters), with no final result yet. No
frozen fitting source/plan/input binding has changed during native optimization.

### October6: paired fits closed; native representation discrepancy isolated

Watcher28403and independent verifier32613are terminal exit0. Both30epoch fits
completed; type status fails all four improvement gates (held macro32/262versus
27/262, complete26versus31, more false positives). Neither model is promoted or
extended. Native inspection11830and reconstruction77644are terminal exit0:
both180second openings produce zero new workers/buildings and repeatedly issue
Smart/Attackcommands. CPU peaks6.7%/6.6%; weights frozen, no RL.

A frozen opening diagnostic identifies equivalent native295/professional3666
mining-order IDs and partial-source field availability as interacting input
mismatches: matching both restoresTrainSCVprediction in both saved models;
either change alone does. This warrants explicit observation-contract compatibility,
not another training sweep or a strength claim. Full native observations must stay
available in logs and any source projection must be explicit and tested. See
[results and next check](superpowers/plans/2026-10-06-type-status-imitation-results.md).

### October6: explicit professional input contract restores native worker production

Opt-in observation profiles match missing-field declarations and engine-verified
order aliases without changing raw traces, command grammar or weights. Known
native dispatched history remains known. Profile derived from all rows/catalogs
of the six paired-fit teaching games only.379normal/15focused optional tests,
Ruff/diff and independent review pass; incorrect engine aliases are rejected.

Frozen baseline native opener30437is terminal exit0. It produces three actual
new workers (12to15), collects2175final minerals, then supply-blocks; noDepotor
Barracks. Seventeen issued commands returnSuccess;2501unavailableTrainSCVrequests
stay out of issued history. Trace reconstruction verifies all2518decisions.
CPU peak9.7%, noGPU/fitting/RL. This is a concrete opening compatibility repair,
not promotion or full-game competence. See the
[implementation and verified limits](superpowers/plans/2026-10-06-professional-observation-contract-results.md).

### October6: engine-conditioned choices remove unavailable retries, not macro failure

Opt-in GoalFirst command candidates use resource-aware normal queries plus
resource-independent autocast queries and catalog flags. Alias, ability, mode and
caster masks preserve default inference and checkpoint weights. Review caught
and fixed an input-mask alias mutation before execution. Normal385tests (29skips),
focused21Torchchecks, Ruff/diff and independent review pass; inherited optional
checks are included in the count.

Native watcher22805and verifier47983are terminal exit0. Frozen baseline/profile
opener produces3newworkers,167accepted submissions (3TrainSCV/164Smart), zero
availability blocks,2180finalminerals,15/15supply and zeroDepot/Barracks. Independent
reconstruction reproduces all167choices using the saved raw queries/profile;
CPUpeak6.1%, noGPU/fitting/RL. Legal Smart choices replace the old impossible
SCVretry loop without repairing macro planning. No model promotion or extension.
See [verified result and next diagnostic](superpowers/plans/2026-10-06-native-command-candidates-results.md).

The prior observation-profile plan is restored to its exact frozen hash, with
results moved to a separate document. Keep future experiment plans immutable;
source-bound historical verifiers require their corresponding Git implementation.

### October6: seeded imitation sampling produces actual economic construction

GoalFirstsupports explicit optional ability sampling from its learned distribution
after engine masking; default/forced-label behavior and all weights stay unchanged.
New tests prove seeded probability draws, input/weight invariance and no draws for
empty candidates/forced choices.387normaltests (31optional skips),23focusedTorch
checks, Ruff/diff and independent review pass.

Frozen opener59273and independent verifier15655are terminal exit0. Fixed ability
seed120603produces eight new workers, a completedDepotandRefinery, final20workers,
23supplycap and1365minerals/268gas. All112draws/commands/history reconstruct.
ThreeCommandCenterand oneBarracksplacement fail; five other commands return
NotSupported. CPUpeak6.0%, noGPU/fitting/RL. This is one deliberately truncated
VeryEasyopening, not checkpoint promotion, reliable planning or a full-game win.
No seed sweep/extension. See
[sampled-policy result and next execution repair](superpowers/plans/2026-10-06-sampled-human-policy-results.md).

Next integrate the existing local engine-placement primitive explicitly, preserving
learned build choices and recording requested versus actually dispatched commands.
Useful imitation and all remaining roadmap gates are still incomplete.

### October6: existing placement primitive integrated and reconstructed

Opt-in native engine placement preserves original model choice and records actual
adjusted dispatch/history plus exact query packets. Separate rejection/adjustment
counts and default-parity integration tests pass.390normaltests (31optional skips),
30focused optional/execution checks, Ruff/diff and independent review pass.

Watcher61363and verifier76397are terminal exit0. Same fixed sampled checkpoint/
profile/candidates/seeds opener completes one additionalCommandCenter, twoDepots,
twoRefineries and16totalworkers, but noBarracks/army.125choices reconstruct,
including threepoint adjustments; zero placement-location failures. ThreeRefinery
unit-target commands still returnNotSupported. CPUpeak10.5%, noGPU/fitting/RL.
This is valid execution evidence and inefficient macro behavior, not promotion,
a repairedBarracksattempt, reliable planning or a full-game win. See
[verified placement result and target-validation question](superpowers/plans/2026-10-06-native-placement-primitive-results.md).

Next inspect the rejected unit-target gas positions before changing target behavior;
existing point resolution deliberately does not replace the model's selected geyser.
The full human-imitation/micro/Hard-and-higher roadmap remains incomplete.

### October6: unit construction validation; learned barracks intent remains weak

Exact selected visible unit positions now receive one engine placement query;
valid commands retain their unit target, invalid/unobserved ones do not dispatch
or enter history. No alternategeyserchosen.392normaltests (31optional skips),
32focusedoptional/execution checks, Ruff/diff and independent review pass.

Watcher72828and verifier12437are terminal exit0.101sampled decisions reconstruct
with98actualdispatches. Two invalidrefineryplacements and one localCCplacement
are blocked; fourremainingNotSupported responses areSmartcommands. Final24workers,
2Depots,1Refinery,oneadditionalCC, noBarracks/army. CPUpeak6.3%; noGPU/fitting/RL.

Barracksis engine-eligible in41of101states, but frozen probabilities at first/
middle/last eligible states are only.37%/.25%/.30%. Teaching sources do contain
18Barracksand162Marine commands over six8–14minute games. The next work should
address human production-intent supervision, with a coverage/predictability audit
before another controller fit, rather than more unchanged execution openers.
See [verified result and next learning question](superpowers/plans/2026-10-06-unit-construction-validation-results.md).

### October6: human production forecast coverage audited

Current phase remains human imitation. New target-only labels retain exact
loop/sequence order, censor intervening unknown issued events and reject ambiguous
source contracts. On six fitted games, 850 immediate production commands yield
2,069 usable forecast observations; 1,322 rows remain unknown-censored. Barracks
18→40 labels still represent the same 18 decisions. All 3,400 labels reconstruct
independently, source bindings match and observations remain unchanged.

A source-bound unresolved-name inspection finds 900 of 1,276 unresolved events
without the current exact engine-name/index match, including army production.
Names and sc2reader fallback unit IDs are insufficient to recover commands.
Next investigate independently verifiable production identities and coverage
before another imitation fit. No native game, optimizer or RL ran. Normal suite:
395 tests pass, 31 optional skips. Full roadmap completion remains unproved.
See [coverage evidence and source-repair direction](superpowers/plans/2026-10-06-production-forecast-coverage-results.md).

### October6: missing human army production recovered into a separate corpus

Exact named producer metadata plus unchanged selection/flags/target/loop/mutual
uniqueness gates recover146commands across the six fitted games:74Hellions,
35SiegeTanks,15WidowMines,1Thor,18Orbital and3Planetary morphs. No reader numeric ID
joins, freeform name guesses or original-corpus edits. All3,400previous commands
retain full serializations; zero retained-command metadata contradictions.

Independent correspondence reconstruction passes3,546commands. Separate imports
finish allsixgames with peakwholeCPU8.3%, CPU-only/noRL. Every causalhistory and
delay label reconstructs;3,400prior observations remain unchanged apart from history.
Source eligibility and vocabulary checks pass;3,544labels are representable, with
the same two prior observed-target exclusions. Normal suite397tests/31optional skips,
Ruff/diff and independent review pass. The new corpus is
`logs/roadmap/pro-demonstrations-production-08/`; no learned improvement is claimed.

Next design a bounded human imitation experiment on the repaired source, explicitly
reporting the recovered production families and ordinary complete-command fidelity.
RL/native promotion and the remaining micro/Hard/higher roadmap gates stay pending.
See [recovery evidence and limitations](superpowers/plans/2026-10-06-production-identity-audit-results.md).

### October6: matched source-version human imitation run active

Frozen [paired source-version plan](superpowers/plans/2026-10-06-repaired-production-imitation.md)
compares fresh original/repaired controllers with identical initialization and
teaching-only union support. Each arm gets3,398examples/epoch,30epochs,
6,390updates/101,940presentations if complete; repaired sampling draws without
replacement from3,544representable rows. Full planned indices/exposure are saved;
actual exposure is calculated from completed optimizer updates, including partial
epochs. Source repair includes shared-row history/timing changes, not just146labels.

Preflight95519 is terminal exit0, CPUpeak5.0%, zerooptimizer updates. Tenoptional
CPU-Torchfit/provider checks, partial-epoch exposure reference checks, Ruff/diff
and independent read-only review pass. Reporting amendments preserve the executed
preflight script snapshot and repeat all initialization/sampling assertions before
the final fit. Final contract SHA256:
`4e85ce4716ab286005e2bdcc608cc22ee582551b628cc976b49deb5169211cda`.

Watchdog session53923 is live, with original-arm fit-start output observed. Each
arm is capped at600optimizer seconds, whole run1,800seconds, CPUguard80%.
NoGPU/native/RL. Use this existing handle for subsequent waits; its childPID39 is
local to the watchdog execution namespace, so another shell's PIDlookup cannot
prove job termination. Telemetry is
`logs/roadmap/repaired-production-imitation-01.telemetry.json`.

No result or checkpoint promotion is claimed. Next await this exact run and
independently reconstruct both ordinary and own-history metrics, including recovered
families. Close at bounds without extension/sweep. The full roadmap remains active.

### October6: repaired-source imitation trial closed after independent verification

Run53923and verifier51260are terminal exit0. Botharms30epochs/6,390updates/
101,940presentations; optimizer339.20/346.31seconds, peakwholeCPU11.6%.
All9,318ordinary and2,226own-history predictions/metrics/gates independently reproduce.
Matched budgets and false-positive tolerance pass; allfive improvement gates fail:
heldmacro27→21/262, complete31→28/1,113, own-historymacro10→4/262.
No extension, promotion, native game, GPU or RL.

Newteaching146rows: ordinary complete0→19; ability0→26. Given correct ability,
conditional complete3→122; given ability+actors, repaired146/146. This establishes
conditional argument learning on these teaching states, not autonomous planning.
Next test upcoming human production intent/timing supervision separately from the
next raw click, with censored target-only future labels and no future-input leakage.
Preserve full raw controls and sensory information; no recipe/primitive action-space
replacement. See [verified source-version result](superpowers/plans/2026-10-06-repaired-production-imitation-results.md).

### October6: upcoming human production diagnostic closed

[Fixed forecast diagnostic](superpowers/plans/2026-10-06-production-forecast-probe.md)
completed at peakwholeCPU8.7%, withoutGPU/native/RL. Independent verification
reconstructs3,162targets and6,324predictions.399tests/31optional skips pass.
State-only heldaccuracy34.30%, state+history30.44%, majority37.47%; nonworker
accuracy15.86/16.08%, Barracks0/13. History fits97.54%teachingchoices but generalizes
poorly. Bothnumericalsolves verify, so this result is not an iteration-limit artifact.
No promotion or extension. Next use one fixed nonlinear current-state diagnostic
to test resource/count threshold interactions before choosing controller work.
See [evidence and limits](superpowers/plans/2026-10-06-production-forecast-probe-results.md).

### October6: nonlinear production diagnostic completed

One fixed CPU tree model/refit finishes46.74seconds, peakwholeCPU9.5%, noRL.
Developmentclass-average recall12.01→26.34%, nonworker15.86→20.26%; Barracks0→5/13.
Marine38→11/217; overallaccuracy35.95% stilltrailsworkermajority37.47%.
Balancedclassweights andmodelbothchange, so noisolatednonlinearityclaim.
No promotion/sweep. Next audit additional localprofessionaldata and sensorycoverage
before anotherfullcontrollerfit. See[results](superpowers/plans/2026-10-06-production-threshold-probe-results.md).

### October 6: additional professional human sources verified

[Bounded intake 02](superpowers/plans/2026-10-06-professional-source-expansion-02.md)
adds five games with 2,543 commands, 2,542 representable. Teaching now contains
11 games with 6,089 raw and 6,086 representable decisions. Existing development
and reserved splits are preserved. All 65 initial own identities, 456,482 whole-source
own-type checks, 2,543 independent command correspondences and every history/delay
verify. Metadata verification reconstructs 81 producer mappings and binds 87 reader
files. The final verification receipt binds admission evidence and next fit inputs.

Transfer reservations total 5,789,851 bytes, below 16 MiB. Import CPU peaks at
13.3 percent of the host; all imports finish normally. No GPU, native game, optimizer
or RL. One unmatched raw game and one unobserved target label remain excluded.
Preserve unknown energy and other missing fields. Next freeze human-only training
on the expanded data, applying the production/generalization findings.
See [verified intake](superpowers/plans/2026-10-06-professional-source-expansion-02-results.md).

### October 6: expanded imitation closed; outcome imitation passes offline gates

The expanded full-command fit completed30epochs/6,390updates/101,940presentations
and independent reconstruction. All learning gain gates failed: production27/262,
complete30/1,113, own-history production3/262. No RL/native promotion.
See [closed fit](superpowers/plans/2026-10-06-expanded-professional-imitation-results.md).

A new human-supervised production-outcome model copies multiple outcomes over
45seconds. It uses verified own tracker labels, masked current state, no action
history and the eleven-game teaching/three-game development split. It passes
frozen offline gates; all6,354labels/predictions/metrics independently verify.
Fit19.78seconds, CPU-only two threads, peak19percent host CPU. This does not
establish native competence or reliable Hard wins. RL remains off.
See [verified outcome result](superpowers/plans/2026-10-06-human-production-goals-results.md).

ProductionLedger and its focused tests account for predicted/pending/queued work
without creating strategic goals. The native executor is not yet integrated.
Next complete generic engine execution, input-profile parity and six fixed bounded
native development games with declared assistance. Do not refit/sweep the passing
model or unlock RL before useful closed-loop imitation is demonstrated.

### October6: verified native human-outcome panel and caster fix

Generic native execution and masked-input parity are implemented. Six frozen Hard
jobs finish;1,543predictions and original replay production chronology verify.
Three Macro games pass sustained production gates; three Rush defeats fail.
Zero wins; all-race starting competence remains incomplete. Peak CPU27.2percent.
No refit, RL or reserved use. See [native result](superpowers/plans/2026-10-06-human-production-goals-native-results.md).

A source-trace-backed addon alias regression now restricts Factory Tech Lab goals
to actual Factories. It passes its formerly failing test. Native revalidation and
addon/spawn placement investigation are next; no unchanged model sweep. Preserve
`human-goal-native-01/panel/source-snapshot` as the original execution code.

### October6: clearance repair and fixed-model native recheck

Native debug fixture verifies clear/blocked addon pads. Generic execution reserves
addon/spawn space, pending/batch footprints and claimed geysers. Same six Hard jobs
complete; predictions and original replay production verify. Actual FactoryTechLab
starts improve3/6to6/6, delayed action errors1to0; zero victories persists.
Macro workers decline40/49/48to35/31/37, with three sustained Macro passes and
three Rush failures. Peak CPU30.1percent, no fit/RL.419tests pass with31skips.
See [repair result](superpowers/plans/2026-10-06-production-clearance-results.md).
Next audit temporal/resource interpretation of human outcome forecasts; no
unchanged fit/sim sweep or hidden strategic recipe. Full roadmap remains active.

### October 6: user-directed primitives-first reset

The user redirected execution to diagnosing losses and building reliable
primitives from established open-source SC2 bots, explicitly including attacking
and combat micro. This supersedes the preceding next-step restriction on scripted
strategy for the baseline phase. Imitation and RL training are paused; the latest
saved timing-model reevaluation finished, failed its error gates, and was not
deployed. No new learning batch is authorized by this reset.

The active goal and roadmap now require native verification of mining, worker
and army production, supply, construction, scouting, army movement, attacking and
combat micro, followed by a declared all-race scripted Hard baseline. Diagnose
resource starvation and the lack of offensive army destinations using saved
traces and actual game outcomes. Reference bot selection still requires source
and license inspection; no bot has yet been selected or proven on our engine.
Then return to professional imitation with the verified execution layer, and
only afterward RL and learned micro transfer. Scripted wins must remain distinct
from learned-controller wins; the complete roadmap remains unfinished.

### October 6: Terran primitives controller and Linux visibility repair

Shared mining/combat rules and a scripted Marine/Tank/Medivac baseline are
implemented. Test-first regressions and a native four-minute economy/production
smoke pass. The first Hard diagnostic panel finished two Terran cutoffs and one
Zerg victory before being stopped for a visibility defect; none counts toward
acceptance. Frozen sources and receipts are preserved. Shared PlayerView now
uses the visibility grid to guard bogus Visible flags on Linux 4.10, matching the
installed SDK. Historical source observations require auditing before fitting.
Attack-search arrival and redundant command handling are also repaired.

The formerly active panel 02 and its verifier are terminal. Four wins in six:
Terran Rush, Zerg Rush, Protoss Rush/Macro. Terran/Zerg Macro cut off. Original
replay/tracker and sampled fog checks pass; CPU peak19.9percent. Reference bot
selection is complete: pinned Sharpy/Burny MIT source informed the controller;
the local unchanged Reaper reference lost all six diagnostic games.

### October 6: action legality, reachable construction and army coordination

Panel 03 completes and independently verifies four wins in six: both Zerg and
both Protoss games; both Terran games cut off. CPU peak7.7percent. Removing
untargetable KD8 charges, restricting detected/ranged targets, respecting Tank
transforms and requiring reachable builder placement eliminated raw action
errors in all six games. Eight delayed errors remain, all in Zerg Rush. Relative
Tank caps, Viking production and returning the scout to mining also apply.
Source snapshots and original artifacts are frozen separately for panels02/03.

The next candidate repairs a trace-supported coordination hypothesis: support
units kept the supply-based attacking flag latched after ground-force losses.
Marine/Tank strength now controls attack/regroup decisions; Vikings follow the
ground force unless engaging visible aircraft. Dead actors are excluded.
Meaningful regressions failed before fixes and now pass. Full suite450tests,
32optional skips; separate native smoke passes in15.2seconds. The targeted Terran
Rush/Macro recheck in `primitives-native-04/panel` and verifier are terminal.
RushDefeat1029.6seconds; Macrocutoff1200seconds; peakCPU5.5percent. Zero raw
errors, three delayed Macro errors. This candidate did not improve strength.
Original sources and artifacts are frozen. Tank traces show near-home positions
despite distant attack orders; next check actual unit paths/production exits.
Scripted wins remain separate from learning; imitation/RL stay paused.

### October 6: native Tank path failure and two targeted wins

Direct engine replay queries show all sampled Tanks unable to reach the external
defensive point while Marines can; Tanks can still reach the local rally. The
occupied enemy-base center is an invalid control early and is not used to infer
trapping. Wider physical construction/addon spacing now leaves a two-tile lane,
using actual catalogue footprints and reserving pending/same-batch structures.
Lowered depots/flying structures are excluded. Shared human-goal placement uses
the same calculation; no human imitation or RL runs.

Regression observed failing then passing; full suite452tests/32skips and native
smoke pass. Panel05 independently verifies two Terran wins: Rush683.2seconds,
Macro836.8seconds, zero raw/delayed errors, peakCPU8.9percent. Fixed replay queries
show positive Tank paths to the external defensive point and actual advancement.
Frozen sources/replays/query diagnostics preserved in primitives-native-04/05.

Panel06 all-race six-game development recheck is active, session88883, under
`logs/roadmap/primitives-native-06/panel`. Poll that handle, keep its source fixed,
then run its verifier and archive bound sources. Fresh30-game baseline acceptance
and broader map/strategy coverage remain pending; no learned strength claim.

### October 6: six development wins and fresh scripted baseline

Panel06 finishes six victories and independently verifies originals; peakCPU13.
ProtossRush371raw attacks all target invulnerable Adept shades; TerranMacro has
one raw error. Shade exclusion now passes a formerly failing regression.
No imitation/RL. Full suite454tests/32skips, separate native smoke14.65seconds.

Fresh30-game contract frozen: ten perrace, two maps, five named builds, newseeds
819001–819030. Initial gate21/30overall and7/10each race; all jobs/nonwins reported.
`primitives-hard-baseline-01/panel` is active, session96434. Poll the live handle;
do not modify bound source, then verify and archive originals before diagnosing.

Independent human-source visibility audit finishes7,202states/73,724enemycurrent
observations. Native-coordinate assumption rejects68,861; properfeature mapping
puts67,358on visiblecells and6,366elsewhere,1,429without visibleimmediate neighbor.
This is coarse diagnostic evidence, not native proof. PlayerView/tournament
importer now support correctfeature mapping, regression passes. Existingcorpora
are unchanged; new re-import/intake verification is required before anyfit.

### October 6: verified human visibility re-import

All 14 prior teaching/development games re-import into a new corpus; original
phase/source/reconciliation binding checks remain enabled. Independent verifier
passes all 7,202 label rows, unchanged own units/player/map fields, and 67,358
current enemy observations on visible supplied feature cells. Enemy memory has
no current dynamic fields. Three targets are unavailable, two newly unavailable
Smart targets in teaching games 163/1032. Source grid coarseness and partial
professional reconstruction remain limits; no native fog-proof overclaim.
Peak re-import host CPU9.5 percent. No fitting, RL or reserved reads.

Streaming full raw-command representability inventory is active, session16144.
It explicitly preserves original commands and excludes unsupported labels.
Baseline panel remains active, session96434; ten completed games all win at this
checkpoint, not a terminal gate. Preserve its frozen source until all30finish.
See [human repair evidence](human-visibility-repair.md).

The representability inventory is now terminal: 6,083/6,089 teaching commands and
1,112/1,113 development commands supported, all seven exclusions explicitly
outside observed target candidates. Runtime79.1seconds, no optimizer/model.
Use these counts for a new contract; earlier6,086teaching-count assertions are
not valid for the repaired corpus.
