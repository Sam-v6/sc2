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
| A: shared controls | Raw ability, unit group, unit/point target, queue and autocast schema; full visible-map entities, scouting memory, map grids, recent commands; hidden-health checks | Broader physical command-family inventory and learned selection |
| B: replay extraction | Matching-build preflight; fog enabled; observation before command; full anonymous replay reconstructed (559 commands); source-labelled Masters trio fully reconstructed; issued-command repeats audited | Verified professional Terran games, wider corpus, issued/executed event audit |
| C: imitation | Saved CPU-only command-conditioned imitation models; whole-game/held-out-player split; raw unit groups, arguments and delay labels | Wider training corpus and useful live-game competence |
| D: micro | Native DefeatRoaches adapter using shared entities/commands; trace, scores and replay; CPU-only return-driven policy search; held-out combat-score gains; ordinary-game transfer measured | Other scenarios and successful full-game transfer |
| E: full-game RL | CPU raw-ability PPO bridge and native collection/update/paired evaluation; fresh combat-return mechanism gains | Native wins over frozen imitation; learned arguments and durable competence |
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

Spawning Tool's date filter requires M/D/YY: ISO dates silently return unfiltered
results. Search after_played_on=8/13/19 and before_played_on=8/19/19 for the local
build's week; metadata/build and actual Terran identity still need independent
inspection before acceptance.

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

Latest unit verification: 143 tests passed in 10.203 seconds, saved in
`logs/roadmap/unittest-twelfth.log`. Native search/extraction results must be
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
