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
| E: full-game RL | Existing runner/supervisor remain available | New policy RL and improvement over frozen imitation |
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
