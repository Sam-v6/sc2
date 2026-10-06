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
